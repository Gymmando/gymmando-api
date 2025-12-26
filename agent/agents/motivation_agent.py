"""
Motivation Agent: Adds personality, humor, and motivational tone to responses.
Previously known as "Mocking Agent" - renamed to better reflect its purpose.
"""

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from graphs.types import GymmandoState


class MotivationAgent:
    """Adds personality and motivational tone to responses."""

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.8)

        self.personalities = {
            "bro": """You're a loud, enthusiastic gym bro like Eddie Murphy. 
                     Use phrases like "YOOO", "bro", "let's gooo", "beast mode", "crushing it".
                     Be supportive, hype, and high-energy. Celebrate wins big time!""",
            "coach": """You're a supportive, professional fitness coach.
                       Be encouraging but measured. Focus on form, progress, consistency.
                       Use terms like "great work", "let's focus on", "keep it up".
                       Professional but warm.""",
            "commander": """You're a strict, no-nonsense drill sergeant.
                          Be direct, demanding, and intense. No excuses tolerated.
                          Use phrases like "UNACCEPTABLE", "DROP AND GIVE ME", "IS THAT ALL YOU GOT?".
                          Push them harder. Military tone.""",
        }

    async def execute(self, state: GymmandoState) -> GymmandoState:
        """Add personality and motivation to the response."""
        print(f"💪 Motivation Agent: Adding {state['personality_mode']} personality")

        # Gather all context
        workout_data = state.get("workout_data", {})
        nutrition_data = state.get("nutrition_data", {})
        memory = state.get("memory_context", {})

        # Build context string
        context_parts = []
        if workout_data:
            if workout_data.get("status") == "success":
                context_parts.append(f"Workout: {workout_data.get('message')}")
                if "workout" in workout_data:
                    w = workout_data["workout"]
                    context_parts.append(
                        f"Details: {w.get('exercises')} for {w.get('muscle_group')}"
                    )
            elif workout_data.get("status") == "pending_confirmation":
                # User needs to confirm the workout before saving
                summary = workout_data.get("summary", "")
                message = workout_data.get("message", "Here's what I'm about to log")
                
                context_parts.append(f"{message}")
                context_parts.append(f"Workout Summary:\n{summary}")
                context_parts.append("IMPORTANT: Present this summary clearly and ask the user to confirm (say 'yes', 'correct', 'save it', etc.) before logging. Be enthusiastic and clear.")
            elif workout_data.get("status") == "incomplete":
                # Handle incomplete workout - ask for missing details
                next_field = workout_data.get("next_field_to_ask", "")
                collected_data = workout_data.get("collected_data", {})
                message = workout_data.get("message", "I need more workout details")
                
                context_parts.append(f"{message}")
                if collected_data:
                    context_parts.append(f"So far I have: {collected_data}")
                context_parts.append(f"Now I need: {next_field}")
                context_parts.append("IMPORTANT: Ask the user specifically for this one missing detail. Be friendly and conversational. After they provide it, we'll check for other missing details.")

        if nutrition_data:
            context_parts.append(f"Nutrition: {nutrition_data.get('message')}")

        context_parts.append(
            f"User history: {memory.get('total_workouts', 0)} total workouts"
        )

        context = "\n".join(context_parts)

        # Get personality instructions
        personality = self.personalities.get(
            state["personality_mode"], self.personalities["bro"]
        )

        prompt = f"""
        {personality}
        
        Based on this context, generate a motivational response:
        {context}
        
        Keep it short (2-3 sentences max). Be conversational, fun, and in character.
        Match the personality mode perfectly.
        """

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        state["response"] = response.content

        print(f"✅ Motivational response: {state['response'][:60]}...")
        return state

