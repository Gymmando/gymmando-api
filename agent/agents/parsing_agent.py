"""
Parsing Agent: Converts natural language into structured intents.
"""

import json

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from graphs.types import GymmandoState


class ParsingAgent:
    """Parses natural language into structured intents."""

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    async def execute(self, state: GymmandoState) -> GymmandoState:
        """Parse user transcript into structured intent."""
        print(f"🧠 Parsing Agent: Processing '{state['transcript']}'")

        prompt = f"""
        You are a parsing agent for GYMMANDO, a gym and nutrition tracking assistant.
        Parse the user's message into a structured intent.
        
        User message: "{state['transcript']}"
        
        Return JSON with:
        - type: one of [log_workout, view_workouts, search_routines, log_meal, view_macros, general_query, change_personality]
        - data: extracted entities (exercises, muscle_group, meals, etc.)
        
        For workout logging, extract:
        - exercises (array of exercise names)
        - muscle_group
        - sets (number)
        - reps (number)
        - weight (string)
        - duration (optional)
        - notes (optional)
        
        Return ONLY valid JSON, no extra text.
        """

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])

        try:
            intent = json.loads(response.content)
        except:
            intent = {"type": "general_query", "data": {}}

        state["intent"] = intent
        print(f"✅ Parsed intent: {intent['type']}")
        return state

