import os
from langchain_groq import ChatGroq
from langchain.agents import create_agent

from tools.weather import get_weather
from tools.notion_notes import get_notes, add_note
from tools.notion_calender import get_calendar_events, add_calendar_event
from utils.logger import get_logger


logger = get_logger(__name__)


def get_llm():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.error("Groq api key not set")
        raise ValueError("Groq api key not set")
    
    return ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0.5,
        api_key=api_key
    )


def create_react_agent_custom():
    logger.info("Initializing Agent")
    llm = get_llm()

    tools = [get_weather, get_notes, add_note, get_calendar_events, add_calendar_event]


    try:
        agent = create_agent(model=llm, tools=tools)
        logger.info("Agent Intialized")
        return agent
    
    except TypeError as e:
        logger.error(f"Failed to create agent: {e}")
        raise e