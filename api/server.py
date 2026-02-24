from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from agent.bot import create_react_agent_custom
from utils.logger import get_logger
from tools.notion_calender import get_calendar_events, add_calendar_event
from tools.notion_notes import get_notes, add_note
from tools.weather import get_weather


logger = get_logger(__name__)

app = FastAPI(title="ReAct Agent API")


agent = None

@app.on_event("startup")
async def startup_event():
    global agent
    try:
        agent = create_react_agent_custom()
        logger.info("Agent init in API")
    except Exception as e:
        logger.error(f"Failed to Init agent :{e}")
        pass


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, Any]]] = None


@app.post("/chat")
async def chat(request: ChatRequest):
    global agent
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not Init")
    

    try:
        response = agent.invoke({"messages":[("user", request.message)]})

        if isinstance(response, dict) and "messages" in response:
            messages = response["messages"]
            if messages:
                last_msg = messages[-1]
                return {"response":last_msg.content}
            
    except Exception as e:
        logger.error("Error during chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status":"ok"}

app.mount("/",StaticFiles(directory="static",html=True), name='static')