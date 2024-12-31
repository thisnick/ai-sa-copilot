from copy import deepcopy
import os
import re
from typing import Callable, Coroutine, List, Protocol, TypeAlias, cast, Optional, Any
from urllib.parse import urljoin, urlparse

import inngest
from markdown_it import MarkdownIt
from supabase import AsyncClient

from lib.db.types import (
  Artifact,
  ArtifactContent,
  ArtifactDomain,
  ArtifactLink,
  CrawlConfig,
)
from lib.inngest import inngest_client
from lib.metadata import ArtifactMetadata, Link
from lib.scraper import (
  WebScraper,
  DataExtractor,
  DataExtractorConfig,
  ScrapingConfig,
  WebScraperResult,
)
from lib.scraper.types import PageDataExtractionResult, ScrapedContent
from lib.supabase import create_async_supabase_admin_client

from .events import CrawlRequestedEvent, CrawlRequestedEventData
from .tools import get_sha256_hash

MetadataExtractionResponse : TypeAlias = PageDataExtractionResult[ArtifactMetadata, ArtifactMetadata]
class ScheduleCrawlFunction(Protocol):
  async def __call__(self, step_id: str, crawl_request: CrawlRequestedEventData | List[CrawlRequestedEventData]) -> List[str]:
    pass

MAX_CRAWL_DEPTH = 5

@inngest_client.create_function(
  fn_id="crawl",
  trigger=inngest.TriggerEvent(event=CrawlRequestedEvent.name),
  concurrency=[
    inngest.Concurrency(limit=20),
    inngest.Concurrency(scope="account", limit=1, key="event.data.url")
  ],
)
async def crawl_url(ctx: inngest.Context, step: inngest.Step):
  event = CrawlRequestedEvent.from_event(ctx.event)

  def schedule_crawl(step_id: str, crawl_request: CrawlRequestedEventData | List[CrawlRequestedEventData]):
    # For single request
    if isinstance(crawl_request, CrawlRequestedEventData):
        events = [CrawlRequestedEvent(data=crawl_request).to_event()]
    # For list of requests
    else:
        events = [
            CrawlRequestedEvent(data=request).to_event()
            for request in crawl_request
        ]
    return step.send_event(step_id, events)

  return await _crawl_url(
    event.data,
    schedule_crawl
  )

async def _embed_strings(texts: List[str]) -> List[List[float]]:
  from lib.nomic import NomicEmbeddings

  nomic_api_key = os.getenv("NOMIC_API_KEY")
  assert nomic_api_key is not None, "NOMIC_API_KEY is not set"
  embedding_client = NomicEmbeddings(api_key=nomic_api_key)
  embeddings = await embedding_client.embed_texts(
    texts=texts,
    model='nomic-embed-text-v1.5',
    task_type="search_document",
  )

  return embeddings.embeddings

async def _crawl_url(
  crawl_request: CrawlRequestedEventData,
  schedule_crawl: ScheduleCrawlFunction = None
):
  # Validate and get domain config
  artifact_domain = await _validate_and_get_domain(crawl_request)

  # Check crawl depth limits
  scraping_config, max_crawl_depth = _get_crawl_configs(artifact_domain)
  if crawl_request.crawl_depth > max_crawl_depth:
    print(f"Crawl depth {crawl_request.crawl_depth} is greater than max crawl depth {max_crawl_depth}, skipping")
    return

  # Check for existing artifact
  existing_artifact = await _get_existing_artifact(crawl_request.url)
  if existing_artifact:
    return await _process_existing_artifact(
      existing_artifact,
      crawl_request,
      schedule_crawl
    )

  # Create new artifact and scrape
  upserted_artifact = await _create_new_artifact(crawl_request)
  scrape_response = await _perform_scraping(crawl_request.url, scraping_config)

  # Check for duplicate content
  duplicate_artifact = await _check_duplicate_content(
    upserted_artifact,
    scrape_response.page_content
  )

  if duplicate_artifact:
    return await _process_existing_artifact(
      duplicate_artifact,
      crawl_request,
      schedule_crawl
    )
  extraction_response = await _extract_data(scrape_response)

  # Save data related to the artifact
  updated_article = await _save_artifact_data(
    upserted_artifact,
    scrape_response,
    extraction_response
  )

  # Process sections and embeddings
  updated_artifact_contents = await _process_artifact_sections(
    upserted_artifact,
    scrape_response,
    extraction_response
  )

  # Process links
  crawl_links_response = await _crawl_links(
    updated_artifact_contents,
    scrape_response,
    crawl_request,
    artifact_domain["crawl_config"],
    schedule_crawl
  )

  return {
    "artifact": updated_article,
    **crawl_links_response
  }

