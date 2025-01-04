from typing import List
from lib.db.types import ArtifactDomain
from lib.inngest_context import with_inngest_step, get_inngest_step_from_context
from lib.logger import with_logger, get_logger_from_context
from lib.inngest import inngest_client
from lib.supabase import create_async_supabase_admin_client
from lib.cluster.summarizer import ClusterSummarizer
from api.inngest.events import ClusterArtifactsEvent, ClusterArtifactsEventData
import inngest

@inngest_client.create_function(
  fn_id="cluster_artifacts",
  trigger=inngest.TriggerEvent(event=ClusterArtifactsEvent.name),
  concurrency=[
    inngest.Concurrency(limit=1),
  ],
)
async def cluster_artifacts(ctx: inngest.Context, step: inngest.Step):
  event = ClusterArtifactsEvent.from_event(ctx.event)
  with with_logger(ctx.logger), with_inngest_step(step):
    await step.run(
      "detect_article_clusters",
      lambda: _run_detect_article_clusters(event.data.domain_id),
    )
    return await _get_cluster_summaries(event.data.domain_id)

async def _run_detect_article_clusters(domain_id: str):
  logger = get_logger_from_context()
  logger.info(f"Running detect article clusters for domain {domain_id}")

  supabase = await create_async_supabase_admin_client()
  await supabase.rpc("detect_article_clusters", {"target_domain_id": domain_id}).execute()

async def _generate_summary_for_cluster(domain_id: str, cluster_id: str, iteration: int, min_cluster_size: int):
  supabase = await create_async_supabase_admin_client()

  summarizer = ClusterSummarizer(supabase)
  topics_summary = await summarizer.generate_summary(
    domain_id=domain_id,
    cluster_id=cluster_id,
    iteration=iteration,
    min_cluster_size=min_cluster_size
  )
  if topics_summary is None:
    return None

  return topics_summary.model_dump()

async def _get_cluster_summaries(domain_id: str):
  supabase = await create_async_supabase_admin_client()
  step = get_inngest_step_from_context()

  domain_response = await (
    supabase
    .from_("artifact_domains")
    .select("*")
    .eq("id", domain_id)
    .maybe_single()
    .execute()
  )
  if domain_response is None or domain_response.data is None:
    raise inngest.NonRetriableError(f"Domain {domain_id} not found")

  domain = ArtifactDomain(**domain_response.data)
  min_cluster_size = domain["crawl_config"].get("min_cluster_size", 10)

  summarizer = ClusterSummarizer(supabase)
  top_level_clusters = await step.run(
    "get_top_level_clusters",
    lambda: summarizer.get_top_level_clusters(domain_id)
  )

  cluster_summaries = []
  for cluster in top_level_clusters:
    summary = await step.run(
      f"generate_summary_cluster_{cluster['cluster_id']}",
      lambda: _generate_summary_for_cluster(
        domain_id,
        cluster['cluster_id'],
        cluster['iteration'],
        min_cluster_size
      )
    )
    if summary:
      cluster_summaries.append({
        'cluster_id': cluster['cluster_id'],
        'summary': summary
      })

  return cluster_summaries

