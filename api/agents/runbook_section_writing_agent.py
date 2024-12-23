import asyncio
import json
from typing import Any, Dict, List

from swarm import AsyncAgent
from swarm.types import AsyncResult

from api.config import Settings

from .agent_map import AGENT_RUNBOOK_SECTION_WRITING
from .tools import (
  async_get_artifacts,
  async_get_knowledge_topics,
  async_query_for_artifacts,
  format_artifacts,
  format_knowledge_topics,
  format_runbook_section_outline,
  format_written_sections
)
from api.config import Settings

from .types import ContextVariables
from .agent_map import AGENT_RUNBOOK_SECTION_WRITING

def create_runbook_section_writing_agent(settings: Settings) -> AsyncAgent:
  async def instructions(context_variables: ContextVariables):
    current_section_idx = context_variables.get("current_runbook_section") or 0
    current_section = (context_variables.get("runbook_sections") or [])[current_section_idx or 0]
    artifacts = [
      artifact
      for topic, artifacts in (context_variables.get("saved_artifacts") or {}).items()
      for artifact in artifacts
      if artifact.artifact_id in current_section.related_artifacts
    ]
    section_research_artifacts = (context_variables.get("section_research_artifacts") or {}).get(current_section_idx) or []
    artifacts = artifacts + section_research_artifacts
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
2. After reviewing, determine whether you have what you need from the artifact to write
    the section, or you need to retrieve a related artifact. Remember, never make up
    writing. You should reference only the artifact contents, either in the contexts or retrieved.
3. If none of the related artifacts may contain the information you need, you can call
    `query_for_artifacts` to search for more artifacts, which will give you summaries
    of the artifacts that are related to the queries. You can use the core topics and
    key concepts to help you craft queries with more hits.
4. After you have determined which artifacts you need to write your section, be sure
   to call `retrieve_artifacts` to get the actual contents of the artifacts. You
   should only use the contents from the actual artifacts, not the summaries.
5. If you have gathered all the article contents you need to start writing, call
   "submit_writing_for_section" to submit the section content and move on.
    You will write the section content in the markdown format. Follow this format:
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
  will influence their next steps.
* It's important you repeat the above steps for each section unless you already have
  all the information you need to write the section.

# User requirements:

{context_variables.get("user_requirements")}

# Written sections:

{format_written_sections((context_variables.get("runbook_sections") or []), up_to=current_section_idx)}

# Outline of the section you are writing:

{format_runbook_section_outline(current_section)}

# Core topics and key concepts in the knowledge base:

{formatted_topics}

# Supporting artifacts for this section:

{format_artifacts(artifacts, include_links=True)}
    """
    return prompt

  async def async_retrieve_artifacts(context_variables: ContextVariables, artifact_ids: List[str]) -> AsyncResult:
    if isinstance(artifact_ids, str):
      artifact_ids = json.loads(artifact_ids)

    artifacts = await async_get_artifacts(artifact_ids, with_links=False)

    # saved_artifacts = context_variables.get("saved_artifacts", {}).copy()
    # current_topic = context_variables["research_topics"][context_variables["current_expansion_topic"]]
    # existing_artifacts_for_topic = saved_artifacts.get(current_topic.research_question, [])
    # updated_artifacts = existing_artifacts_for_topic + artifacts
    # saved_artifacts[current_topic.research_question] = updated_artifacts
    current_section_idx = context_variables.get("current_runbook_section") or 0
    existing_section_research_artifacts = context_variables.get("section_research_artifacts") or {}
    existing_section_research_artifacts[current_section_idx] = artifacts

    return AsyncResult(
      value="Artifacts retrieved and saved to the prompt",
      context_variables={
        "section_research_artifacts": existing_section_research_artifacts
      }
    )

  async def query_for_artifacts(context_variables: ContextVariables, queries: List[str]):
    """Query for artifacts that are related to the queries and return their summaries

    Arguments:
      queries: an array of strings in JSON format, i.e. `["query1", "query2", ...]`. Make sure it is a valid JSON array.
      If there is only one query, you should still enclose it in an array, i.e. `["query1"]`.
    """
    try:
      if isinstance(queries, str):
        queries = json.loads(queries)

      return await async_query_for_artifacts(queries)
    except Exception as e:
      return AsyncResult(value=f"Error querying for artifacts: {e}")

  async def retrieve_artifacts(context_variables: ContextVariables, artifact_ids: List[str]) -> AsyncResult:
    """Retrieve the contents of the related artifacts.

    Arguments:
      artifact_ids: an array of related artifact IDs in JSON format,
        i.e. `["artifact_id1", "artifact_id2", ...]`. Make sure it is formatted as a valid JSON array of strings.
    """
    try:
      return await async_retrieve_artifacts(context_variables, artifact_ids)
    except Exception as e:
      return AsyncResult(value=f"Error retrieving artifacts: {e}")

  async def submit_writing_for_section(context_variables: Dict[str, Any], section_content: str) -> AsyncResult:
    """Write the section content. If there are more sections to write, move on to the next section.
    Otherwise, save the runbook and hand off the next steps back to the research coordinator agent.

    Arguments:
      section_content: the content of the section to write in Markdown format.
    """
    try:
      current_section_idx = context_variables.get("current_runbook_section", 0)
      all_sections = context_variables.get("runbook_sections", []).copy()
      current_section = all_sections[current_section_idx]
      current_section.content = section_content

      if current_section_idx + 1 >= len(all_sections):
        if context_variables.get("debug", False):
          print("Session writing complete", context_variables.get("runbook_sections", {}))
        # Save all sections to a markdown file
        with open("runbook.md", "w") as f:
          f.write("\n\n".join(section.content for section in all_sections))

        from .research_coordinator_agent import create_research_coordinator_agent
        return AsyncResult(
          value="All sections written",
          context_variables={
            "runbook_sections": all_sections,
            "current_runbook_section": None,
          },
          agent=create_research_coordinator_agent(settings)
        )

      return AsyncResult(
        value=f"Section {current_section_idx + 1} written",
        context_variables={
          "runbook_sections": all_sections,
          "current_runbook_section": current_section_idx + 1
        },
        agent=create_runbook_section_writing_agent(settings)
      )
    except Exception as e:
      return AsyncResult(value=f"Error submitting writing for section: {e}")

  return AsyncAgent(
    name=AGENT_RUNBOOK_SECTION_WRITING,
    instructions=instructions,
    functions=[query_for_artifacts, retrieve_artifacts, submit_writing_for_section],
    tool_choice="required",
    model=settings.agent_llm_model
  )
