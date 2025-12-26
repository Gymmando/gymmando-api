"""
Main entry point for GYMMANDO with LiveKit integration.
"""

import os
from datetime import datetime
from pathlib import Path

from livekit import agents
from livekit.agents import Agent, AgentSession, RunContext
from livekit.agents.llm import function_tool
from livekit.plugins import deepgram, openai, silero

from graphs.gymmando import build_graph
from graphs.types import GymmandoState

from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth

load_dotenv()

# Initialize Firebase Admin SDK for agent
firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
if firebase_credentials_path and os.path.exists(firebase_credentials_path):
    try:
        cred = credentials.Certificate(firebase_credentials_path)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin SDK initialized in agent")
    except Exception as e:
        print(f"⚠️  Firebase Admin SDK initialization failed: {e}")
else:
    # Try using default credentials (for GCP deployment)
    try:
        firebase_admin.initialize_app()
        print("✅ Firebase Admin SDK initialized (using default credentials)")
    except Exception as e:
        print(f"⚠️  Firebase Admin SDK not initialized: {e}")

# Get project root directory
PROJECT_ROOT = Path(__file__).parent
PROMPTS_DIR = PROJECT_ROOT / "prompt_templates"


class GymmandoAssistant(Agent):
    """LiveKit agent powered by the multi-agent graph."""

    def __init__(self, user_id: str = "default_user"):
        # Load system prompt directly
        system_prompt = (PROMPTS_DIR / "main_system_prompt.md").read_text()

        super().__init__(instructions=system_prompt)

        self.user_id = user_id
        self.user_name = "User"
        self.graph = build_graph(user_id=user_id)
        self.personality_mode = "bro"

        # Verification counters
        self.total_messages = 0
        self.graph_calls = 0

    @function_tool
    async def process_command(self, context: RunContext, transcript: str) -> str:
        """
        MANDATORY: Process ALL user input through the intelligent agent graph.

        This function MUST be called for every single user message, including:
        - Workout tracking ("I did 3 sets of bench press")
        - Questions ("What did I do last week?")
        - Greetings ("Hey what's up")
        - Any other user input

        The graph handles intent classification, data processing, and response generation.
        """

        # ✅ VERIFICATION: Log that graph is being called
        self.graph_calls += 1
        print(f"\n{'🔥'*30}")
        print(f"✅ GRAPH CALL #{self.graph_calls} - WORKING CORRECTLY!")
        print(f"{'🔥'*30}")

        initial_state: GymmandoState = {
            "transcript": transcript,
            "intent": None,
            "workout_data": None,
            "response": "",
            "personality_mode": self.personality_mode,
            "user_id": self.user_id,
        }

        print(f"\n{'='*60}")
        print(f"🎤 User: {transcript}")
        print(f"{'='*60}")

        final_state = await self.graph.ainvoke(initial_state)

        # Ensure response is always set
        response = final_state.get("response", "")
        if not response or response.strip() == "":
            response = "I'm here to help! Try saying something like 'I did bench press' to log a workout."

        print(f"{'='*60}")
        print(f"🤖 Gymmando ({self.personality_mode} mode): {response}")
        print(f"{'='*60}")
        print(
            f"📊 Stats: {self.graph_calls} graph calls / {self.total_messages} total messages"
        )
        print(f"{'='*60}\n")

        # Handle personality mode changes
        if (
            final_state.get("intent")
            and final_state["intent"].get("type") == "change_personality"
        ):
            new_mode = final_state["intent"].get("data", {}).get("mode", "bro")
            if new_mode.lower() in ["bro", "coach", "commander"]:
                self.personality_mode = new_mode.lower()
                return f"Switched to {new_mode} mode! {response}"

        return response

    @function_tool
    async def get_current_date_and_time(self, context: RunContext) -> str:
        """Get the current date and time."""
        current_datetime = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        return f"The current date and time is {current_datetime}"

    def increment_message_counter(self):
        """Track total messages received."""
        self.total_messages += 1
        print(f"\n📨 Message #{self.total_messages} received")

        # ⚠️ WARNING: Check if graph is being bypassed
        if self.total_messages > self.graph_calls:
            print(
                f"⚠️  WARNING: Graph not called! ({self.graph_calls} calls vs {self.total_messages} messages)"
            )
            print(f"⚠️  This means the LLM responded directly without using the graph!")


