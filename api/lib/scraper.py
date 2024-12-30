"""
Simple web scraper with LLM integration
"""
import asyncio
from typing import AsyncGenerator, Literal, Optional, Dict, Any, List, Type, TypeAlias, TypeVar, Generic, LiteralString, Union
from pydantic import BaseModel
from pydantic_core import to_json as pydantic_to_json

T = TypeVar('T', bound=BaseModel)

class ScrapedLink(BaseModel):
  url: str
  anchor_text: str

class ScrapedContent(BaseModel):
  id: Optional[str] = None
  content: str
  title: str
  extracted_data: Optional[T] = None
  scraped_links: List[ScrapedLink] = []

class WebScraperResult(BaseModel, Generic[T]):
  url: str
  page_title: str
  page_content: str
  scraped_sections: List[ScrapedContent]

ScraperType : TypeAlias = Literal['playwright', 'scraping_fish']

class ScrapingConfig(BaseModel, Generic[T]):
  splitting_selector: List[str] = [
    'html',
    'article',
    'section',
  ]
  max_chunk_size: int = 50000
  title_selector: str = 'title, h1, h2, h3'
  section_id_selector: Optional[str] = None
  schema: Type[T]
  prompt: str

class WebScraper():

  def __init__(
    self,
    headless: bool = True,
    verbose: bool = False,
    model: str = "gpt-4o-mini",
    scraper: ScraperType = "playwright",
    model_api_base: Optional[str] = 'https://api.openai.com/v1',
    model_api_key: Optional[str] = None,
  scraping_service_api_key: Optional[str] = None,
  ):
    """Initialize the web scraper with configuration options"""
    self.headless = headless
    self.verbose = verbose
    self.model = model
    self.model_api_base = model_api_base
    self.model_api_key = model_api_key
    self.scraping_service_api_key = scraping_service_api_key
    self.scraper = scraper
    # Playwright configuration
    self.browser_config = {}
    self.RETRY_LIMIT = 3
    self.TIMEOUT = 10

  async def async_fetch_content(self, url: str) -> str:
    if self.scraper == "playwright":
      return await self.async_fetch_content_playwright(url)
    elif self.scraper == "scraping_fish":
      return await self.async_fetch_content_scraping_fish(url)
    else:
      raise ValueError(f"Invalid scraper: {self.scraper}")

  async def async_fetch_content_scraping_fish(self, url: str) -> str:
    """Fetch content from URL using ScrapingFish API"""
    import aiohttp
    import json

    if not self.scraping_service_api_key:
      raise ValueError("ScrapingFish requires an API key. Please provide it via scraping_service_api_key parameter.")

    if self.verbose:
      print(f"Fetching content from: {url}")

    params = {
      "api_key": self.scraping_service_api_key,
      "url": url,
      "trial_timeout_ms": self.TIMEOUT * 1000,
    }

    attempt = 0
    while attempt < self.RETRY_LIMIT:
      try:
        async with aiohttp.ClientSession() as session:
          async with session.get(
            "https://scraping.narf.ai/api/v1/",
            params=params,
            timeout=self.TIMEOUT
          ) as response:
            if response.status != 200:
              raise Exception(f"ScrapingFish API error: {response.status}")

            text = await response.text()
            return text
      except Exception as e:
        attempt += 1
        if self.verbose:
          print(f"Attempt {attempt} failed: {e}")
        if attempt == self.RETRY_LIMIT:
          return WebScraper.FetchContentResult(
            content=f"Error: Network error after {self.RETRY_LIMIT} attempts - {e}",
            title="Error"
          )

  async def async_fetch_content_playwright(self, url: str) -> str:
    """Fetch content from URL using Playwright"""
    from playwright.async_api import async_playwright
    from undetected_playwright import Malenia

    if self.verbose:
      print(f"Fetching content from: {url}")

    attempt = 0

    while attempt < self.RETRY_LIMIT:
      try:
        async with async_playwright() as p:
          browser = await p.chromium.launch(
            headless=self.headless,
            **self.browser_config
          )
          context = await browser.new_context()
          await Malenia.apply_stealth(context)

          page = await context.new_page()
          await page.goto(url, wait_until="domcontentloaded")
          await page.wait_for_load_state("domcontentloaded")

          content = await page.content()

          if self.verbose:
            print("Content successfully scraped")

          return content
      except Exception as e:
        attempt += 1
        if self.verbose:
          print(f"Attempt {attempt} failed: {e}")
        if attempt == self.RETRY_LIMIT:
          return f"Error: Network error after {self.RETRY_LIMIT} attempts - {e}"

      finally:
        await browser.close()

  async def extract_page_sections(
    self,
    html_content: str,
    base_url: str,
    scraping_config: ScrapingConfig[T],
    split_depth: int = 0,
    id_counter: int = 0
  ) -> AsyncGenerator[ScrapedContent, None]:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    for section in soup.select(scraping_config.splitting_selector[split_depth]):
      section_content = str(section)
      if not section_content:
        continue

      if len(section_content) > scraping_config.max_chunk_size and split_depth < len(scraping_config.splitting_selector) - 1:
        split_successful = False
        async for subsection in self.extract_page_sections(section_content, base_url, scraping_config, split_depth + 1, id_counter):
          id_counter += 1
          split_successful = True
          yield subsection

        if split_successful:
          # Continue to the next section
          continue

      id_counter += 1
      id : Optional[str] = section.get('id') or str(id_counter)
      if scraping_config.section_id_selector:
        id_element = section.select_one(scraping_config.section_id_selector)
        if id_element:
          id = id_element.get(scraping_config.section_id_selector)
      section_title_soup = section.select_one(scraping_config.title_selector)
      section_title = section_title_soup.text if section_title_soup else ""
      parsed_content = self.parse_content(section_content, base_url)
      links = section.find_all('a')
      scraped_links = [
        ScrapedLink(
          url=self._normalize_url(link.get('href'), base_url),
          anchor_text=link.text.strip()
        )
        for link in links
        if self._normalize_url(link.get('href'), base_url) and link.text.strip()
      ]
      # extracted_data = await self.async_extract_data(parsed_content, section_title, scraping_config.schema, scraping_config.prompt)
      yield ScrapedContent(
        id=id,
        content=parsed_content,
        title=section_title,
        scraped_links=scraped_links,
        # extracted_data=extracted_data
      )

  def parse_content(self, html_content: str, base_url: str) -> Dict[str, Any]:
    """Parse HTML content and extract relevant information"""
    import html2text

    if self.verbose:
      print("Parsing content...")

    # Initialize html2text
    h = html2text.HTML2Text(baseurl=base_url)
    h.ignore_links = False
    h.ignore_images = True

    # Extract text content using html2text
    text_content = h.handle(html_content).strip()

    return text_content

  async def async_extract_data(self, parsed_content: str, title: str, schema: Type[T], prompt: str) -> T:
    """Extract structured data using LiteLLM"""
    import json
    from litellm import acompletion

    if self.verbose:
      print("Extracting data using LLM...")

    # Prepare the message for the LLM
    system_prompt = f"""You are a web scraping assistant. Extract information according to the provided schema.
Follow these instructions:
{prompt}"""

    messages = [
      {"role": "system", "content": system_prompt},
      {"role": "user", "content": f"Page Title: {title}\n\nContent:\n{parsed_content}"}
    ]

    # Call LiteLLM with response format
    response = await acompletion(
      model=self.model,
      messages=messages,
      temperature=0.7,
      max_tokens=1500,
      response_format=schema,
      api_base=self.model_api_base,
      api_key=self.model_api_key,
    )

    # Parse and validate the response
    try:
      raw_result = json.loads(response.choices[0].message.content)
      # Validate against the schema
      result = schema.model_validate(raw_result)
      return result
    except Exception as e:
      if self.verbose:
        print(f"Warning: Failed to parse or validate LLM response: {e}")
      raise ValueError(f"Failed to parse or validate LLM response: {e}")

  async def async_scrape(self, url: str, scraping_config: ScrapingConfig[T]) -> WebScraperResult[T]:
    """Async version of the main scraping method"""
    # 1. Fetch the document
    html_content = await self.async_fetch_content(url)
    parsed_content = self.parse_content(html_content, url)
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    title = soup.title.text if soup.title else ""

    sections = [
      section
      async for section in self.extract_page_sections(html_content, url, scraping_config)
    ]

    return WebScraperResult(
      url=url,
      page_title=title,
      page_content=parsed_content,
      scraped_sections=sections,
    )

  async def async_scrape_multiple(
    self,
    urls: List[str],
    scraping_config: ScrapingConfig[T]
    ) -> List[WebScraperResult[T]]:
    """Scrape multiple URLs concurrently"""

    tasks = [self.async_scrape(url, scraping_config) for url in urls]
    results = await asyncio.gather(*tasks)
    return results

  def scrape(self, url: str, scraping_config: ScrapingConfig[T]) -> WebScraperResult[T]:
    """Main method to orchestrate the scraping process"""
    return asyncio.run(self.async_scrape(url, scraping_config))

  def scrape_multiple(self, urls: List[str], scraping_config: ScrapingConfig[T]) -> List[WebScraperResult[T]]:
    """Synchronous wrapper for scraping multiple URLs"""
    return asyncio.run(self.async_scrape_multiple(urls, scraping_config))

  def _normalize_url(self, href: str, base_url: str) -> str:
    """Normalize relative URLs to absolute URLs and filter out self-links"""
    from urllib.parse import urljoin, urlparse

    if not href:
      return ""

    # Handle fragment-only URLs (anchor links)
    if href.startswith('#'):
      return ""

    # Parse both URLs
    parsed_href = urlparse(href)
    parsed_base = urlparse(base_url)

    # If there's no scheme (protocol) or netloc (domain), it's relative
    if not parsed_href.scheme and not parsed_href.netloc:
      full_url = urljoin(base_url, href)
      parsed_full = urlparse(full_url)
    else:
      full_url = href
      parsed_full = parsed_href

    # Check if it points to the same page
    if (parsed_full.scheme == parsed_base.scheme and
        parsed_full.netloc == parsed_base.netloc and
        parsed_full.path == parsed_base.path):
      return ""

    return full_url

