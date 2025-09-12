import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.schemas.intent_analyzer import IntentAnalysis
from app.tools.registry import DATA_TOOLS


class IntentAnalyzer:
    def __init__(self, llm):
        self.llm = llm

    def analyze(self, query: str) -> dict:
        data_tool_descriptions = "\n".join(
            f"- {t.name}: {t.description}" for t in DATA_TOOLS.values()
        )

        system_prompt = f"""
You are an Intent Analyzer for a geospatial assistant.
Your job is to analyze user queries and decide which tools the assistant must call.
Not all queries will require the use of tools.
Your focus is specifically on the Pheonix, Arizona area. 
If no specific location (city, address, coordinates, zip code, etc) is specified, then assume it is referring to Phoenix, Arizona.
If a user request is not directly or indirectly related to Phoenix, Arizona, then response with a JSON object containing:
{{
    "error": "explanation of why you cannot process the query"
}}


Available tools:
**Data tools**
{data_tool_descriptions}

If the user provides:
- A full address including city and state → use geocode_address
- Only a street name/number without city/state → use geocode_street_name


Schema: IntentAnalysis with fields: 
- needs_tools (bool)
- intent_type (general|crime|flood|location|multi)
- required_tools (list[str])
- requires_geocoding (bool)
- extracted_info: {{address, zip_code, year, month, crime_type}}
- reasoning (string)

Examples:
- "What's the population of Phoenix?" -> needs_tools: false (general knowledge)
- "What's the population of Portland, Oregon" -> error: "This query is not related to Phoenix, Arizona"
- "Crime stats for zip 85015" -> needs_tools: true, tools: [crime_service_recent_activity]
- "Is 123 Main St in a flood zone?" -> needs_tools: true, tools: ["geocode_street_name", "flood_zone_details"]
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Analyze this query: {query}"),
        ]

        structured_llm = self.llm.with_structured_output(IntentAnalysis)
        response = structured_llm.invoke(messages)
        return response.dict()
