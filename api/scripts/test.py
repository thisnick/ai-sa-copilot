from pydantic import BaseModel, Field
from typing import List
import json
import os
from copy import deepcopy
from lib.scraper import ScrapingConfig, WebScraper, DataExtractor, DataExtractorConfig, WebScraperResult
from lib.metadata import ArtifactMetadata, Link

from dotenv import load_dotenv
load_dotenv(".env")

scraper = WebScraper(
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

scraping_result = scraper.scrape(
    url="https://supabase.com/docs/guides/cron",
    scraping_config=ScrapingConfig(
        splitting_selector=[
          'html',
          'article',
          'section',
        ],
    )
)

data_extractor = DataExtractor(
  verbose=True,
  model="openai/gpt-4o-mini",
  model_api_key=os.getenv("OPENAI_API_KEY"),
)

truncated_scraping_result = deepcopy(scraping_result)
truncated_scraping_result.scraped_sections = truncated_scraping_result.scraped_sections[:5]

extraction_prompt = f"""You are a web scraping assistant. Extract information according to the provided schema.
Extract the title, summary, main content links, and nav_bar_links. This is the schema of the output:\n{metadata_schema_str}"""

extraction_result = data_extractor.extract_from_scraped_data(
  truncated_scraping_result,
  DataExtractorConfig(
    page_extraction_schema=ArtifactMetadata,
    page_extraction_prompt=extraction_prompt,
    section_extraction_schema=ArtifactMetadata,
    section_extraction_prompt=extraction_prompt,
  )
)

print(json.dumps(extraction_result.model_dump(), indent=2))
