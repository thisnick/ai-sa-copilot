"""
Simple web scraper with LLM integration
"""
import asyncio
from typing import AsyncGenerator, Optional, List

from aiohttp import ClientTimeout
from .types import ScrapedLink, ScrapedContent, WebScraperResult, ScraperType, ScrapingConfig
from lib.logger import get_logger_from_context

class WebScraper():

  def __init__(
    self,
    headless: bool = True,
    model: str = "gpt-4o-mini",
    scraper: ScraperType = "playwright",
    model_api_base: Optional[str] = 'https://api.openai.com/v1',
    model_api_key: Optional[str] = None,
  scraping_service_api_key: Optional[str] = None,
  ):
    """Initialize the web scraper with configuration options"""
    self.headless = headless
    self.model = model
    self.model_api_base = model_api_base
    self.model_api_key = model_api_key
    self.scraping_service_api_key = scraping_service_api_key
    self.scraper = scraper
    # Playwright configuration
    self.browser_config = {}
    self.RETRY_LIMIT = 3
    self.TIMEOUT = 10

    self.logger = get_logger_from_context()

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

    self.logger.info(f"Scraping with ScrapingFish: {url}")

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
            timeout=ClientTimeout(total=self.TIMEOUT)
          ) as response:
            if response.status != 200:
              raise Exception(f"ScrapingFish API error: {response.status}")

            text = await response.text()
            return text
      except Exception as e:
        attempt += 1
        self.logger.warning(f"Attempt {attempt} failed: {e}")
        if attempt == self.RETRY_LIMIT:
          self.logger.error("Max retries reached. Returning None")
          raise Exception(f"Unable to scrape {url}, error: {e}")

    assert False, "Reached the end of the async_fetch_content_scraping_fish method without returning a value"

  async def async_fetch_content_playwright(self, url: str) -> str:
    """Fetch content from URL using Playwright"""
    from playwright.async_api import async_playwright, Browser
    from undetected_playwright import Malenia

    self.logger.info(f"Scraping with Playwright: {url}")

    attempt = 0
    browser: Optional[Browser] = None
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

          self.logger.info("Content successfully scraped")

          return content
      except Exception as e:
        attempt += 1
        self.logger.warning(f"Attempt {attempt} failed: {e}")
        if attempt == self.RETRY_LIMIT:
          self.logger.error("Max retries reached. Returning None")
          raise Exception(f"Unable to scrape {url}, error: {e}")

      finally:
        if browser:
          await browser.close()

    assert False, "Reached the end of the async_fetch_content_playwright method without returning a value"

  async def extract_page_sections(
    self,
    html_content: str,
    base_url: str,
    scraping_config: ScrapingConfig,
    split_depth: int = 0,
    id_counter: int = 0
  ) -> AsyncGenerator[ScrapedContent, None]:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    sections = soup.select(scraping_config.splitting_selector[split_depth])
    if not sections and split_depth < len(scraping_config.splitting_selector) - 1:
      async for subsection in self.extract_page_sections(html_content, base_url, scraping_config, split_depth + 1, id_counter):
        yield subsection

    for section in sections:
      section_content = str(section)
      if not section_content:
        continue

      parsed_content = self.parse_content(section_content, base_url)

      if len(parsed_content) > scraping_config.max_chunk_size and split_depth < len(scraping_config.splitting_selector) - 1:
        split_successful = False
        async for subsection in self.extract_page_sections(section_content, base_url, scraping_config, split_depth + 1, id_counter):
          id_counter += 1
          split_successful = True
          yield subsection

        if split_successful:
          # Continue to the next section
          continue

      id_counter += 1
      id : Optional[str] = str(section.get('id') or id_counter)
      if scraping_config.section_id_selector:
        id_element = section.select_one(scraping_config.section_id_selector)
        if id_element:
          id = str(id_element.get(scraping_config.section_id_selector))
      section_title_soup = section.select_one(scraping_config.title_selector)
      section_title = section_title_soup.text if section_title_soup else ""

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

  def parse_content(self, html_content: str, base_url: str) -> str:
    """Parse HTML content and extract relevant information"""
    import html2text

    self.logger.info("Parsing content...")

    # Initialize html2text
    h = html2text.HTML2Text(baseurl=base_url)
    h.ignore_links = False
    h.ignore_images = True

    # Extract text content using html2text
    text_content = h.handle(html_content).strip()

    return text_content

  async def async_scrape(
    self,
    url: str,
    scraping_config: ScrapingConfig
  ) -> WebScraperResult:
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
    scraping_config: ScrapingConfig
    ) -> List[WebScraperResult]:
    """Scrape multiple URLs concurrently"""

    tasks = [self.async_scrape(url, scraping_config) for url in urls]
    results = await asyncio.gather(*tasks)
    return results

  def scrape(self, url: str, scraping_config: ScrapingConfig) -> WebScraperResult:
    """Main method to orchestrate the scraping process"""
    return asyncio.run(self.async_scrape(url, scraping_config))

  def scrape_multiple(self, urls: List[str], scraping_config: ScrapingConfig) -> List[WebScraperResult]:
    """Synchronous wrapper for scraping multiple URLs"""
    return asyncio.run(self.async_scrape_multiple(urls, scraping_config))

  def _normalize_url(self, href: str, base_url: str) -> str:
    """Normalize relative URLs to absolute URLs and filter out self-links"""
    from urllib.parse import urljoin, urlparse, urlunparse

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

    # Remove the fragment and reconstruct the URL
    cleaned_parts = parsed_full._replace(fragment='')
    return urlunparse(cleaned_parts)

