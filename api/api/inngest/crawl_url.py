from lib.inngest_context import with_inngest_step
from lib.logger import with_logger
from lib.inngest import inngest_client
from .crawler import run_crawl_url
from .events import CrawlRequestedEvent
import inngest

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

  with with_logger(ctx.logger), with_inngest_step(step):
    return await run_crawl_url(
      event.data,
    )
