"""
Memory Agent: Manages user context, history, and preferences.
"""

from database.supabase_client import supabase
from graphs.types import GymmandoState


class MemoryAgent:
    """Manages user context and history."""

    async def execute(self, state: GymmandoState) -> GymmandoState:
        """Retrieve relevant user context and history."""
        print(f"🧠 Memory Agent: Loading user context")

        # TODO: Query user preferences, PRs, injury history from Supabase
        # TODO: Retrieve recent workout/nutrition history
        # TODO: Load personality preferences

        state["memory_context"] = {
            "user_id": state["user_id"],
            "personality_preference": state["personality_mode"],
            "total_workouts": 0,  # Would query from DB
            "last_workout_date": None,
            "injuries": [],
            "goals": [],
            "prs": {},  # Personal records
        }

        return state

