from typing import Any, Coroutine, List, Dict, Optional, Sequence, TypedDict, cast
import asyncio

from litellm import Message, acompletion, Choices
from litellm.types.utils import ModelResponse
from pydantic import BaseModel, Field

from supabase import AsyncClient

from lib.db.types import TopLevelCluster

class SampledArtifact(TypedDict):
  artifact_id: str
  title: str
  summary: str
  url: str

class PriorCluster(TypedDict):
  cluster_id: str
  member_count: int
  iteration: int

class ClusterInfo(BaseModel):
    cluster_id: str
    domain_id: str
    member_count: int
    iteration: int
    sample_artifacts: List[SampledArtifact]
    prior_clusters: List[PriorCluster]

class TopicSummary(BaseModel):
  main_theme: str = Field(description="A phrase that describes the main theme of the topic.")
  key_concepts: List[str] = Field(description="A list of phrases that describe key concepts in the topic.")

class ClusterSummarizer:
  def __init__(
    self,
    supabase: AsyncClient,
    llm_model: str = "gpt-4o-mini",
    llm_api_key: str | None = None,
  ):
    self.supabase = supabase
    self.llm_model = llm_model
    self.llm_api_key = llm_api_key
      # self.executor = ThreadPoolExecutor(max_workers=4)


  async def get_cluster_info(self, domain_id: str, cluster_id: str, iteration: int) -> ClusterInfo:
    response = await self.supabase.rpc(
      'get_cluster_summarization_data',
      {
        'target_domain_id': domain_id,
        'target_cluster_id': cluster_id,
        'target_iteration': iteration
      }
    ).execute()

    if not response.data:
      raise ValueError(f"No cluster found for {cluster_id} at iteration {iteration}")

    data = response.data[0]
    return ClusterInfo(
      cluster_id=cluster_id,
      domain_id=domain_id,
      member_count=data['member_count'],
      iteration=iteration,
      sample_artifacts=data['sample_artifacts'],
      prior_clusters=data['prior_clusters']
    )

  async def generate_summary(self, domain_id: str, cluster_id: str, iteration: int, min_cluster_size: int = 10) -> Optional[TopicSummary]:
    """Recursively generates summaries for a cluster and its prerequisites"""

    # Check if summary already exists
    existing = await self.get_existing_summary(domain_id, cluster_id, iteration)
    if existing:
        return existing

    # Get cluster information
    cluster_info = await self.get_cluster_info(domain_id, cluster_id, iteration)

    if cluster_info.member_count < min_cluster_size:
      return None

    if cluster_info.member_count < 100:
      return await self.summarize_cluster_members(cluster_info)

    if cluster_info.iteration > 2:
      # Has prior clusters
      prior_summaries = await self.ensure_prior_summaries(cluster_info, min_cluster_size)
      return await self.summarize_large_hierarchical_cluster(cluster_info, prior_summaries)

    # No prior clusters
    return await self.summarize_cluster_members(cluster_info)


  async def ensure_prior_summaries(self, cluster_info: ClusterInfo, min_cluster_size: int) -> List[TopicSummary]:
    """Recursively ensures all prior cluster summaries exist and returns them"""
    prior_summaries: List[TopicSummary] = []

    # Process prior clusters in parallel
    tasks : List[Coroutine[Any, Any, Optional[TopicSummary]]] = []
    for prior in cluster_info.prior_clusters:
      tasks.append(self.generate_summary(
        cluster_info.domain_id,
        prior['cluster_id'],
        prior['iteration'],
        min_cluster_size=min_cluster_size
      ))

    summaries = await asyncio.gather(*tasks)

    # Combine prior cluster info with their summaries
    for prior, summary in zip(cluster_info.prior_clusters, summaries):
      if summary:  # Only include clusters that got summarized (>10 members)
        prior_summaries.append(summary)

    return prior_summaries

  async def get_existing_summary(self, domain_id: str, cluster_id: str, iteration: int) -> Optional[TopicSummary]:
    response = await self.supabase.table('cluster_summaries')\
      .select('summary')\
      .eq('domain_id', domain_id)\
      .eq('cluster_id', cluster_id)\
      .eq('iteration', iteration)\
      .execute()

    if response.data:
      return TopicSummary.model_validate(response.data[0]['summary'])
    return None

  async def store_summary(
    self,
    domain_id: str,
    cluster_id: str,
    iteration: int,
    member_count: int,
    summary: Dict
  ):
    await self.supabase.table('cluster_summaries').upsert({
      'domain_id': domain_id,
      'cluster_id': cluster_id,
      'iteration': iteration,
      'member_count': member_count,
      'summary': summary
    }).execute()

  async def summarize_cluster_members(self, cluster_info: ClusterInfo) -> Optional[TopicSummary]:
    summary = await self.llm_summarize(cluster_info.sample_artifacts)
    await self.store_summary(
      cluster_info.domain_id,
      cluster_info.cluster_id,
      cluster_info.iteration,
      cluster_info.member_count,
      summary.model_dump() if isinstance(summary, TopicSummary) else {}
    )
    return summary

  async def summarize_large_hierarchical_cluster(
    self,
    cluster_info: ClusterInfo,
    prior_summaries: List[TopicSummary]
  ) -> Optional[TopicSummary]:

    summary = await self.llm_summarize(prior_summaries)
    await self.store_summary(
      cluster_info.domain_id,
      cluster_info.cluster_id,
      cluster_info.iteration,
      cluster_info.member_count,
      summary.model_dump() if isinstance(summary, TopicSummary) else {},
    )
    return summary

  async def llm_summarize(self, members: Sequence[SampledArtifact | TopicSummary]) -> Optional[TopicSummary]:
    """Generate a summary using both member data and lower-level summaries"""

    articles_string = "\n".join([
      f"- Theme: {member.main_theme}. Key concepts: {"\n".join(member.key_concepts)}" if isinstance(member, TopicSummary) else f"- {member['title']}: {member['summary']}"
      for member in members
      ])

    if len(members) == 0:
      return None

    prompt = f"""You are summarizing the main themes and key concepts from a list.
The list can be a list of summaries of articles, or a list of main themes and key concepts of a group of articles.
Your goal is to synthesize the main themes and key concepts that cover that list.

Articles or article summaries:
{articles_string}

Higher-level summary:"""

    response = await acompletion(
      model=self.llm_model,
      api_key=self.llm_api_key,
      messages=[
        {
          "role": "user",
          "content": prompt
        }
      ],
      temperature=0.7,
      response_format=TopicSummary
    )

    assert isinstance(response, ModelResponse)
    assert isinstance(response.choices, list)
    assert isinstance(response.choices[0], Choices)
    assert isinstance(response.choices[0].message, Message)

    return TopicSummary.model_validate_json(str(response.choices[0].message.content))

  async def get_top_level_clusters(self, domain_id: str) -> List[TopLevelCluster]:
    response = await self.supabase.rpc('get_top_level_clusters', {
      'target_domain_id': domain_id
    }).execute()
    return [
      TopLevelCluster(cluster) for cluster in response.data
    ]

