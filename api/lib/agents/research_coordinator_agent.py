from pydantic import TypeAdapter
from typing import List
import logging

from swarm import AsyncAgent
from swarm.types import AsyncResult

from lib.config import Settings
from .types import ContextVariables, ResearchTopic
from .tools import async_get_knowledge_topics, format_knowledge_topics, format_written_sections
from .agent_map import AGENT_RESEARCH_COORDINATOR


def create_research_coordinator_agent(settings: Settings) -> AsyncAgent:
  async def instructions(context_variables: ContextVariables):
    domain_id = context_variables.get("domain_id")
    formatted_topics = format_knowledge_topics(await async_get_knowledge_topics(domain_id)) if domain_id else ""
    return f"""You are a research coordinator agent. You are helping a research run books for solutions.
    Here is your workflow:
    1. If the user's request is vague or too broad, before continuing to the next step, ask the user to explain the goal they want to achieve. You
       should prompt user by asking them whether their requirements overlap with specific topics or key concepts from the knowledge topics.
       You can skip this step if the user's requirement is very comprehensive.
    2. Once you have gathered requirements, add their them to the context by calling "save_requirements" function.
    3. Once the user indicates there are no more requirements, or you have identified all the key requirements, plan your
       research topics and kick off the research by calling "research_runbook_topics" function, which also takes in a list of research topics.
       This will hand off the research process to the research agent, which will then hand off the results to other agents to write the runbook.
       Do not kick off the research without giving the user a chance to provide additional requirements.

    After initial runbook is written:
    * If the user asks you to rewrite the run book given feedback or asks you change the runbook structure,
      hand off the planning task to the update_runbook_outline function.
    * If the user asks you to rewrite a just one section, hand off the writing task to the
      update_runbook_section_copy function.
    * If the user asks you to write a section you have not researched yet, then you should save that
      new requirement by calling `save_requirements` function and then call `research_runbook_topics` to
      start researching the new topic.

    Remember:
    - Do not make up answers. Your job is to help formulating the research topics and handing them over to the research agent. The research agent will hand off the results
      which will later be able to answer the user's question.
    - Do not give answers to the user without doing the research. Use kick_off_research to start the research, which will end with a writing
      agent writing the runbook.
    - Here is when to call each functions:
      * save_requirements: When the user provides new requirements
      * research_runbook_topics: When the user is asking to write a new runbook from scratch or to update the runbook. You will kick off the runbook writing
        by researching the user's questions and requirements.
      * update_runbook_outline_without_research: When the user wants to update the runbook outline without conducting research.
      * update_runbook_section_content_without_research: When the user wants to update the runbook section content without conducting research.
      * answer_question_without_updating_runbook: When the user wants to answer a question without the need to update the runbook.
    Knowledge topics:
    {formatted_topics}

    Existing requirements:
    {"\n".join(f"- {req}" for req in context_variables.get("user_requirements") or []) or "None"}

    Written runbook so far:
    {format_written_sections(context_variables.get("runbook_sections") or [])}

    Unwritten runbook sections:
    {sum(1 for section in context_variables.get("runbook_sections") or [] if not section.content)}

    Researched topics:
    {"\n".join([f"- {topic}" for topic in context_variables.get("saved_artifacts") or {}.keys()]) or "None"}
    """

  async def save_requirements(context_variables: ContextVariables, requirements: List[str] | str) -> AsyncResult:
    """Saves the user requirements to the context so it can be used by research agent

    Arguments:
      requirements: List[str] | str - The user requirements to add (can be either a string or list of strings)
    """
    try:
      # Convert string input to list if necessary
      req_list = [requirements] if isinstance(requirements, str) else requirements

      return AsyncResult(
        value="Requirements added successfully",
        context_variables={
          "user_requirements": context_variables.get("user_requirements") or [] + req_list
        }
      )
    except Exception as e:
      logging.error(f"Error in save_requirements: {str(e)}")
      return AsyncResult(value=f"Error saving requirements: {e}")

  async def research_runbook_topics(context_variables: ContextVariables, topics: List[ResearchTopic]) -> AsyncResult:
    """This is the entry point for the runbook writing process. You will kick off the process by researching
    the user's questions and requirements. The research agent will thoroughly research your given topic and
    start writing the runbook. Call this method if the user is interested in getting a step-by-step result on how
    to perform a task.

    Please do not include more than 3 topics. You can ask the user whether to add them after the initial runbook is written.

    Arguments:
      topics: [
        {
          "research_question": "The question to research",
          "related_key_concepts": "The key concepts related to the research question",
          "related_user_requirements": "The user requirements related to the research question"
        }
      ]
    """

    if not context_variables.get("user_requirements"):
      logging.warning("Attempted to kickoff research without user requirements")
      return AsyncResult(
        value="Error: No user requirements to conduct research. Please add user requirements first."
      )

    try:
      topic_list_adapter = TypeAdapter(List[ResearchTopic])
      if isinstance(topics, str):
        # Create a type adapter for List[ResearchTopic]
        # Parse the JSON string into a list of ResearchTopic objects
        topics = topic_list_adapter.validate_json(topics)
      else:
        topics = topic_list_adapter.validate_python(topics)


      if context_variables.get("debug", False):
        print("topics", topics)

      from .topic_research_agent import create_topic_research_agent

      research_agent = create_topic_research_agent(settings)
      return AsyncResult(
        value="Research kicked off",
        agent=research_agent,
        context_variables={
          "research_topics": topics,
          "current_research_topic": 0
        }
      )
    except Exception as e:
      logging.error(f"Error in research_runbook_topics: {str(e)}")
      return AsyncResult(value=f"Error kicking off research: {e}")

  async def update_runbook_outline_without_research(context_variables: ContextVariables) -> AsyncResult:
    """Hand of the task to update the runbook outline without conducting research. This is useful when the user wants to change the runbook structure or add new sections.
    without the need to research the topics again.
    """
    from .runbook_planning_agent import create_runbook_planning_agent
    return AsyncResult(
      agent=create_runbook_planning_agent(settings),
    )

  async def update_runbook_section_content_without_research(context_variables: ContextVariables, section_index: int) -> AsyncResult:
    """Hand off the task to update the runbook section content without conducting research. This is useful when the user does not want to change the runbook structure.
    and only wants to update the copy of the content without changing its outline or researching new topics.
    """
    from .runbook_section_writing_agent import create_runbook_section_writing_agent
    return AsyncResult(
      agent=create_runbook_section_writing_agent(settings),
      context_variables={
        "current_section_idx": section_index
      }
    )

  async def answer_question_without_updating_runbook(context_variables: ContextVariables) -> AsyncResult:
    """Hand off the task to answer the user's question without updating the runbook. This is useful when the user wants to answer a question
    without changing the runbook structure or researching new topics.
    """
    from .question_answer_agent import create_question_answer_agent
    return AsyncResult(
      agent=create_question_answer_agent(settings),
    )

  return AsyncAgent(
    name=AGENT_RESEARCH_COORDINATOR,
    instructions=instructions,
    functions=[
      save_requirements,
      research_runbook_topics,
      update_runbook_outline_without_research,
      update_runbook_section_content_without_research,
      answer_question_without_updating_runbook,
    ],
    model=settings.agent_llm_model
  )
