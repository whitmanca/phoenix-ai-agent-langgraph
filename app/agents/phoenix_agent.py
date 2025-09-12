import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph

from app.agents.execution_planner import ExecutionPlanner
from app.agents.intent_analyzer import IntentAnalyzer
from app.agents.response_generator import ResponseGenerator
from app.agents.state import AgentState
from app.agents.tool_executor import ToolExecutor
from app.core.config import Settings
from app.tools.registry import ALL_TOOLS

load_dotenv()


class PhoenixAgent:
    def __init__(self, model_name: str = None):
        # Initialize LLM
        self.llm = ChatGroq(
            model=model_name or Settings.GROQ_MODEL,
            temperature=Settings.GROQ_TEMPERATURE,
            api_key=os.getenv("GROQ_API_KEY"),
            verbose=True,
        )

        # Tool registry
        self.tools = ALL_TOOLS

        # Core components
        self.intent_analyzer = IntentAnalyzer(self.llm)
        self.planner = ExecutionPlanner()
        self.executor = ToolExecutor(self.tools)
        self.responder = ResponseGenerator(self.llm)

        # Workflow graph
        self.graph = self._build_graph()

    # Graph Setup
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)

        workflow.add_node("analyze_intent", self._node_analyze_intent)
        workflow.add_node("plan_execution", self._node_plan_execution)
        workflow.add_node("execute_tools", self._node_execute_tools)
        workflow.add_node("generate_response", self._node_generate_response)
        workflow.add_node("handle_error", self._node_handle_error)

        # Entry + flow
        workflow.set_entry_point("analyze_intent")
        workflow.add_conditional_edges(
            "analyze_intent",
            self._should_use_tools,
            {
                "use_tools": "plan_execution",
                "direct_response": "generate_response",
                "error": "handle_error",
            },
        )
        workflow.add_edge("plan_execution", "execute_tools")
        workflow.add_edge("execute_tools", "generate_response")
        workflow.add_edge("generate_response", END)
        workflow.add_edge("handle_error", END)

        return workflow.compile()

    # Workflow Nodes
    def _should_use_tools(self, state: AgentState) -> str:
        """Branch depending on intent and errors."""
        if state.get("error"):
            return "error"

        if state.get("final_response"):
            return "direct_response"

        intent = state.get("intent_analysis", {}) or {}
        if intent.get("needs_tools", False):
            return "use_tools"
        return "direct_response"

    def _node_analyze_intent(self, state: AgentState) -> AgentState:
        try:
            intent = self.intent_analyzer.analyze(state["user_query"])

            if intent.get("extracted_info", {}).get("error"):
                return {
                    **state,
                    "intent_analysis": intent,
                    "final_response": f"Sorry, I can only answer questions related to Phoenix, AZ.",
                }

            return {**state, "intent_analysis": intent}

        except Exception as e:
            return {**state, "error": f"Intent analysis failed: {e}"}

    def _node_plan_execution(self, state: AgentState) -> AgentState:
        try:
            required_tools = self.planner.plan(state.get("intent_analysis", {}))
            return {**state, "required_tools": required_tools}
        except Exception as e:
            return {**state, "error": f"Planning failed: {e}"}

    def _node_execute_tools(self, state: AgentState) -> AgentState:
        """Execute the required tools in order."""
        try:
            results = self.executor.execute(
                state["required_tools"], state["intent_analysis"], state
            )
            return {**state, "tool_results": results}
        except Exception as e:
            return {**state, "error": f"Tool execution failed: {str(e)}"}

    def _node_generate_response(self, state: AgentState) -> AgentState:
        try:
            if state.get("final_response"):
                return state

            intent = state.get("intent_analysis", {}) or {}
            tool_results = state.get("tool_results", {}) or {}

            # Text response
            response = self.responder.generate(
                state["user_query"],
                intent.get("needs_tools", False),
                tool_results,
            )

            return {
                **state,
                "final_response": response,
            }

        except Exception as e:
            return {**state, "error": f"Response generation failed: {e}"}

    def _node_handle_error(self, state: AgentState) -> AgentState:
        error_msg = (
            f"I encountered an error while processing your request: "
            f"{state.get('error', 'Unknown error')}"
        )
        return {**state, "final_response": error_msg}

    def run(self, user_query: str) -> dict:
        """Run agent on a user query."""
        initial_state = AgentState(
            messages=[HumanMessage(content=user_query)],
            user_query=user_query,
            intent_analysis=None,
            required_tools=[],
            tool_results={},
            coordinates=None,
            final_response=None,
            error=None,
        )

        final_state = self.graph.invoke(initial_state)

        return {
            "final_response": final_state.get(
                "final_response", "No response generated."
            ),
        }
