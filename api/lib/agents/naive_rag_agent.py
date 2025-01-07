from typing import List
from swarm import AsyncAgent
from swarm.types import AsyncResult
from lib.agents.agent_map import AGENT_NAIVE_RAG_AGENT
from lib.agents.types import ContextVariables
from lib.config import Settings
from lib.agents.tools import async_query_for_artifacts


def create_naive_rag_agent(settings: Settings) -> AsyncAgent:
  async def instructions(context_variables: ContextVariables):
    return (
      "You are a helpful assistant who can retrieve artifacts "
      "using the retrieve_artifacts function. "
      "Gather relevant information from the domain based on the user's query, "
      "integrate it into your reasoning, and provide a comprehensive response."
    )

  async def retrieve_artifacts(context_variables: ContextVariables, query: str) -> AsyncResult:
    domain_id = context_variables.get("domain_id")
    assert domain_id is not None, "domain_id is required"
    artifacts = await async_query_for_artifacts(
      [query],
      domain_id,
      full_text_search=False,
    )
    existing_requirements = context_variables.get("user_requirements") or []
    if len(existing_requirements) == 0:
      existing_requirements.append(query)
    return AsyncResult(
      value="\n\n".join([
        f"## Title: {artifact['title']}\n\n### URL: {artifact['url']}\n\n### Content\n\n{artifact['summary']}"
        for artifact in artifacts["artifacts"]
      ]),
      context_variables={
        "user_requirements": existing_requirements,
      }
    )

  return AsyncAgent(
    name=AGENT_NAIVE_RAG_AGENT,
    instructions=instructions,
    functions=[retrieve_artifacts],
  )
