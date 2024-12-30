from pydantic import BaseModel, Field
from typing import List
import json
import os
from lib.scraper import ScrapingConfig, WebScraper
from lib.metadata import ArtifactMetadata, Link

from dotenv import load_dotenv
load_dotenv(".env")

scraper = WebScraper(
  verbose=True,
  model="openai/gpt-4o-mini",
  model_api_key=os.getenv("OPENAI_API_KEY"),
  scraping_service_api_key=os.getenv("SCRAPING_FISH_API_KEY"),
  scraper="scraping_fish"
)

# ************************************************
# Create the SmartScraperGraph instance and run it
# ************************************************
metadata_schema_str = json.dumps(ArtifactMetadata.model_json_schema())
prompt=f"Extract the title, summary, main content links, and nav_bar_links. This is the schema of the output:\n{metadata_schema_str}"

result = scraper.scrape(
    url="https://supabase.com/docs/guides/getting-started/quickstarts/ruby-on-rails",
    scraping_config=ScrapingConfig(
        prompt=prompt,
        schema=ArtifactMetadata,
        splitting_selector=[
          'html',
          'article',
          'section',
        ],
    )
)

print(result.scraped_sections)
