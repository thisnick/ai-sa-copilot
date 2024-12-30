
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
  metadata: dict
  parsed_text: str
  summary: str
  title: str
  url: str

class ArtifactContent(TypedDict):
  artifact_content_id: str
  artifact_id: str
  created_at: str
  metadata: dict
  parsed_text: str
  summary: str
  title: str
  anchor_id: str

class ArtifactLink(TypedDict):
  anchor_text: str
  created_at: str
  id: str
  source_artifact_content_id: str
  target_url: str

class CrawlConfig(TypedDict):
  crawl_depth: int
  allowed_url_patterns: list[str]

class ArtifactDomain(TypedDict):
  id: str
  name: str
  crawl_config: CrawlConfig
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
