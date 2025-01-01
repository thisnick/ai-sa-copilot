from typing import List
from lib.inngest_context import with_inngest_step, get_inngest_step_from_context
from lib.logger import with_logger
from lib.inngest import inngest_client
from lib.supabase import create_async_supabase_admin_client
from .events import ResumeCrawlEvent, CrawlRequestedEvent, CrawlRequestedEventData
import inngest

@inngest_client.create_function(
  fn_id="resume_crawl",
  trigger=inngest.TriggerEvent(event=ResumeCrawlEvent.name),
  concurrency=[
    inngest.Concurrency(limit=1),
  ],
)
async def resume_crawl(ctx: inngest.Context, step: inngest.Step):
  with with_logger(ctx.logger), with_inngest_step(step):
    batch_size = 100
    page = 0
    total_sent_events : List[str] = []

    while True:
      sent_events = await step.run(
        f"crawl_url_batch_{page}",
        lambda: _crawl_url_batch(page, batch_size),
      )
      total_sent_events.extend(sent_events)
      if len(sent_events) < batch_size:
        break
      page += 1

    return {
      "sent_events": total_sent_events,
    }

async def _crawl_url_batch(page: int, batch_size: int) -> List[str]:
  supabase = await create_async_supabase_admin_client()
  unfinished_artifacts = await (
    supabase
      .table("artifacts")
      .select("*")
      .in_("crawl_status", ["discovered", "scraping", "scrape_failed"])
      .order("artifact_id")
      .range(page * batch_size, (page + 1) * batch_size - 1)
      .execute()
  )

  if not unfinished_artifacts.data:
    return []

  event_to_send: List[inngest.Event] = [
    CrawlRequestedEvent(
      data=CrawlRequestedEventData(
        url=artifact["url"],
        domain_id=artifact["domain_id"],
        crawl_depth=artifact["crawl_depth"],
      )
    ).to_event()
    for artifact in unfinished_artifacts.data
  ]

  step = get_inngest_step_from_context()

  return await step.send_event(f"send_events_batch_{page}", event_to_send)
