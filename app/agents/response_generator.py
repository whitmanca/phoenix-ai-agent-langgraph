import json

from langchain_core.messages import HumanMessage, SystemMessage


class ResponseGenerator:
    def __init__(self, llm):
        self.llm = llm

    def _to_json_safe(self, value):
        """Convert values to JSON-serializable form."""
        if isinstance(value, (str, int, float)):
            return value
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, dict):
            return {k: self._to_json_safe(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._to_json_safe(v) for v in value]
        if hasattr(value, "to_dict"):
            return {
                "record_count": len(value),
                "columns": list(value.columns),
            }
        return str(value)

    def _summarize_results(self, tool_results: dict) -> dict:
        return {
            tool: self._to_json_safe(result) for tool, result in tool_results.items()
        }

    def generate(self, user_query: str, needs_tools: bool, tool_results: dict) -> str:
        if not needs_tools:
            system_prompt = "You are a helpful assistant. Answer the user's question directly using your knowledge."
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_query),
            ]
        else:
            summarized_results = self._summarize_results(tool_results)

            system_prompt = "You are a helpful assistant providing information based on location services data."
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(
                    content=(
                        f"User Query: {user_query}\n\n"
                        f"Tool Results (summarized): {json.dumps(summarized_results, indent=2)}"
                        "Provide a comprehensive, helpful response based on the data retrieved. "
                        "Be specific with numbers and details, but keep the overall length concise."
                        "Do not describe the methodology or tools used to generate the data."
                    )
                ),
            ]

        resp = self.llm.invoke(messages)
        # Groq returns an object with .content — but be defensive:
        return getattr(resp, "content", str(resp))
