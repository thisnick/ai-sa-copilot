from typing import List
from pydantic import BaseModel, Field

class ArtifactSection(BaseModel):
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

class ArtifactMetadata(BaseModel):
  """Contains metadata information extracted from a webpage or document."""

  title: str = Field(
    description="The title of the webpage or document"
  )
  summary: str = Field(
    description="3-5 sentences of what this article is about and what it can accomplish."
  )
  main_sections: List[ArtifactSection] = Field(
    description="A list of the main sections of the article"
  )

  is_deprecated: bool = Field(
    description="Whether this article has marked itself as deprecated or archived"
  )

  new_version_url: str = Field(
    description="The URL of the new version of this article if it includes a link to a newer version of this article"
  )

Prompt = """Given a webpage or document, analyze its content and provide a structured summary following this exact JSON format:

{
  "title": "The main title of the page",
  "summary": "A 3-5 sentence overview describing what this article covers and what readers can accomplish with it.",
  "main_sections": [
    {
      "heading": "First Major Section Title",
      "content_summary": "2-3 sentences describing what this section contains and its key points."
    },
    {
      "heading": "Second Major Section Title",
      "content_summary": "2-3 sentences describing what this section contains and its key points."
    }
  ],
  "is_deprecated": false,
  "new_version_url": ""
}

Important requirements:
- The summary should be 3-5 complete sentences that capture the main purpose and value of the content
- Each section's content_summary should be 2-3 sentences
- Include all major sections from the document
- Set is_deprecated to true if the content is marked as deprecated/archived
- Include new_version_url only if there's a specific link to a newer version of the content
- Ensure the output is valid JSON that matches this exact structure

Please analyze the content and provide the structured data in this format.
"""