async def _validate_and_get_domain(crawl_request: CrawlRequestedEventData) -> ArtifactDomain:
  assert crawl_request.crawl_depth is not None, "Crawl depth is required"
  assert crawl_request.url is not None, "URL is required"
  assert crawl_request.domain_id is not None, "Domain ID is required"

  admin_supabase = await create_async_supabase_admin_client()
  crawl_domain_response = await (
    admin_supabase
    .table("artifact_domains")
    .select("*")
    .eq("domain_id", crawl_request.domain_id)
    .maybe_single()
    .execute()
  )

  if not crawl_domain_response:
    print(f"Domain {crawl_request.domain_id} not found")
    raise inngest.NoDataError(f"Domain {crawl_request.domain_id} not found")

  artifact_domain = cast(ArtifactDomain, crawl_domain_response.data)
  if not artifact_domain.get("crawl_config"):
    print(f"Domain {crawl_request.domain_id} does not have a crawl config")
    raise inngest.NoDataError(f"Domain {crawl_request.domain_id} does not have a crawl config")

  return artifact_domain

def _get_crawl_configs(artifact_domain: ArtifactDomain) -> tuple[ScrapingConfig, int]:
  scraping_config = ScrapingConfig()
  scraping_config = scraping_config.model_copy(
    update=artifact_domain.get("crawl_config"),
    ignore_extra=True
  )
  max_crawl_depth = artifact_domain["crawl_config"].get("crawl_depth", MAX_CRAWL_DEPTH)
  return scraping_config, max_crawl_depth

async def _extract_data(scrape_response: WebScraperResult) -> MetadataExtractionResponse:
  data_extractor = DataExtractor(
    model="openai/gpt-4o-mini",
    model_api_key=os.getenv("OPENAI_API_KEY"),
  )

  return await data_extractor.async_extract_from_scraped_data(
    scrape_response,
    DataExtractorConfig(
      section_extraction_schema=ArtifactMetadata,
      section_extraction_prompt="Extract the title, summary, and main_sections.",
      page_extraction_schema=ArtifactMetadata,
      page_extraction_prompt="Extract the title, summary, and main_sections.",
    )
  )

async def _save_artifact_data(
  artifact: Artifact,
  scrape_response: WebScraperResult,
  extraction_response: MetadataExtractionResponse
) -> Artifact:
  admin_supabase = await create_async_supabase_admin_client()
  updated_article_response = await admin_supabase\
    .table("artifacts")\
    .update({
      "crawl_status": "scraped",
      "metadata": extraction_response.whole_page_data.model_dump(mode='json'),
      "parsed_text": scrape_response.page_content,
      "summary": extraction_response.whole_page_summary,
      "title": scrape_response.page_title,
    })\
    .eq("artifact_id", artifact["artifact_id"])\
    .execute()

  return Artifact(updated_article_response.data[0])

async def _process_existing_artifact(
  existing_artifact: Artifact,
  base_crawl_event: CrawlRequestedEventData,
  schedule_crawl: ScheduleCrawlFunction = None
) -> dict:
  admin_supabase = await create_async_supabase_admin_client()
  assert existing_artifact["crawl_status"] == "scraped", "Artifact must be scraped before processing"

  if existing_artifact["crawl_depth"] <= base_crawl_event.crawl_depth:
    print(f"Artifact {existing_artifact['url']} has already been processed at depth {existing_artifact['crawl_depth']}")
    return {"data": existing_artifact}

  print(f"Processing outbound links for {existing_artifact['url']} at depth {existing_artifact['crawl_depth']}")

  await admin_supabase\
    .table("artifacts")\
    .update({
      "crawl_depth": base_crawl_event
    })\
    .eq("artifact_id", existing_artifact["artifact_id"])\
    .execute()

  outbound_links = await admin_supabase\
    .table("artifact_links")\
    .select("*")\
    .eq("source_artifact_id", existing_artifact["artifact_id"])\
    .limit(100)\
    .execute()

  outbound_crawl_requests = [
    CrawlRequestedEventData(
      url=link["target_url"],
      crawl_depth=base_crawl_event.crawl_depth + 1,
      allowed_url_patterns=base_crawl_event.allowed_url_patterns
    ) for link in outbound_links.data if base_crawl_event.crawl_depth + 1 <= MAX_CRAWL_DEPTH
  ]
  event_ids = await schedule_crawl(
    step_id=f"crawl-outbound-links",
    crawl_request=outbound_crawl_requests
  )
  return {"event_ids": event_ids}

