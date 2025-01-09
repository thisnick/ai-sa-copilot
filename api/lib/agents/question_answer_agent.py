import asyncio
import json
import os
from typing import Any, Dict, List, Literal
import logging

from swarm import AsyncAgent
from swarm.types import AsyncResult

from lib.config import Settings

from .agent_map import AGENT_QUESTION_ANSWER
from .types import ArtifactSearchResult, ContextVariables
from .tools import async_get_artifacts, async_get_knowledge_topics, async_query_for_artifacts, format_knowledge_topics

def create_question_answer_agent(settings: Settings) -> AsyncAgent:
  async def instructions(context_variables: ContextVariables):
    question = context_variables.get("question", "")
    domain_id = context_variables.get("domain_id")
    formatted_knowledge_topics = format_knowledge_topics(await async_get_knowledge_topics(domain_id)) if domain_id else ""

    return f"""You are a question-answering agent. Your goal is to find relevant documents
    and provide a comprehensive answer to the user's question.

    Here is your workflow:
    1. Based on the user's question, generate 3-5 search queries that will help find
       relevant information. These queries should overlap with the knowledge topics
       and be phrased in different ways to increase the chance of finding relevant
       articles.
    2. Call `query_for_artifacts` with your search queries to get a list of potentially
       relevant artifacts. Send all queries in one call.
    3. Analyze the artifacts and determine which ones are most relevant to answering
       the question. Save the most relevant ones (up to 5) using `save_artifacts`.
    4. Provide the answer to the user based on the results of the "saved_artifacts".
    5. If the user asks you to perform any other tasks, including updating the runbook
       or researching for the runbook, call `hand_off_to_research_coordinator` to
       to handle the task accordingly.

    Current question to answer:
    {question}

    Knowledge topics:
    {formatted_knowledge_topics}
    """

  async def query_for_artifacts(
    context_variables: ContextVariables,
    queries: List[str],
  ) -> Dict[Literal["artifacts"], List[ArtifactSearchResult]] | str:
    try:
      assert isinstance(queries, list), "Queries must be a list"
      domain_id = context_variables.get("domain_id")
      assert domain_id is not None, "Domain ID is required"
      return await async_query_for_artifacts(queries, domain_id)
    except Exception as e:
      logging.error(f"Error in query_for_artifacts: {str(e)}")
      return f"Error querying for artifacts: {e}"

  async def save_artifacts(context_variables: ContextVariables, artifact_content_ids: List[str]) -> AsyncResult:
    try:
      if isinstance(artifact_content_ids, str):
        artifact_content_ids = json.loads(artifact_content_ids)

      artifacts = await async_get_artifacts(artifact_content_ids)
      return AsyncResult(
        value="Artifacts saved successfully.",
        context_variables={
          "saved_artifacts": artifacts
        }
      )
    except Exception as e:
      logging.error(f"Error in save_artifacts: {str(e)}")
      return AsyncResult(value=f"Error saving artifacts: {e}")

  async def hand_off_to_research_coordinator(context_variables: ContextVariables) -> AsyncResult:
    from .research_coordinator_agent import create_research_coordinator_agent
    return AsyncResult(
      agent=create_research_coordinator_agent(settings),
    )

  return AsyncAgent(
    name=AGENT_QUESTION_ANSWER,
    instructions=instructions,
    functions=[query_for_artifacts, save_artifacts, hand_off_to_research_coordinator],
    tool_choice="required",
    model=settings.agent_llm_model
  )
