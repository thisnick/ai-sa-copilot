import asyncio
import json
import os
from typing import Any, Dict, List, Literal
import logging

from swarm import AsyncAgent
from swarm.types import AsyncResult

from lib.config import Settings

from .agent_map import AGENT_QUESTION_ANSWER
from .types import ArtifactSearchResult, ContextVariables, ResearchTopic
from .tools import async_get_artifacts, async_get_knowledge_topics, async_query_for_artifacts, format_artifacts, format_knowledge_topics

def create_question_answer_agent(settings: Settings) -> AsyncAgent:
  async def instructions(context_variables: ContextVariables):
    question = context_variables.get("question", "")
    domain_id = context_variables.get("domain_id")
    current_question = context_variables.get("current_question")
    if current_question:
      saved_artifacts = (context_variables.get("saved_artifacts") or {}).get(current_question, [])
    else:
      saved_artifacts = []

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
       the question. Save the most relevant ones (up to 5) using `save_artifacts`,
       which will update the "Currently researched artifacts for this question" section.
    4. Answer the user based on the results of the "Currently researched
       artifacts for this question".
    5. After you have answered the question, if the user follows up with tasks you
       are uneable to do, including updating the runbook or researching for the runbook, call
       `hand_off_to_research_coordinator` to to handle the task accordingly.

    Current question to answer:
    {question or "None"}

    Currently researched artifacts for this question:
    {format_artifacts(saved_artifacts) or "Not yet researched or no relevant artifacts found"}
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

  async def save_artifacts(context_variables: ContextVariables, question: str, artifact_content_ids: List[str]) -> AsyncResult:
    """Saves the *relevant* artifacts to the research context. Limit the number of artifacts saved to no more than 5.

    Arguments:
      question: the question to answer
      artifact_content_ids: an array of artifact content IDs in JSON format, i.e. `["artifact_content_id1", "artifact_content_id2", ...]`. Make sure it is a valid JSON array.
    """
    try:
      if isinstance(artifact_content_ids, str):
        artifact_content_ids = json.loads(artifact_content_ids)


      artifacts = await async_get_artifacts(artifact_content_ids)
      current_saved_artifacts = (context_variables.get("saved_artifacts") or {}).copy()

      current_saved_artifacts[question] = artifacts

      return AsyncResult(
        value=f"{len(artifacts)} artifacts saved successfully. They are now available in the 'Currently researched artifacts for this question' section.",
        context_variables={
          "saved_artifacts": current_saved_artifacts,
          "current_question": question
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
    tool_choice="auto",
    model=settings.agent_llm_model
  )
