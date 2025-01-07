
from typing import Literal, Optional, Sequence, TypedDict

CrawlStatus = Literal["discovered", "scraped", "scrape_failed", "scraping"]

ThreadType = Literal["runbook_generator"]

class ClusterSummarySummary(TypedDict):
  main_theme: str
  key_concepts: Sequence[str]

class Artifact(TypedDict):
  domain_id: str
  artifact_id: str
  crawl_depth: int
  crawl_status: CrawlStatus
  created_at: str
  metadata: Optional[dict]
  parsed_text: Optional[str]
  summary: Optional[str]
  title: Optional[str]
  url: str
  content_sha256: Optional[str]
  crawled_as_artifact_id: Optional[str]


class ArtifactContentInsert(TypedDict):
  artifact_id: str
  metadata: dict
  parsed_text: str
  summary: str
  summary_embedding: str
  title: str
  anchor_id: Optional[str]

class ArtifactContent(ArtifactContentInsert):
  artifact_content_id: str
  created_at: str

class ArtifactLinkInsert(TypedDict):
  anchor_text: Optional[str]
  source_artifact_content_id: str
  target_url: str

class ArtifactLink(ArtifactLinkInsert):
  created_at: str
  id: str

class DomainConfig(TypedDict, total=False):
  max_crawl_depth: int
  allowed_url_patterns: list[str]
  min_cluster_size: int
  crawler_disabled: Optional[bool]
  starting_agent: Optional[str]

class ArtifactDomain(TypedDict):
  id: str
  name: str
  config: DomainConfig
  created_at: str

class ArtifactCluster(TypedDict):
  id: str
  artifact_id: str
  cluster_id: str
  is_intermediate: bool
  iteration: int
  created_at: str

class ClusterSummary(TypedDict):
  id: str
  created_at: str
  domain_id: str
  cluster_id: str
  iteration: int
  member_count: int
  summary: ClusterSummarySummary

class TopLevelCluster(TypedDict):
  cluster_id: str
  member_count: int
  iteration: int
  summary: Optional[ClusterSummarySummary]

class Profile(TypedDict):
  user_id: str
  created_at: str
  name: str
  email: str

class Thread(TypedDict):
  thread_id: str
  created_at: str
  user_id: str
  last_known_good_thread_state_id: Optional[str]
  thread_type: ThreadType
  title: Optional[str]

class ThreadState(TypedDict):
  thread_state_id: str
  created_at: str
  thread_id: str
  messages: list[str]
  context_variables: dict
  agent_name: Optional[str]
