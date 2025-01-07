from swarm.types import AsyncAgent
from lib.agents.agent_map import (
  AGENT_NAIVE_RAG_AGENT,
  AGENT_RESEARCH_COORDINATOR,
  AGENT_TOPIC_RESEARCH,
  AGENT_RUNBOOK_PLANNING,
  AGENT_RUNBOOK_SECTION_WRITING
)
from lib.agents.naive_rag_agent import create_naive_rag_agent
from .research_coordinator_agent import create_research_coordinator_agent
from .topic_research_agent import create_topic_research_agent
from .runbook_planning_agent import create_runbook_planning_agent
from .runbook_section_writing_agent import create_runbook_section_writing_agent
from lib.config import Settings

def create_agent(settings: Settings, agent_name: str) -> AsyncAgent:
  if agent_name == AGENT_RESEARCH_COORDINATOR:
    return create_research_coordinator_agent(settings)
  elif agent_name == AGENT_TOPIC_RESEARCH:
    return create_topic_research_agent(settings)
  elif agent_name == AGENT_RUNBOOK_PLANNING:
    return create_runbook_planning_agent(settings)
  elif agent_name == AGENT_RUNBOOK_SECTION_WRITING:
    return create_runbook_section_writing_agent(settings)
  elif agent_name == AGENT_NAIVE_RAG_AGENT:
    return create_naive_rag_agent(settings)
  else:
    raise ValueError(f"Agent {agent_name} not found")
