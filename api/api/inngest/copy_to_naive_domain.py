from typing import List
from lib.db.types import Artifact, ArtifactContentInsert
from lib.inngest_context import with_inngest_step, get_inngest_step_from_context
from lib.logger import with_logger, get_logger_from_context
from lib.inngest import inngest_client
from lib.supabase import create_async_supabase_admin_client
from api.inngest.events import CopyToNaiveDomainEvent, CopyToNaiveDomainEventData
import inngest

from lib.text_splitter import HierarchicalMarkdownSplitter
from lib.config import Settings

BATCH_SIZE = 50
settings = Settings()

@inngest_client.create_function(
  fn_id="copy_to_naive_domain",
  trigger=inngest.TriggerEvent(event=CopyToNaiveDomainEvent.name),
  concurrency=[
    inngest.Concurrency(limit=1),
  ],
)
async def copy_to_naive_domain(ctx: inngest.Context, step: inngest.Step):
  event = CopyToNaiveDomainEvent.from_event(ctx.event)
  with with_logger(ctx.logger), with_inngest_step(step):
    return await _copy_to_naive_domain(event.data.source_domain_id, event.data.target_domain_id)


async def _copy_to_naive_domain(source_domain_id: str, target_domain_id: str) -> dict:
  step = get_inngest_step_from_context()
  logger = get_logger_from_context()
  copy_response : int = await step.run("copy_domain_artifacts", lambda: _copy_domain_artifacts(source_domain_id, target_domain_id))
  logger.info(f"Copied {copy_response} artifacts from {source_domain_id} to {target_domain_id}")
  artifacts_processed = 0
  page = 0
  while True:
    artifact_content_response = await step.run(
      f"copy_artifacts_page_{page}",
      lambda: _ingest_artifacts(target_domain_id, page),
    )
    artifacts_processed += artifact_content_response["artifacts_processed"]
    if artifact_content_response["artifacts_processed"] < BATCH_SIZE:
      break
    page += 1
  return {
    "artifacts_processed": artifacts_processed,
  }

async def _copy_domain_artifacts(source_domain_id: str, target_domain_id: str) -> int:
  supabase = await create_async_supabase_admin_client()
  artifact_response = await supabase.rpc(
    "copy_domain_artifacts",
    {
      "source_domain_id": source_domain_id,
      "target_domain_id": target_domain_id,
    },
  ).execute()
  return int(artifact_response.data)

async def _get_artifacts(domain_id: str, page: int) -> List[Artifact]:
  supabase = await create_async_supabase_admin_client()
  artifact_response = await (
    supabase
    .table("artifacts")
    .select("*")
    .eq("domain_id", domain_id)
    .eq("crawl_status", "scraped")
    .not_.is_("parsed_text",  None)
    .range(page * BATCH_SIZE, (page + 1) * BATCH_SIZE - 1)
    .execute()
  )
  return [Artifact(**artifact_data) for artifact_data in artifact_response.data]

async def _upsert_artifact_contents(payload: List[ArtifactContentInsert]) -> dict:
  supabase = await create_async_supabase_admin_client()
  artifact_content_response = await supabase.table("artifact_contents").upsert(payload, on_conflict="artifact_id,anchor_id").execute()
  return {
    "artifact_contents_processed": len(artifact_content_response.data),
  }

async def _ingest_artifacts(domain_id: str, page: int) -> dict:
  artifacts = await _get_artifacts(domain_id, page)
  splitter = HierarchicalMarkdownSplitter(chunk_size=512)
  contents_processed = 0
  for artifact in artifacts:
    if artifact["parsed_text"] is None:
      continue
    chunks = list(splitter.split(artifact["parsed_text"]))
    embeddings = await _embed_strings(chunks)
    upsert_payload = [
      ArtifactContentInsert(
        artifact_id=artifact["artifact_id"],
        metadata={},
        parsed_text=chunk,
        summary=chunk,
        summary_embedding=str(embedding),
        title=chunk.splitlines()[0].strip(),
        anchor_id=str(i),
      )
      for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]
    artifact_content_response = await _upsert_artifact_contents(upsert_payload)
    contents_processed += len(upsert_payload)
  return {
    "artifacts_processed": len(artifacts),
    "contents_processed": contents_processed,
  }

async def _embed_strings(texts: List[str]) -> List[List[float]]:
  from lib.nomic import NomicEmbeddings

  nomic_api_key = settings.nomic_api_key
  assert nomic_api_key is not None, "NOMIC_API_KEY is not set"
  embedding_client = NomicEmbeddings(api_key=nomic_api_key)
  embeddings = await embedding_client.embed_texts(
    texts=texts,
    model='nomic-embed-text-v1.5',
    task_type="search_document",
  )

  return embeddings.embeddings
