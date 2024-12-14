from typing import List, Callable, Coroutine
import inngest
from supabase import AsyncClient
from urllib.parse import urljoin, urlparse
from markdown_it import MarkdownIt
import re

from ...lib.scraper import WebScraper
from .events import CrawlRequestedEvent, CrawlRequestedEventData
from ...lib.inngest import inngest_client
from ...lib.supabase import create_async_supabase_client
from ...db.types import Artifact, ArtifactLink
from ...lib.metadata import ArtifactMetadata, Link

from typing import List, Callable, Coroutine, Protocol
from .uncrawled_urls import uncrawled_urls

class ScheduleCrawlFunction(Protocol):
  async def __call__(self, step_id: str, crawl_request: CrawlRequestedEventData | List[CrawlRequestedEventData]) -> List[str]:
    pass

MAX_CRAWL_DEPTH = 5
DATABRICK_ALLOWED_URL_PATTERNS = [
  "^https:\\/\\/docs\\.databricks\\.com\\/en\\/.*$"
]

@inngest_client.create_function(
  fn_id="continue-crawl",
  trigger=inngest.TriggerEvent(event="one-off/continue-crawl"),
)
async def continue_crawl(ctx: inngest.Context, step: inngest.Step):
  supabase = await create_async_supabase_client()

  event_payload = [
    CrawlRequestedEvent(data=CrawlRequestedEventData(
      url=url["url"],
      crawl_depth=url["crawl_depth"],
      allowed_url_patterns=DATABRICK_ALLOWED_URL_PATTERNS
    )).to_event() for url in uncrawled_urls
  ]
  event_ids = await step.send_event(
    "send-crawl-events",
    event_payload
  )
  return {"event_ids": event_ids}

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

  admin_supabase = await create_async_supabase_client()
  return await _crawl_url(
    event.data,
    schedule_crawl
  )

async def _embed_string(prompt: str):
  from ollama import AsyncClient as OllamaClient
  # TODO: this needs to be changed in PROD
  ollama = OllamaClient()
  return await ollama.embeddings(
    model='nomic-embed-text',
    prompt=prompt
  )

async def _crawl_url(
  crawl_request: CrawlRequestedEventData,
  schedule_crawl: ScheduleCrawlFunction = None
):
  assert crawl_request.crawl_depth is not None, "Crawl depth is required"
  assert crawl_request.url is not None, "URL is required"
  assert crawl_request.allowed_url_patterns and len(crawl_request.allowed_url_patterns) > 0, "Allowed URL patterns must be non-empty"

  if crawl_request.crawl_depth > MAX_CRAWL_DEPTH:
    print(f"Crawl depth {crawl_request.crawl_depth} is greater than max crawl depth {MAX_CRAWL_DEPTH}, skipping")
    return

  admin_supabase = await create_async_supabase_client()

  existing_artifact_response = await admin_supabase\
    .table("artifacts")\
    .select("*")\
    .eq("url", crawl_request.url)\
    .limit(1)\
    .maybe_single()\
    .execute()

  if existing_artifact_response and \
    existing_artifact_response.data and \
    Artifact(existing_artifact_response.data)["crawl_status"] == "scraped":

    return await _process_existing_artifact(
      admin_supabase,
      Artifact(existing_artifact_response.data),
      crawl_request,
      schedule_crawl
    )

  upsert_response = await admin_supabase\
    .table("artifacts")\
    .upsert(
      {
        "crawl_status": "scraping",
        "crawl_depth": crawl_request.crawl_depth,
        "url": crawl_request.url
      },
      on_conflict="url"
    )\
    .execute()

  upserted_artifact = Artifact(upsert_response.data[0])

  # TODO: this needs to be changed in PROD
  scraper = WebScraper()
  scrape_response = await scraper.async_scrape(
    crawl_request.url,
    ArtifactMetadata,
    "Extract the title, summary, abd main_sections."
  )

  crawl_links_response = await _crawl_links(
    admin_supabase,
    upserted_artifact["artifact_id"],
    scrape_response.page_content,
    crawl_request,
    schedule_crawl
  )

  summary = f"{scrape_response.page_title}\n\n{scrape_response.extracted_data.summary}"

  # TODO: this needs to be changed in PROD
  summary_embedding = await _embed_string(summary)

  updated_article_response = await admin_supabase\
    .table("artifacts")\
    .update({
      "crawl_depth": crawl_request.crawl_depth,
      "crawl_status": "scraped",
      "metadata": scrape_response.extracted_data.model_dump(mode='json'),
      "parsed_text": scrape_response.page_content,
      "summary": scrape_response.extracted_data.summary,
      "summary_embedding": str(summary_embedding['embedding']),
      "title": scrape_response.page_title,
      "url": crawl_request.url,
    })\
    .eq("artifact_id", upserted_artifact["artifact_id"])\
    .execute()

  updated_article = Artifact(updated_article_response.data[0])

  return {
    "artifact": updated_article,
    **crawl_links_response
  }

