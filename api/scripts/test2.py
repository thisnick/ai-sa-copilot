import asyncio
import uuid

from api.inngest.crawler import _crawl_url
from api.inngest.events import CrawlRequestedEventData


if __name__ == "__main__":
    crawl_request = CrawlRequestedEventData(
        url="https://docs.databricks.com/en/admin/account-settings-e2/credentials.html",
        crawl_depth=1,
        allowed_url_patterns=["^https:\\/\\/docs\\.databricks\\.com\\/en\\/.*$"]
    )
    async def schedule_crawl(step_id, crawl_request):
        print(f"Sending event {step_id} for {crawl_request}")
        return [str(uuid.uuid4())]

    asyncio.run(_crawl_url(
        crawl_request=crawl_request,
        schedule_crawl=schedule_crawl,
    ))


# {
#   "data": {
#     "allowed_url_patterns": [
#       "^https:\\/\\/docs\\.databricks\\.com\\/en\\/.*$"
#     ],
#     "crawl_depth": 1,
#     "url": "https://docs.databricks.com/en/index.html"
#   }
# }
