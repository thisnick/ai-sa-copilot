import asyncio
from typing import Optional, Tuple, Type, TypeVar
from pydantic import BaseModel
import json

from .types import (
  DataExtractorConfig,
  PageDataExtractionResult,
  SectionDataExtractionResult,
  WebScraperResult,
  TPage,
  TSection,
)

TData = TypeVar("TData", bound=BaseModel)

class DataExtractor():
  def __init__(self,
    model: str = "gpt-4o-mini",
    model_api_base: Optional[str] = 'https://api.openai.com/v1',
    model_api_key: Optional[str] = None,
    verbose: bool = False,
    ):
    self.model = model
    self.model_api_base = model_api_base
    self.model_api_key = model_api_key
    self.verbose = verbose

  def extract_from_scraped_data(
    self,
    scraped_page: WebScraperResult,
    config: DataExtractorConfig[TPage, TSection]
  ) -> PageDataExtractionResult[TPage, TSection]:
    return asyncio.run(self.async_extract_from_scraped_data(scraped_page, config))

  async def async_extract_from_scraped_data(
    self,
    scraped_page: WebScraperResult,
    config: DataExtractorConfig[TPage, TSection]
  ) -> PageDataExtractionResult[TPage, TSection]:

    if self.verbose:
      print("Extracting full page data using LLM...")

    whole_page_summary, whole_page_data = await self._async_extract_data(
      scraped_page.page_content,
      scraped_page.page_title,
      config.page_extraction_prompt,
      config.page_extraction_schema,
    )

    if self.verbose:
      print("Extracting section data using LLM...")

    raw_sections_data = await asyncio.gather(*[
      self._async_extract_data(
        section.content,
        section.title,
        config.section_extraction_prompt,
        config.section_extraction_schema,
        whole_page_summary,
      )
      for section in scraped_page.scraped_sections
    ])

    return PageDataExtractionResult(
      whole_page_summary=whole_page_summary,
      whole_page_data=whole_page_data,
      sections_data=[
        SectionDataExtractionResult(
          section_summary=section_summary,
          section_data=section_data,
        )
        for section_summary, section_data in raw_sections_data
      ]
    )

  async def _async_extract_data(
    self,
    parsed_content: str,
    title: str,
    extraction_prompt: str,
    extraction_schema: Type[TData],
    context: Optional[str] = None,
  ) -> Tuple[str, TData]:
    from litellm import acompletion
    # Truncate content to 50k characters
    truncated_content = f"{parsed_content[:50000]}..." if len(parsed_content) > 50000 else parsed_content

    if not context:
      summary_prompt = f"""
      1. Analyze the input text and generate 5 essential questions that, when answered, capture the main points and core meaning of the text.
      2. When formulating your questions:
        a. Address the central idea, theme or argument
        b. Identify key supporting ideas
        c. Highlight unique and important facts or evidence
        d. Reveal the document's purpose and goals
        e. Explore any significant implications or conclusions.
      3. Answer all of your generated questions one-by-one succinctly in 2-3 sentences as main points of the document.
      4. Do not include the questions. Output the main points only.

      Output format:
      * <Main point 1> (reframed from answer to question 1)
      * <Main point 2> (reframed from answer to question 2)
      ...
      """
      content_message = f"""
<Document>
  <Title>{title}</Title>
  <Content>{truncated_content}</Content>
</Document>
"""
    else:
      summary_prompt = f"""
      1. You are analyzing the document chunk within a given document context. Generate 5 essential questions that, when answered, capture the main points and core meaning of the text
         within the given context. Your goal is to improve search retrieval of the content, and your questions should be situated within the context.
      2. When formulating your questions:
        a. Address the central idea, theme or argument
        b. Identify key supporting ideas
        c. Highlight unique and important facts or evidence
        d. Reveal the document's purpose and goals
        e. Explore any significant implications or conclusions.
        f. Makes sense of the content by using the context.
      3. Answer all of your generated questions one-by-one succinctly in 2-3 sentences as main points of the document.
      4. Do not include the questions. Output the main points only.

      Output format:
      * <Main point 1> (reframed from answer to question 1)
      * <Main point 2> (reframed from answer to question 2)
      ...
      """
      content_message = f"""
<ParentDocumentContext>
  {context}
</ParentDocumentContext>
<DocumentChunkToAnalyze>
  <Heading>{title}</Heading>
  <Content>{truncated_content}</Content>
</DocumentChunkToAnalyze>"""

    summary_messages = [
      {"role": "system", "content": summary_prompt},
      {"role": "user", "content": content_message}
    ]

    summary_response = await acompletion(
      model=self.model,
      messages=summary_messages,
      temperature=0.7,
      api_base=self.model_api_base,
      api_key=self.model_api_key,
    )

    summary_result = summary_response.choices[0].message.content

    extract_messages = [
      {"role": "system", "content": extraction_prompt},
      {"role": "user", "content": f"<Title>{title}</Title>\n\n<Content>{truncated_content}</Content>"}
    ]

    extract_response = await acompletion(
      model=self.model,
      messages=extract_messages,
      response_format=extraction_schema,
      temperature=0.7,
      api_base=self.model_api_base,
      api_key=self.model_api_key,
    )

    extract_result = extract_response.choices[0].message.content
    try:
      raw_result = json.loads(extract_result)
      extracted_page_data = extraction_schema.model_validate(raw_result)
      return summary_result, extracted_page_data
    except Exception as e:
      if self.verbose:
        print(f"Warning: Failed to parse or validate LLM response: {e}")
      raise ValueError(f"Failed to parse or validate LLM response: {e}")