async def _extract_links(
  parsed_content: str,
  base_url: str,
  allowed_url_patterns: List[str],
) -> List[Link]:
  """
  Given a parsed markdown of a content, extract all the links from the content.
  If the link is relative, convert it to an absolute link using the base_url.
  Only return links that match any of the allowed_url_patterns (supports regex).
  Removes anchor fragments from URLs.
  """
  md = MarkdownIt()
  tokens = md.parse(parsed_content)
  links = []

  for token in tokens:
    if token.type == "inline":
      for child in token.children:
        if child.type == "link_open":
          href = child.attrs.get("href", "")
          if href:
            # Remove anchor fragment before creating absolute URL
            href = href.split('#')[0]
            absolute_url = urljoin(base_url, href)

            if any(re.match(pattern, absolute_url) for pattern in allowed_url_patterns):
              text_token = token.children[token.children.index(child) + 1]
              link_text = text_token.content if text_token else ""

              links.append(Link(
                url=absolute_url,
                text=link_text
              ))

  return links

async def _process_existing_artifact(
  admin_supabase: AsyncClient,
  existing_artifact: Artifact,
  base_crawl_event: CrawlRequestedEventData,
  schedule_crawl: ScheduleCrawlFunction = None
) -> dict:
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
  admin_supabase: AsyncClient,
  artifact_id: str,
  parsed_content: str,
  base_crawl_event: CrawlRequestedEventData,
  schedule_crawl: ScheduleCrawlFunction = None
) -> None:
  """
  Process and store links for an artifact.
  Deletes existing links and inserts new ones.
  """
  # Delete existing links
  await admin_supabase\
    .table("artifact_links")\
    .delete()\
    .eq("source_artifact_id", artifact_id)\
    .execute()

  # Extract and process new links
  links = await _extract_links(
    parsed_content,
    base_crawl_event.url,
    base_crawl_event.allowed_url_patterns
  )

  event_payload = [
    CrawlRequestedEventData(
      url=link.url,
      crawl_depth=base_crawl_event.crawl_depth + 1,
      allowed_url_patterns=base_crawl_event.allowed_url_patterns
    ) for link in links if base_crawl_event.crawl_depth + 1 <= MAX_CRAWL_DEPTH
  ]
  event_ids = await schedule_crawl(
    step_id=f"crawl-outbound-links",
    crawl_request=event_payload
  )

  # Prepare and insert new links
  insert_payload = [
    {
      "anchor_text": link.text,
      "source_artifact_id": artifact_id,
      "target_url": link.url
    } for link in links
  ]
  insert_response = await admin_supabase\
    .table("artifact_links")\
    .insert(insert_payload)\
    .execute()

  return {
    "crawl_event_ids": event_ids,
    "insert_ids": insert_response.data
  }



