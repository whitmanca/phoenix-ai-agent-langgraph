from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    messages: List[BaseMessage]
    user_query: str
    intent_analysis: Optional[Dict[str, Any]]
    required_tools: List[str]
    tool_results: Dict[str, Any]
    coordinates: Optional[Dict[str, float]]
    zip_code: Optional[str]
    final_response: Optional[str]
    error: Optional[str]
