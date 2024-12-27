from pydantic import BaseModel, Field
from typing import List
import json
import os
from api.lib.scraper import WebScraper

from dotenv import load_dotenv
load_dotenv(".env")

class Section(BaseModel):
    heading: str = Field(
        description="The heading of the section"
    )
    content_summary: str = Field(
        description="2-3 sentence about what this section contains and what it can accomplish."
    )

class Link(BaseModel):
    """Represents a hyperlink found within text content."""

    url: str = Field(
        description="The URL/href of the link"
    )
    text: str = Field(
        description="The visible text/anchor text of the link"
    )

class Metadata(BaseModel):
    """Contains metadata information extracted from a webpage or document."""

    title: str = Field(
        description="The title of the webpage or document"
    )
    summary: str = Field(
        description="3-5 sentences of what this article is about and what it can accomplish."
    )
    main_sections: List[Section] = Field(
        description="A list of the main sections of the article"
    )

scraper = WebScraper(
  verbose=True,
  model="openai/gpt-4o-mini",
  model_api_key=os.getenv("OPENAI_API_KEY")

)

# ************************************************
# Create the SmartScraperGraph instance and run it
# ************************************************
metadata_schema_str = json.dumps(Metadata.model_json_schema())
prompt=f"Extract the title, summary, main content links, and nav_bar_links. This is the schema of the output:\n{metadata_schema_str}"

result = scraper.scrape(
    prompt=prompt,
    schema=Metadata,
    url="https://docs.databricks.com/en/admin/account-settings-e2/credentials.html"
)

print(result.extracted_data.model_dump_json(indent=2))