async def _crawl_links(
  artifact_contents: List[ArtifactContent],
  scraper_result: WebScraperResult,
  base_crawl_event: CrawlRequestedEventData,
  crawl_config: CrawlConfig,
  schedule_crawl: ScheduleCrawlFunction = None
) -> dict:
  """Process and store links for an artifact."""
  # Match sections and delete existing links
  matched_sections = _match_artifact_sections(artifact_contents, scraper_result)
  await _delete_existing_links(artifact_contents)

  # Create and insert new links
  insert_links_payload = _create_insert_links_payload(matched_sections, crawl_config)
  insert_response = await _insert_new_links(insert_links_payload)

  # Handle crawling of new links
  links_to_crawl = await _filter_existing_links(
    insert_links_payload,
    base_crawl_event
  )

  event_ids = await _schedule_link_crawls(
    links_to_crawl,
    base_crawl_event,
    schedule_crawl
  )

  return {
    "crawl_event_ids": event_ids,
    "insert_ids": insert_response.data
  }

def _match_artifact_sections(
  artifact_contents: List[ArtifactContent],
  scraper_result: WebScraperResult
) -> List[tuple[ArtifactContent, ScrapedContent]]:
  """Match artifact contents with scraped sections."""
  used_artifact_contents = set()
  return [
    (artifact_content, scraped_section)
    for artifact_content in artifact_contents
    for scraped_section in scraper_result.scraped_sections
    if (artifact_content["anchor_id"], artifact_content["content"]) == (scraped_section.id, scraped_section.content)
    and artifact_content["artifact_content_id"] not in used_artifact_contents
    and not used_artifact_contents.add(artifact_content["artifact_content_id"])
  ]

async def _delete_existing_links(
  artifact_contents: List[ArtifactContent]
) -> None:
  """Delete existing links for the given artifact contents."""
  admin_supabase = await create_async_supabase_admin_client()
  await admin_supabase.table("artifact_links")\
    .delete()\
    .in_(
      "source_artifact_content_id",
      [content["artifact_content_id"] for content in artifact_contents]
    )\
    .execute()

def _create_insert_links_payload(
  matched_sections: List[tuple[ArtifactContent, ScrapedContent]],
  crawl_config: CrawlConfig
) -> List[ArtifactLink]:
  """Create payload for new links to be inserted."""
  return [
    ArtifactLink(
      anchor_text=link.anchor_text,
      source_artifact_content_id=artifact_content["artifact_content_id"],
      target_url=link.url
    )
    for (artifact_content, scraped_section) in matched_sections
    for link in scraped_section.scraped_links[:50]
    if any(re.match(pattern, link.url) for pattern in crawl_config.allowed_url_patterns)
  ]

async def _insert_new_links(
  links_payload: List[ArtifactLink]
) -> Any:
  """Insert new links into the database."""
  admin_supabase = await create_async_supabase_admin_client()
  return await admin_supabase.table("artifact_links")\
    .insert(links_payload)\
    .execute()

async def _filter_existing_links(
  links: List[ArtifactLink],
  base_crawl_event: CrawlRequestedEventData
) -> List[ArtifactLink]:
  """Filter out links that already exist with lower/equal crawl depth."""
  admin_supabase = await create_async_supabase_admin_client()
  existing_response = await admin_supabase.table("artifacts")\
    .select("*")\
    .in_("url", [link["target_url"] for link in links])\
    .limit(100)\
    .execute()

  if not existing_response.data:
    return links

  existing_artifacts = [cast(Artifact, artifact) for artifact in existing_response.data]
  return [
    link for link in links
    if not any(
      artifact["url"] == link["target_url"] and
      artifact["crawl_depth"] <= base_crawl_event.crawl_depth + 1
      for artifact in existing_artifacts
    )
  ]

