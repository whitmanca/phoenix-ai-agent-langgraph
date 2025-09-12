from typing import Callable, Dict

from langchain.tools import StructuredTool

from app.agents.state import AgentState


class ToolExecutor:
    def __init__(self, tools: dict, geocode_service=None):
        self.tools = tools
        self.geocode_service = geocode_service
        self.post_hooks: Dict[str, Callable] = {
            "geocode_address": self._handle_geocode_result,
            "geocode_street_name": self._handle_geocode_result,
            "reverse_geocode": self._handle_geocode_result,
        }

    def _handle_geocode_result(self, state: AgentState, result: dict) -> AgentState:
        """Store geocoded coordinates and ZIP code in the agent state."""
        if result:
            state["coordinates"] = {
                "lat": result.get("lat"),
                "lon": result.get("lon"),
            }
            state["zip_code"] = result.get("zip_code", "00000")

        return state

    def _build_tool_args(self, tool: StructuredTool, state: AgentState) -> dict:
        """Build input args from intent analysis and state."""
        extracted_info = state.get("intent_analysis", {}).get("extracted_info", {})
        schema = tool.args_schema
        valid_fields = schema.model_fields.keys()

        candidate_args = {}
        for field in valid_fields:
            if field in extracted_info:
                candidate_args[field] = extracted_info[field]
            elif field in state:
                candidate_args[field] = state[field]
            elif field in (state.get("coordinates") or {}):
                candidate_args[field] = state["coordinates"][field]

        try:
            return schema(**candidate_args).model_dump()
        except Exception as e:
            raise ValueError(f"Failed to build args for tool {tool.name}: {str(e)}")

    def _validate_complete_address(self, intent) -> str:
        """
        Forces the tool choice for incomplete addresses if missing a city/state.
        Uses a very simple and crude heuristic of checking for a comma
        """
        extracted = intent.get("extracted_info", {})
        address = extracted.get("address")
        if address and "," not in address:
            return "geocode_street_name"
        return "geocode_address"

    def execute(self, tools_order: list[str], intent: dict, state: dict) -> dict:
        results = state.get("tool_results", {})

        for tool_name in tools_order:
            tool = self.tools.get(tool_name)
            if not tool:
                raise ValueError(f"Unknown tool requested: {tool_name}")

            if tool_name == "geocode_address":
                tool_name = self._validate_complete_address(intent)

            args = self._build_tool_args(tool, state)
            result = tool.invoke(args)
            results[tool_name] = result

            if tool_name in self.post_hooks:
                state = self.post_hooks[tool_name](state, result)

        return results
