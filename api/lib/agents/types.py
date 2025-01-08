from typing import Any, List, Dict, Optional, TypedDict
from pydantic import BaseModel, Field


class ArtifactSummary(BaseModel):
  url: str
  title: Optional[str] = None
  summary: str

class ArtifactWithLinks(ArtifactSummary):
  artifact_id: Optional[str] = Field(
    default=None,
    deprecated=True,
    description="Deprecated: Use artifact_content_id instead"
  )
  artifact_content_id: Optional[str] = None
  parsed_text: str
  metadata: Optional[Dict[str, Any]] = None
  outbound_links: Optional[List[ArtifactSummary]] = None
  inbound_links: Optional[List[ArtifactSummary]] = None

class ResearchTopic(BaseModel):
  research_question: str
  related_key_concepts: str
  related_user_requirements: str

class KnowledgeTopic(BaseModel):
  topic: str
  key_concepts: List[str]

class RunbookSectionOutline(BaseModel):
  section_title: str = Field(description="The title of the section")
  outline: str = Field(description="A high-level outline of the section")
  related_artifacts: List[str] = Field(description="A list of artifact content IDs that are related to this section")

class RunbookSection(RunbookSectionOutline):
  retrieved_artifacts: Optional[List[ArtifactWithLinks]] = Field(description="A list of artifacts that have been retrieved for this section", default=[])
  content: Optional[str] = Field(default=None, description="The content of the section")

class ContextVariables(TypedDict, total=False):
  domain_id: Optional[str]
  user_requirements: Optional[List[str]]
  research_topics: Optional[List[ResearchTopic]]
  current_research_topic: Optional[int]
  current_expansion_topic: Optional[int]
  saved_artifacts: Optional[Dict[str, List[ArtifactWithLinks]]]
  runbook_sections: Optional[List[RunbookSection]]
  current_runbook_section: Optional[int]
  debug: Optional[bool]

class ArtifactSearchResult(TypedDict):
  artifact_content_id: str
  url: str
  title: str
  summary: str
  anchor_id: Optional[str]
  similarity: float
  main_sections: List[str]

