from typing import Literal, Optional, List, Type, TypeAlias, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)
TPage = TypeVar('TPage', bound=BaseModel)
TSection = TypeVar('TSection', bound=BaseModel)

class ScrapedLink(BaseModel):
  url: str
  anchor_text: str

class ScrapedContent(BaseModel):
  id: Optional[str] = None
  content: str
  title: str
  scraped_links: List[ScrapedLink] = []

class WebScraperResult(BaseModel):
  url: str
  page_title: str | None = None
  page_content: str
  scraped_sections: List[ScrapedContent]

ScraperType : TypeAlias = Literal['playwright', 'scraping_fish']

class ScrapingConfig(BaseModel):
  splitting_selector: List[str] = [
    'html',
    'article',
    'section',
  ]
  max_chunk_size: int = 50000
  title_selector: str = 'title, h1, h2, h3'
  section_id_selector: Optional[str] = None

class DataExtractorConfig(BaseModel, Generic[TPage, TSection]):
  section_extraction_schema: Type[TSection]
  section_extraction_prompt: str
  page_extraction_schema: Type[TPage]
  page_extraction_prompt: str

class SectionDataExtractionResult(BaseModel, Generic[TSection]):
  section_summary: str
  section_data: TSection

class PageDataExtractionResult(BaseModel, Generic[TPage, TSection]):
  whole_page_summary: str
  whole_page_data: TPage
  sections_data: List[SectionDataExtractionResult]
