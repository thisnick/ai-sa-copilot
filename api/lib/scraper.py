"""
Simple web scraper with LLM integration
"""
import asyncio
from typing import Optional, Dict, Any, List, Type, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class WebScraperResult(BaseModel, Generic[T]):
  url: str
  page_content: str
  page_title: str
  extracted_data: T

class WebScraper():
  def __init__(
    self,
    headless: bool = True,
    verbose: bool = False,
    model: str = "gpt-4o-mini",
    model_api_base: Optional[str] = 'https://api.openai.com/v1',
    model_api_key: Optional[str] = None
  ):
    """Initialize the web scraper with configuration options"""
    self.headless = headless
    self.verbose = verbose
    self.model = model
    self.model_api_base = model_api_base
    self.model_api_key = model_api_key
    # Playwright configuration
    self.browser_config = {}
    self.load_state = "domcontentloaded"
    self.RETRY_LIMIT = 3
    self.TIMEOUT = 10

  async def async_fetch_content(self, url: str) -> Dict[str, Any]:
    """Fetch content from URL using Playwright"""
    from playwright.async_api import async_playwright
    from undetected_playwright import Malenia

    if self.verbose:
      print(f"Fetching content from: {url}")

    results = {"content": "", "title": ""}
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
          await page.wait_for_load_state(self.load_state)

          results["content"] = await page.content()
          results["title"] = await page.title()

          if self.verbose:
            print("Content successfully scraped")
          break
      except Exception as e:
        attempt += 1
        if self.verbose:
          print(f"Attempt {attempt} failed: {e}")
        if attempt == self.RETRY_LIMIT:
          results["content"] = f"Error: Network error after {self.RETRY_LIMIT} attempts - {e}"
          results["title"] = "Error"
      finally:
        await browser.close()

    return results

  def parse_content(self, html_content: str, base_url: str) -> Dict[str, Any]:
    """Parse HTML content and extract relevant information"""
    import html2text

    if self.verbose:
      print("Parsing content...")

    # Initialize html2text
    h = html2text.HTML2Text()
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

  async def async_scrape(self, url: str, schema: Type[T], prompt: str) -> WebScraperResult[T]:
    """Async version of the main scraping method"""
    # 1. Fetch the document
    html_content = await self.async_fetch_content(url)

    # 2. Parse the document
    parsed_content = self.parse_content(html_content["content"], url)

    # 3. Extract structured data using LLM
    result = await self.async_extract_data(parsed_content, html_content["title"], schema, prompt)

    return WebScraperResult(url=url, page_content=parsed_content, page_title=html_content["title"], extracted_data=result)

  async def async_scrape_multiple(self, urls: List[str], schema: Type[T], prompt: str) -> List[WebScraperResult[T]]:
    """Scrape multiple URLs concurrently"""

    tasks = [self.async_scrape(url, schema, prompt) for url in urls]
    results = await asyncio.gather(*tasks)
    return results

  def scrape(self, url: str, schema: Type[T], prompt: str) -> WebScraperResult[T]:
    """Main method to orchestrate the scraping process"""
    return asyncio.run(self.async_scrape(url, schema, prompt))

  def scrape_multiple(self, urls: List[str], schema: Type[T], prompt: str) -> List[WebScraperResult[T]]:
    """Synchronous wrapper for scraping multiple URLs"""
    return asyncio.run(self.async_scrape_multiple(urls, schema, prompt))
