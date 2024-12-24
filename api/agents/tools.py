import asyncio
import json
import os
from typing import Dict, List, Literal, Optional, TypedDict

from litellm import cast
from nomic.embed import text as embed_text
from supabase import AsyncClient

from api.db.types import TopLevelCluster

from .types import (
  ArtifactWithLinks,
  ArtifactSearchResult,
  KnowledgeTopic,
  ResearchTopic,
  RunbookSection
)
from .contexts import get_supabase_client_from_context


async def async_get_knowledge_topics(domain_id: str) -> List[KnowledgeTopic]:
  supabase = get_supabase_client_from_context()
  top_level_clusters_response = await supabase.rpc("get_top_level_clusters", {"target_domain_id": domain_id}).execute()
  top_level_clusters = cast(List[TopLevelCluster], top_level_clusters_response.data)

  results = [
    KnowledgeTopic(
      topic=cluster["summary"]["main_theme"],
      key_concepts=list(cluster["summary"]["key_concepts"])
    )
    for cluster in top_level_clusters
    if cluster["summary"] is not None
  ]
  return results

def format_knowledge_topics(topics: List[KnowledgeTopic]) -> str:
  return "\n".join(
    [
      f"{i+1}. {topic.topic}: ({', '.join(topic.key_concepts)})"
      for i, topic in enumerate(topics)
    ]
  )


def format_research_topic(topic: ResearchTopic) -> str:
  return f"- Topic: {topic.research_question}\nRelated Key Concepts: {', '.join(topic.related_key_concepts)}\nRelated User Requirements: {topic.related_user_requirements}"


def format_related_artifacts(artifact: ArtifactWithLinks) -> str:
  outbound_links = (
    "\n".join(
      [
        f"- Title: {link.title}\n  Artifact ID: {link.artifact_id}\n  Summary: {link.summary}"
        for link in artifact.outbound_links or []
      ]
    )
    or "None"
  )
  inbound_links = (
    "\n".join([
      f"- Title: {link.title}\n  Artifact ID: {link.artifact_id}\n  Summary: {link.summary}"
      for link in artifact.inbound_links or []
    ])
    or "None"
  )
  return f"Outbound Links:\n{outbound_links}\n\nInbound Links:\n{inbound_links}"

def format_artifact(artifact: ArtifactWithLinks, include_links: bool = False, treat_metadata_as_content: bool = False) -> str:
  if treat_metadata_as_content:
    if artifact.metadata:
      content = f"# Content (metadata)\n\n{json.dumps(artifact.metadata)}"
    else:
      content = f"# Content (summary)\n\n{artifact.summary}"
  else:
    content = f"# Content (full text)\n\n{artifact.parsed_text}"

  return f"""# Title: {artifact.title}

 - Artifact ID: {artifact.artifact_id}
 - URL: {artifact.url}

{content}
""" + (
    f"\n\nRelated Artifacts:\n{format_related_artifacts(artifact)}" if include_links else ""
  )

def format_artifacts(artifacts: List[ArtifactWithLinks], include_links: bool = False, treat_metadata_as_content: bool = False) -> str:
  return "\n\n---\n\n".join([
    format_artifact(artifact, include_links, treat_metadata_as_content)
    for artifact in artifacts
  ])

def format_topic_artifacts(artifacts: Dict[str, List[ArtifactWithLinks]], include_links: bool = False, treat_metadata_as_content: bool = False) -> str:
  return "\n\n---\n\n".join([
    f"Research Topic: {topic}:\n\nRetrieved Artifacts:\n{format_artifacts(artifacts, include_links, treat_metadata_as_content)}"
    for topic, artifacts in artifacts.items()
  ])

def format_written_sections(sections: List[RunbookSection], up_to: Optional[int] = None) -> str:
  return "\n\n---\n\n".join([
    f"Section {i + 1}\n\n{section.content}"
    for i, section in enumerate(sections[:up_to])
    if section.content
  ]) or "None"

def format_runbook_section_outline(section: RunbookSection) -> str:
  return f"## Section Title: {section.section_title}\n\n## Outline:\n{section.outline}"

async def async_get_artifacts(
  artifact_ids: List[str]
) -> List[ArtifactWithLinks]:
  supabase = get_supabase_client_from_context()
  artifacts_response = await (
    supabase
    .rpc("get_artifacts_with_links", { "artifact_ids": artifact_ids })
    .execute()
  )
  return [ArtifactWithLinks.model_validate(artifact) for artifact in artifacts_response.data]

async def async_query_for_artifacts(queries: List[str]) -> Dict[Literal["artifacts"], List[ArtifactSearchResult]]:
  embeddings = embed_text(
    texts=queries,
    model='nomic-embed-text-v1.5',
    task_type="search_query",
  )

  supabase = get_supabase_client_from_context()

  responses = await asyncio.gather(*[
    supabase.rpc("match_artifacts", {
      "query_embedding": embedding,
      "match_count": 4,
      "filter": {}
    }).execute()
    for embedding in embeddings['embeddings']
  ])

  # Flatten the responses array and extract data
  flattened_responses : List[ArtifactSearchResult] = [
    {
      "artifact_id": item["artifact_id"],
      "url": item["url"],
      "title": item["title"],
      "summary": item["summary"],
      "similarity": item["similarity"],
      "main_sections": item.get("metadata", {}).get("main_sections", [])
    }
    for response in responses
    for item in response.data
  ]

  return {
    "artifacts": flattened_responses,
  }
