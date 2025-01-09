from swarm.types import AsyncAgent
from lib.agents.agent_map import (
  AGENT_NAIVE_RAG_AGENT,
  AGENT_RESEARCH_COORDINATOR,
  AGENT_TOPIC_RESEARCH,
  AGENT_RUNBOOK_PLANNING,
  AGENT_RUNBOOK_SECTION_WRITING,
  AGENT_QUESTION_ANSWER
)
from lib.config import Settings

def create_agent(settings: Settings, agent_name: str) -> AsyncAgent:
  if agent_name == AGENT_RESEARCH_COORDINATOR:
    from .research_coordinator_agent import create_research_coordinator_agent
    return create_research_coordinator_agent(settings)
  elif agent_name == AGENT_TOPIC_RESEARCH:
    from .topic_research_agent import create_topic_research_agent
    return create_topic_research_agent(settings)
  elif agent_name == AGENT_RUNBOOK_PLANNING:
    from .runbook_planning_agent import create_runbook_planning_agent
    return create_runbook_planning_agent(settings)
  elif agent_name == AGENT_RUNBOOK_SECTION_WRITING:
    from .runbook_section_writing_agent import create_runbook_section_writing_agent
    return create_runbook_section_writing_agent(settings)
  elif agent_name == AGENT_NAIVE_RAG_AGENT:
    from lib.agents.naive_rag_agent import create_naive_rag_agent
    return create_naive_rag_agent(settings)
  elif agent_name == AGENT_QUESTION_ANSWER:
    from .question_answer_agent import create_question_answer_agent
    return create_question_answer_agent(settings)
  else:
    raise ValueError(f"Agent {agent_name} not found")
