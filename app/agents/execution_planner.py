class ExecutionPlanner:

    def plan(self, intent: dict) -> list[str]:
        tools = intent.get("required_tools", [])

        # Geocoding tools must always go first
        geocode_tools = [
            "geocode_address",
            "geocode_street_name",
            "reverse_geocode",
        ]

        if intent.get("requires_geocoding", False):
            geo_tool_list = [t for t in tools if t in geocode_tools]
            other_tool_list = [t for t in tools if t not in geocode_tools]

            return geo_tool_list + other_tool_list

        return tools
