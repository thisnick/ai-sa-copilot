import asyncio
import json
import os
from typing import Any, Dict, List, Literal

from swarm import AsyncAgent
from swarm.types import AsyncResult

from api.config import Settings

from .agent_map import AGENT_TOPIC_RESEARCH
from .types import ArtifactSearchResult, ContextVariables
from .tools import async_get_artifacts, async_get_knowledge_topics, async_query_for_artifacts, format_knowledge_topics, format_research_topic

def create_topic_research_agent(settings: Settings) -> AsyncAgent:
  async def instructions(context_variables: ContextVariables):
    current_topic_idx = context_variables.get("current_research_topic") or 0
    topics = context_variables.get("research_topics") or []
    if len(topics) >= current_topic_idx:
      current_topic = topics[current_topic_idx]
      formatted_topic = format_research_topic(current_topic)
    else:
      formatted_topic = "No research topics available"

    domain_id = context_variables.get("domain_id")
    formatted_knowledge_topics = format_knowledge_topics(await async_get_knowledge_topics(domain_id)) if domain_id else ""


    return f"""You are a research agent investigating a research topic. Your goal
    is to find the documents that are relevant to the user's question filter them to
    the most relevant ones.

    Here is your workflow:
    1. Based on the research topic generate 3-5 research question that have some
       overlap with the knowledge topics. These questions, when answered, will
       help you answer the research topic.
    2. Call `query_for_artifacts` with the research question to get
       a list of artifacts that are related to the research question. You should
       phrase the research queries in different ways to increase the chance of
       articles that are related to the research question are retrieved. You should
       send all the queries in one call instead of issuing one call per query.
       For example, if the question is about "how to do XYZ" and related concepts
       are ABC, you can also phrase the query as "introduction to XYZ", "How to do
       ABC with XYZ", "XYZ example", etc.
    3. Analyze the artifacts and determine whether they are relevant to the
       research question. If they are, call `save_artifact` so that it can be
       used later to generate the report. Only save the most relevant artifacts,
       and limit the number of artifacts saved to no more than 5.
    4. If there are remaining topics to research, call `finish_research` to
       move on to the next topic or to start writing the report.


    Never answer the user directly. Instead, you should do the research and use `finish_research`
    when you are done researching. The downstream agents will handle answering the user question.

    Research topic:
    {formatted_topic}

    Knowledge topics:
    {formatted_knowledge_topics}

    Remaining topics to research:
    {len(topics) - current_topic_idx - 1}

    """


  async def query_for_artifacts(queries: List[str]) -> Dict[Literal["artifacts"], List[ArtifactSearchResult]] | str:    # Create a new event loop for this sync function
    """Query for artifacts that are related to the query and return their summaries

    Arguments:
      queries: an array of strings in JSON format, i.e. `["query1", "query2", ...]`. Make sure it is a valid JSON array.
    """
    try:
      if isinstance(queries, str):
        queries = json.loads(queries)
      return await async_query_for_artifacts(queries)
    except Exception as e:
      return f"Error querying for artifacts: {e}"


  async def save_artifacts(context_variables: ContextVariables, artifact_ids: List[str]) -> AsyncResult:
    """Saves the *relevant* artifacts to the research context. Limit the number of artifacts saved to no more than 5.

    Arguments:
      artifact_ids: an array of artifact IDs in JSON format, i.e. `["artifact_id1", "artifact_id2", ...]`. Make sure it is a valid JSON array.
    """
    try:
      if isinstance(artifact_ids, str):
        artifact_ids = json.loads(artifact_ids)

      artifacts = await async_get_artifacts(artifact_ids, with_links=True)

      return AsyncResult(
        value="Artifacts saved successfully",
        context_variables={
          "saved_artifacts": {
            **(context_variables.get("saved_artifacts") or {}),
            (context_variables.get("research_topics") or [])[context_variables.get("current_research_topic") or 0].research_question: artifacts
          }
        }
      )
    except Exception as e:
      return AsyncResult(value=f"Error saving artifacts: {e}")

  async def finish_research(context_variables: Dict[str, Any]) -> AsyncResult:
    """Finish the research of this topic. If there are more topics to research,
    move on to the next topic. Otherwise, hand off the research to the
    runbook planning agent.
    """
    try:
      current = context_variables.get("current_research_topic", 0)
      topics = context_variables.get("research_topics", [])

      if current + 1 >= len(topics):
        if context_variables.get("debug", False):
          print("saved_artifacts", context_variables.get("saved_artifacts", {}))

        from .runbook_planning_agent import create_runbook_planning_agent
        return AsyncResult(
          value="Research complete",
          context_variables={
            "current_expansion_topic": 0
          },
          agent=create_runbook_planning_agent(settings)
        )


      return AsyncResult(
        value="Moving to next topic",
        context_variables={"current_research_topic": current + 1},
        agent=create_topic_research_agent(settings)
      )
    except Exception as e:
      return AsyncResult(value=f"Error finishing research: {e}")

  return AsyncAgent(
    name=AGENT_TOPIC_RESEARCH,
    instructions=instructions,
    functions=[query_for_artifacts, save_artifacts, finish_research],
    tool_choice="required",
    model=settings.agent_llm_model
  )
