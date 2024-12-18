import json
from typing import List
from pydantic import TypeAdapter
from swarm import AsyncAgent
from swarm.types import AsyncResult

from api.config import Settings

from .agent_map import AGENT_RUNBOOK_PLANNING
from .types import ContextVariables, RunbookSection, RunbookSectionOutline
from .tools import format_topic_artifacts

def create_runbook_planning_agent(settings: Settings) -> AsyncAgent:

  async def instructions(context_variables: ContextVariables):
    saved_artifacts = context_variables.get("saved_artifacts", {})
    user_requirements = context_variables.get("user_requirements", "")

    prompt = f"""You are a runbook planning agent. Your goal is to analyze the all the documents
    retrieved from the research and create a well-structured runbook outline
    based on user requirements.

    Here is your workflow:
    1. Review the user requirements and saved research materials
    2. Call `create_runbook_outline` to generate a high-level outline of sections
    3. In each section, specify:
       - Section Title
       - Section Outline, which includes:
         - Main outcome this section needs to achieve
         - High level steps that this section contains
       - Related Artifacts: Which artifacts (IDs) to use to write this section (required)

    Make sure to:
    1. Use the saved research materials to inform the structure
    2. Only pick up steps from the articles that are relevant to the user goals
    3. Since this is a run book, your structure should focus on the detailed steps
       needed to achieve the main outcome. No need to include introductions or conclusions.
       You may, however, include sections such as troubleshooting or alternatives.

    User Requirements:
    {user_requirements}

    Saved Research Materials:
    {format_topic_artifacts(saved_artifacts or {})}
    """
    return prompt

  async def create_runbook_outline(context_variables: ContextVariables, section_outlines: List[RunbookSectionOutline]) -> AsyncResult:
    """Save the section outline you created.

    Arguments:
    - section_outlines: an array of section outlines. E.g. [
      {
        "section_title": "Step 1: Set up Databricks IAM on AWS",
        "outline": "- Goals: Set up Databricks IAM on AWS\n- High level steps: 1. Create an IAM role for Databricks\n2. Attach the necessary policies to the role\n3. Create an IAM user in Databricks with the role",
        "related_artifacts": ["artifact_id1", "artifact_id2", ...]
      },
      ...
    ]
    """

    list_of_section_outline_adaptor = TypeAdapter(List[RunbookSection])
    if isinstance(section_outlines, str):
      section_outlines = json.loads(section_outlines)

    list_of_section_outlines = list_of_section_outline_adaptor.validate_python(section_outlines)

    if context_variables.get("debug", False):
      print("List of section outlines: ", list_of_section_outlines)

    from .runbook_section_writing_agent import create_runbook_section_writing_agent

    return AsyncResult(
      value="Outline created successfully",
      agent=create_runbook_section_writing_agent(settings),
      context_variables={
        "runbook_sections": list_of_section_outlines,
        "current_runbook_section": 0
      }
    )

  return AsyncAgent(
    name=AGENT_RUNBOOK_PLANNING,
    instructions=instructions,
    functions=[
      create_runbook_outline,
    ],
    tool_choice="required",
    model=settings.agent_llm_model
  )