async def _schedule_link_crawls(
  links: List[ArtifactLink],
  base_crawl_event: CrawlRequestedEventData,
  schedule_crawl: ScheduleCrawlFunction
) -> List[str]:
  """Schedule crawls for new links if within depth limit."""
  if not links or base_crawl_event.crawl_depth + 1 > MAX_CRAWL_DEPTH:
    return []

  event_payload = [
    CrawlRequestedEventData(
      url=link["target_url"],
      crawl_depth=base_crawl_event.crawl_depth + 1,
      domain_id=base_crawl_event.domain_id,
    ) for link in links
  ]

  return await schedule_crawl(
    step_id="crawl-outbound-links",
    crawl_request=event_payload
  )

async def _get_existing_artifact(
  url: str
) -> Optional[Artifact]:
  admin_supabase = await create_async_supabase_admin_client()
  existing_artifact_response = await (
    admin_supabase
    .table("artifacts")
    .select("*")
    .eq("url", url)
    .limit(1)
    .maybe_single()
    .execute()
  )

  if existing_artifact_response and \
    existing_artifact_response.data and \
    Artifact(existing_artifact_response.data)["crawl_status"] == "scraped":
    return Artifact(existing_artifact_response.data)

  return None

async def _create_new_artifact(
  crawl_request: CrawlRequestedEventData
) -> Artifact:
  admin_supabase = await create_async_supabase_admin_client()
  upsert_response = await (
    admin_supabase
    .table("artifacts")
    .upsert(
      {
        "crawl_status": "scraping",
        "crawl_depth": crawl_request.crawl_depth,
        "url": crawl_request.url,
        "domain_id": crawl_request.domain_id
      },
      on_conflict="url"
    )
    .execute()
  )
  return Artifact(upsert_response.data[0])

async def _perform_scraping(
  url: str,
  scraping_config: ScrapingConfig
) -> WebScraperResult:
  scraper = WebScraper()
  return await scraper.async_scrape(url, scraping_config)

async def _check_duplicate_content(
  artifact: Artifact,
  content: str
) -> Optional[Artifact]:
  admin_supabase = await create_async_supabase_admin_client()
  content_hash = get_sha256_hash(content)

  existing_hash_doc_response = await (
    admin_supabase
    .table("artifacts")
    .select("*")
    .eq("content_sha256", content_hash)
    .is_("crawled_as_artifact_id", None)
    .limit(1)
    .maybe_single()
    .execute()
  )

  if existing_hash_doc_response and existing_hash_doc_response.data:
    print(f"Document with content hash {content_hash} already exists")
    await (
      admin_supabase
      .table("artifacts")
      .update({
        "crawled_as_artifact_id": existing_hash_doc_response.data[0]["artifact_id"],
        "crawl_status": "scraped",
        "metadata": existing_hash_doc_response.data[0]["metadata"],
        "parsed_text": existing_hash_doc_response.data[0]["parsed_text"],
        "summary": existing_hash_doc_response.data[0]["summary"],
        "title": existing_hash_doc_response.data[0]["title"],
        "url": artifact["url"],
        "content_sha256": content_hash,
      })
      .eq("artifact_id", artifact["artifact_id"])
      .execute()
    )
    return Artifact(existing_hash_doc_response.data[0])

  return None

async def _process_artifact_sections(
  artifact: Artifact,
  scrape_response: WebScraperResult,
  extraction_response: MetadataExtractionResponse
) -> List[ArtifactContent]:
  admin_supabase = await create_async_supabase_admin_client()
  summary_embeddings = await _embed_strings([
    f"{section.title}\n\n{section.summary}"
    for section in scrape_response.scraped_sections
  ])

  upsert_artifact_content_payload: List[ArtifactContent] = [
    ArtifactContent(
      artifact_id=artifact["artifact_id"],
      title=scraped_section.title,
      parsed_text=scraped_section.content,
      anchor_id=scraped_section.id,
      summary=extraction_response.sections_data[index].section_summary,
      metadata=extraction_response.sections_data[index].section_data.model_dump(mode='json'),
      summary_embedding=str(summary_embeddings[index]),
    ) for (index, scraped_section) in enumerate(scrape_response.scraped_sections)
  ]

  upsert_response = await (
    admin_supabase
    .table("artifacts_contents")
    .upsert(upsert_artifact_content_payload, on_conflict="artifact_id, anchor_id")
    .execute()
  )

  return upsert_response.data



