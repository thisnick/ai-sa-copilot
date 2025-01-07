import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from swarm import AsyncAgent
from swarm.types import AsyncResult

from lib.config import Settings

from .agent_map import AGENT_RUNBOOK_SECTION_WRITING
from .tools import (
  async_get_artifacts,
  async_get_knowledge_topics,
  async_query_for_artifacts,
  format_artifacts,
  format_topic_artifacts,
  format_knowledge_topics,
  format_runbook_section_outline,
  format_written_sections
)
from lib.config import Settings

from .types import ContextVariables
from .agent_map import AGENT_RUNBOOK_SECTION_WRITING

def create_runbook_section_writing_agent(settings: Settings) -> AsyncAgent:
  async def instructions(context_variables: ContextVariables):
    current_section_idx = context_variables.get("current_runbook_section") or 0
    current_section = (context_variables.get("runbook_sections") or [])[current_section_idx or 0]
    saved_artifacts = context_variables.get("saved_artifacts", {})
    section_research_artifacts = (context_variables.get("section_research_artifacts") or {}).get(current_section_idx) or []

    domain_id = context_variables.get("domain_id")
    formatted_topics = format_knowledge_topics(await async_get_knowledge_topics(domain_id)) if domain_id else ""


    prompt = f"""You are an agent responsible for fleshing out the detail sections
of a runbook to set up a software system.

Here is your workflow:
1. Review the contexts provided to you, which will include:
    - User requirements for the entire runbook
    - Previous sections that are already written
    - The outline of the section you are writing
    - Some supporting artifacts that will help you write the section
    - Core topics and key concepts that the knowledge base contains.
2. After reviewing, determine whether you need to retrieve the actual artifact content or
   query for additional artifacts to give you more detailed information.
   Remember, never make up information without retrieving the actual artifact content.
   Do not rely only on summaries to write the section. You should reference only the
   artifact contents, either in the contexts or retrieved.
3. If none of the related artifacts may contain the information you need, you can call
   `query_for_artifacts` to search for more artifacts, which will give you summaries
   of the artifacts that are related to the queries. You can use the knowledge topics and
   key concepts to help you find the most relevant artifacts.
4. After you have determined which artifacts you need to write your section, be sure
   to call `retrieve_artifacts` to get the actual contents of the artifacts. You
   should only use the contents from the actual artifacts, not the summaries.
5. If you have gathered all the article contents you need to start writing, call
   "submit_writing_for_section" to submit the section content and move on. Normally,
   you should continue writing the next section unless the user specifically asked
   you to write only one section.
6. You will write the section content in the markdown format. Follow this format:
```
   ## Section Title
   ### Goals

   Describe the goals of the section in a few sentences.

   ### High-level Steps

   1. Step n.1
   2. Step n.2
   3. Step n.3

   ### Step n.1

   ### Step n.1.1

   ...
   References:
   - [Reference 1](https://example.com)
   - [Reference 2](https://example.com)
```
5. If all the sections are written. You can inform the user the run book is complete.

Remember:
* When writing your section, be as detailed and comprehensive as possible. Provide
  complete information that users need to achieve their goals. Avoid directing users
  to external URLs unless it's necessary to gather specific information that
  will influence their next steps. Retain as much information as possible from the
  retrieved artifacts.
* It's important you repeat the above steps for each section unless you already have
  all the information you need to write the section.

# User requirements:

{context_variables.get("user_requirements")}

# Written sections:

{format_written_sections((context_variables.get("runbook_sections") or []), up_to=current_section_idx)}

# Unwritten sections:

{sum(1 for section in context_variables.get("runbook_sections") or [] if not section.content)}

# Outline of the section you are writing:

{format_runbook_section_outline(current_section)}

# Core topics and key concepts that can be looked up in the knowledge base:

{formatted_topics}

# Artifacts matched with the user requirements:

{format_topic_artifacts(saved_artifacts or {}, treat_metadata_as_content=True, include_links=True)}

# Full text of retrieved artifacts:

{format_artifacts(section_research_artifacts, include_links=False, treat_metadata_as_content=False)}
    """
    return prompt

  async def async_retrieve_artifacts(context_variables: ContextVariables, artifact_content_ids: List[str]) -> AsyncResult:
    try:
      if isinstance(artifact_content_ids, str):
        artifact_content_ids = json.loads(artifact_content_ids)

      artifacts = await async_get_artifacts(artifact_content_ids)

      current_section_idx = context_variables.get("current_runbook_section") or 0
      existing_section_research_artifacts = context_variables.get("section_research_artifacts") or {}
      existing_section_research_artifacts[current_section_idx] = artifacts

      return AsyncResult(
        value=f"Artifacts (ids: {artifact_content_ids}) retrieved. They are available to you in the system instructions in the 'Full text of retrieved artifacts' section.",
        context_variables={
          "section_research_artifacts": existing_section_research_artifacts
        }
      )
    except Exception as e:
      logging.error(f"Error in async_retrieve_artifacts: {str(e)}")
      return AsyncResult(value=f"Error retrieving artifacts: {e}")

  async def query_for_artifacts(context_variables: ContextVariables, queries: List[str]):
    """Query for artifacts that are related to the queries and return their summaries"""
    try:
      if isinstance(queries, str):
        queries = json.loads(queries)
      domain_id = context_variables.get("domain_id")
      assert domain_id is not None, "Domain ID is required"

      return await async_query_for_artifacts(queries, domain_id)
    except Exception as e:
      logging.error(f"Error in query_for_artifacts: {str(e)}")
      return AsyncResult(value=f"Error querying for artifacts: {e}")

  async def retrieve_artifacts(context_variables: ContextVariables, artifact_content_ids: List[str]) -> AsyncResult:
    """Retrieve the contents of the related artifacts."""
    try:
      return await async_retrieve_artifacts(context_variables, artifact_content_ids)
    except Exception as e:
      logging.error(f"Error in retrieve_artifacts: {str(e)}")
      return AsyncResult(value=f"Error retrieving artifacts: {e}")

  def get_next_unwritten_section_index(context_variables: ContextVariables, start_index: int) -> Optional[int]:
    """Get the next unwritten section from the runbook sections array."""
    runbook_sections = context_variables.get("runbook_sections") or []
    for idx, section in enumerate(runbook_sections[start_index:]):
      if not section.content:
        return idx
    return None

  async def submit_writing_for_section(
    context_variables: ContextVariables,
    section_content: str,
    continue_writing_next_section: bool = True
  ) -> AsyncResult:
    try:
      current_section_idx = context_variables.get("current_runbook_section") or 0
      all_sections = (context_variables.get("runbook_sections") or []).copy()

      if not all_sections:
        logging.warning("No runbook sections found in context")
        return AsyncResult(value="Error: No runbook sections found in context")

      current_section = all_sections[current_section_idx]
      current_section.content = section_content
      next_unwritten_section_index = get_next_unwritten_section_index(context_variables, current_section_idx + 1)

      if not next_unwritten_section_index or not continue_writing_next_section:
        if context_variables.get("debug", False):
          logging.debug("Session writing complete: %s", context_variables.get("runbook_sections", {}))

        from .research_coordinator_agent import create_research_coordinator_agent
        logging.info("All sections complete, handing off to research coordinator")
        return AsyncResult(
          value="Section writing complete. Handing off to research coordinator agent.",
          context_variables={
            "runbook_sections": all_sections,
            "current_runbook_section": None,
          },
          agent=create_research_coordinator_agent(settings)
        )

      logging.info(f"Moving to section {current_section_idx + 1}")
      return AsyncResult(
        value=f"Section {current_section_idx + 1} written. Ready to write the next section.",
        context_variables={
          "runbook_sections": all_sections,
          "current_runbook_section": next_unwritten_section_index
        },
        agent=create_runbook_section_writing_agent(settings)
      )
    except Exception as e:
      logging.error(f"Error in submit_writing_for_section: {str(e)}")
      return AsyncResult(value=f"Error submitting writing for section: {e}")

  return AsyncAgent(
    name=AGENT_RUNBOOK_SECTION_WRITING,
    instructions=instructions,
    functions=[query_for_artifacts, retrieve_artifacts, submit_writing_for_section],
    tool_choice="required",
    model=settings.agent_llm_model
  )
