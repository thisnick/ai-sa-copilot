import asyncio
from lib.inngest import inngest_client
from api.inngest.events import CrawlRequestedEvent, CrawlRequestedEventData


async def main():
  await inngest_client.send(
    CrawlRequestedEvent(
      data=CrawlRequestedEventData(
      url="https://supabase.com/docs/",
      crawl_depth=1,
        domain_id="470ccd9f-937d-47f4-ad85-8605f0e2194a",
      ),
    ).to_event()
  )


if __name__ == "__main__":
  asyncio.run(main())
