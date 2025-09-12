import logging

from app.agents.phoenix_agent import PhoenixAgent
from app.schemas.chat import ChatRequest
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()

agent = PhoenixAgent()


@router.post("/chat")
def execute_chat(request: ChatRequest):
    return agent.run(request.message)
