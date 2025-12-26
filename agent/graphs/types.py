"""
State definition for the agent graph.
"""

from typing import Optional, TypedDict


class GymmandoState(TypedDict):
    """State that flows through the agent graph."""

    transcript: str  # User's speech input
    intent: Optional[dict]  # Parsed intent from user
    workout_data: Optional[dict]  # Workout-related data
    response: str  # Final response to user
    personality_mode: str  # bro, coach, or commander
    user_id: str  # User identifier

