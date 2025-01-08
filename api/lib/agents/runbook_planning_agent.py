import json
from typing import Any, Dict, List, Optional
from pydantic import TypeAdapter
from pydantic.json import pydantic_encoder
from swarm import AsyncAgent
from swarm.types import AsyncResult
import logging

from lib.config import Settings

from .agent_map import AGENT_RUNBOOK_PLANNING
from .types import ContextVariables, RunbookSection, RunbookSectionOutline
from .tools import format_topic_artifacts, format_runbook_section_outlines

def create_runbook_planning_agent(settings: Settings) -> AsyncAgent:

  async def instructions(context_variables: ContextVariables):
    saved_artifacts = context_variables.get("saved_artifacts", {})
    user_requirements = context_variables.get("user_requirements", "")
    runbook_sections = context_variables.get("runbook_sections", [])

    prompt = f"""You are a runbook planning agent. Your goal is to analyze the all the documents
    retrieved from the research and create a well-structured runbook outline
    based on user requirements.

    Here is your workflow:
    1. Review the user requirements and saved research materials
    2. Based on the research, if there is no existing runbook outline, call `create_runbook_outline`
       to propose a high-level run book outline and ask user for feedback.
    3. In each section, specify:
       - Section Title
       - Section Outline, which includes:
         - Main outcome this section needs to achieve
         - High level steps that this section contains. If the main sections from the articles
           relevant to the section, your high level steps should come from the main sections.
       - Related Artifacts: Which artifacts (IDs) to use to write this section (required)
         If you are presenting the artifacts to the user and not as a part of a tool call,
         format each artifact as: [Artifact title (Artifact ID)](Artifact URL)
    4. If there is already an existing runbook outline, use one or more of the following to make changes to
       the existing runbook outline:
       - Call `create_runbook_outline` to rewrite the entire runbook outline
       - Call `insert_runbook_section` to add a new section to the runbook outline at a specific index
       - Call `update_runbook_section` to update an existing section in the runbook outline at a specific index
       - Call `delete_runbook_section` to remove a section from the runbook outline at a specific index
    5. Once the user approves the outline, call `start_writing_runbook` to fill the updated runbook sections.
    6. If the user is asking you to do something that you are unable to do, such as
       researching for a topic, you should hand off the control back to the research
       coordinator agent by calling `handoff_to_research_coordinator_agent`, who will
       decide what to do next.

    Make sure to:
    1. Use the saved research materials to inform the structure
    2. Only pick up steps from the articles that are relevant to the user goals
    3. Since this is a run book, your structure should focus on the detailed steps
       needed to achieve the main outcome. No need to include introductions or conclusions.
       You may, however, include sections such as troubleshooting or alternatives.
    4. When calling `create_runbook_outline`, include all the sections in the runbook
       outline even if the user asks you to write only one section.

    User Requirements:
    {user_requirements}

    Saved Research Materials:
    {format_topic_artifacts(saved_artifacts or {}, treat_metadata_as_content=True)}

    Previously written runbook outline:
    {format_runbook_section_outlines(runbook_sections or []) or "None"}
    """
    return prompt

  async def start_writing_runbook(context_variables: ContextVariables):
    """Hand off the run book outline to the runbook section writing agent to start writing the runbook."""

    if len(context_variables.get("runbook_sections") or []) == 0:
      logging.warning("Attempted to start writing runbook without sections")
      return AsyncResult(
        value="No runbook sections to write. Please create a runbook outline first by calling `create_runbook_outline` first."
      )

    from .runbook_section_writing_agent import create_runbook_section_writing_agent

    return AsyncResult(
      agent=create_runbook_section_writing_agent(settings),
      context_variables={
        "current_runbook_section": get_next_unwritten_section_index(context_variables, 0)
      }
    )

  async def insert_runbook_section(context_variables: ContextVariables, section_outline: RunbookSectionOutline, index: int) -> AsyncResult:
    """Insert the section outline into the runbook sections array at the specified index."""
    runbook_sections = context_variables.get("runbook_sections") or []

    # Ensure the insertion index fits safely within the list (met or at the end).
    # You can decide what to do if the index is below 0 or above len(runbook_sections).
    if index < 0:
      index = 0
    if index > len(runbook_sections):
      index = len(runbook_sections)

    runbook_sections.insert(index, RunbookSection(**section_outline.model_dump()))

    return AsyncResult(
      value="Section outline inserted successfully",
      context_variables={
        "runbook_sections": runbook_sections,
      }
    )

  async def update_runbook_section(context_variables: ContextVariables, section_outline: RunbookSectionOutline, index: int) -> AsyncResult:
    """Update the section outline at the specified index."""
    runbook_sections = context_variables.get("runbook_sections") or []
    runbook_sections[index] = RunbookSection(**section_outline.model_dump())
    return AsyncResult(
      value="Section outline updated successfully",
      context_variables={
        "runbook_sections": runbook_sections,
      }
    )

  async def delete_runbook_section(context_variables: ContextVariables, index: int) -> AsyncResult:
    """Delete the section outline at the specified index."""
    runbook_sections = context_variables.get("runbook_sections") or []
    runbook_sections.pop(index)
    return AsyncResult(
      value="Section outline deleted successfully",
      context_variables={
        "runbook_sections": runbook_sections,
      }
    )

  async def create_runbook_outline(context_variables: ContextVariables, section_outlines: List[RunbookSectionOutline]) -> AsyncResult:
    """save the section outline you created and replace the existing one. If there is an existing outline,
    it will be replaced with the new one.

    Arguments:
    - section_outlines: an array of section outlines. E.g. [
      {
        "section_title": "Step 1: Set up Databricks IAM on AWS",
        "outline": "- Goals: Set up Databricks IAM on AWS\n- High level steps: 1. Create an IAM role for Databricks\n2. Attach the necessary policies to the role\n3. Create an IAM user in Databricks with the role",
        "related_artifacts": ["artifact_content_id1", "artifact_content_id2", ...]
      },
      ...
    ]
    """
    try:
      section_outline_list_of_dicts : List = []
      list_of_section_outline_adaptor = TypeAdapter(List[RunbookSection])
      if isinstance(section_outlines, list) and len(section_outlines) > 0 and isinstance(section_outlines[0], RunbookSectionOutline):
        section_outline_list_of_dicts = [section_outline.model_dump() for section_outline in section_outlines]
      else:
        raise ValueError(f"Invalid section outlines: {section_outlines}")

      if len(section_outlines) == 0:
        logging.warning("Attempted to create runbook outline with empty sections")
        return AsyncResult(
          value="No section outlines to create. Please include the outline in the argument section_outlines."
        )
      list_of_section_outlines = list_of_section_outline_adaptor.validate_python(section_outline_list_of_dicts)

      if context_variables.get("debug", False):
        logging.debug("List of section outlines: %s", list_of_section_outlines)

      return AsyncResult(
        value="Outline created successfully",
        context_variables={
          "runbook_sections": list_of_section_outlines,
        }
      )
    except Exception as e:
      logging.error(f"Error creating runbook outline: {str(e)}")
      return AsyncResult(value=f"Error creating runbook outline: {e}")

  def get_next_unwritten_section_index(context_variables: ContextVariables, start_index: int) -> Optional[int]:
    """Get the next unwritten section from the runbook sections array."""
    runbook_sections = context_variables.get("runbook_sections") or []
    for idx, section in enumerate(runbook_sections[start_index:]):
      if not section.content:
        return idx + start_index
    return None

  async def handoff_to_research_coordinator_agent(context_variables: ContextVariables):
    """Hand off the control back to the research coordinator agent, who can perform tasks
    such as researching for a topic."""
    logging.info("Handing off to research coordinator agent")
    from .research_coordinator_agent import create_research_coordinator_agent
    return AsyncResult(
      agent=create_research_coordinator_agent(settings),
    )

  return AsyncAgent(
    name=AGENT_RUNBOOK_PLANNING,
    instructions=instructions,
    functions=[
      create_runbook_outline,
      start_writing_runbook,
      handoff_to_research_coordinator_agent,
      insert_runbook_section,
      update_runbook_section,
      delete_runbook_section
    ],
    tool_choice="auto",
    model=settings.agent_llm_model
  )