async def entrypoint(ctx: agents.JobContext):
    """LiveKit entry point."""

    # Load greeting prompt directly
    greeting_prompt = (PROMPTS_DIR / "main_greeting_prompt.md").read_text()

    session = AgentSession(
        stt=deepgram.STT(model="nova-2"),
        tts=openai.TTS(voice="onyx"),
        llm=openai.LLM(model=os.getenv("LLM_CHOICE", "gpt-4o-mini")),
        vad=silero.VAD.load(),
    )

    # Extract user_id from participant identity (set in LiveKit token)
    user_id = "default_user"
    user_name = "User"
    
    # Initialize assistant with default first
    assistant = GymmandoAssistant(user_id=user_id)
    assistant.user_name = user_name
    
    await session.start(room=ctx.room, agent=assistant)
    
    # Wait a moment for participants to connect, then extract user_id
    import asyncio
    await asyncio.sleep(1.0)  # Wait longer for participant to fully join
    
    # Extract user_id from remote participants
    if ctx.room:
        print(f"🔍 Checking room participants...")
        print(f"🔍 Room name: {ctx.room.name}")
        print(f"🔍 Remote participants count: {len(ctx.room.remote_participants)}")
        print(f"🔍 Remote participant SIDs: {list(ctx.room.remote_participants.keys())}")
        
        # Try multiple ways to get participant identity
        for sid, participant in ctx.room.remote_participants.items():
            # Method 1: Direct attribute access
            participant_identity = getattr(participant, 'identity', None)
            participant_name = getattr(participant, 'name', None)
            
            # Method 2: Try through attributes dict if available
            if not participant_identity and hasattr(participant, 'attributes'):
                participant_identity = participant.attributes.get('identity', None)
            
            # Method 3: Try through info if available
            if not participant_identity and hasattr(participant, 'info'):
                participant_identity = getattr(participant.info, 'identity', None) if participant.info else None
            
            print(f"🔍 Participant SID: {sid}")
            print(f"🔍 Participant identity (method 1): {participant_identity}")
            print(f"🔍 Participant name: {participant_name}")
            print(f"🔍 Participant attributes: {getattr(participant, 'attributes', 'N/A')}")
            
            # Verify the identity is a valid Firebase UID (not fake_human or default)
            if participant_identity and participant_identity not in ["fake_human", "default_user", "user_123"]:
                # Optionally verify it's a valid Firebase UID format (28 chars, alphanumeric)
                if len(participant_identity) > 20:  # Firebase UIDs are typically 28 chars
                    user_id = participant_identity
                    user_name = participant_name or participant_identity
                    print(f"✅ Extracted Firebase user_id: {user_id} ({user_name})")
                    
                    # Update assistant with correct user_id
                    assistant.user_id = user_id
                    assistant.user_name = user_name
                    # Rebuild graph with correct user_id
                    assistant.graph = build_graph(user_id=user_id)
                    break
                else:
                    print(f"⚠️  Identity '{participant_identity}' doesn't look like a Firebase UID")
            elif participant_identity in ["fake_human", "user_123"]:
                print(f"⚠️  Warning: Participant has '{participant_identity}' identity - Firebase token may not be working")
                print(f"⚠️  Check API logs to see if Firebase token is being verified correctly")
    
    print(f"👤 Agent initialized for user: {user_id} ({user_name})")
    
    if user_id == "default_user":
        print(f"⚠️  WARNING: Using default_user - workouts will not be user-specific!")
        print(f"⚠️  Check that:")
        print(f"   1. UI is sending Firebase token in Authorization header")
        print(f"   2. API is verifying token and setting identity in LiveKit token")
        print(f"   3. Participant identity is being extracted correctly")

    await session.generate_reply(instructions=greeting_prompt)


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))

