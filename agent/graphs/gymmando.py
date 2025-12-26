"""
Graph Orchestrator: Defines the agent workflow and routing logic.
"""

from langgraph.graph import END, StateGraph

from agents.parsing_agent import ParsingAgent
from agents.workout_agent import WorkoutAgent
from graphs.types import GymmandoState


class GymmandoGraph:
    """Main graph orchestrator for GYMMANDO agent system."""

    def __init__(self, user_id: str = "default_user"):
        """Initialize the graph with user_id."""
        self.user_id = user_id
        self.parsing_agent = ParsingAgent()
        self.workout_agent = WorkoutAgent(user_id=user_id)
        self.graph = None
        self._build_graph()

    def _should_route_to_agent(self, state: GymmandoState) -> str:
        """Route based on intent type or pending workout confirmation."""
        # Check if there's a pending workout confirmation
        workout_data = state.get("workout_data")
        if workout_data and workout_data.get("status") == "pending_confirmation":
            # Route to workout agent to handle confirmation
            return "workout"
        
        intent = state.get("intent")
        if not intent:
            return "workout"  # Default route
        
        intent_type = intent.get("type")

        if intent_type in ["log_workout", "view_workouts", "search_routines"]:
            return "workout"
        else:
            # For now, route everything else to workout (or could add general_query handler)
            return "workout"

    def _build_graph(self):
        """Build and compile the LangGraph workflow."""
        # Create the graph
        workflow = StateGraph(GymmandoState)

        # Add nodes
        workflow.add_node("parse", self.parsing_agent.execute)
        workflow.add_node("workout", self.workout_agent.execute)

        # Set entry point
        workflow.set_entry_point("parse")

        # Add conditional routing from parsing
        workflow.add_conditional_edges(
            "parse",
            self._should_route_to_agent,
            {"workout": "workout"},
        )

        # Workout agent goes directly to END
        workflow.add_edge("workout", END)

        # Compile the graph
        self.graph = workflow.compile()
        print("✅ Agent graph compiled successfully")

    def build(self):
        """Return the compiled graph."""
        return self.graph


def build_graph(user_id: str = "default_user"):
    """Build and compile the LangGraph workflow."""
    graph_instance = GymmandoGraph(user_id=user_id)
    return graph_instance.build()

