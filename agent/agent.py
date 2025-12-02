"""
Simplest GYMMANDO - One file, one LLM, LiveKit integration (Dec 2025).
"""

import os

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentSession, JobContext
from livekit.plugins import deepgram, openai, silero

load_dotenv()


async def entrypoint(ctx: JobContext):
    """LiveKit entry point."""

    await ctx.connect()

    # Create agent with instructions
    agent = Agent(
        instructions="""
        You are GYMMANDO, a gym bro voice assistant. 
        You help users track workouts and answer fitness questions.
        Be encouraging, enthusiastic, and supportive.
        Keep responses conversational and brief.
        """
    )

    # Create session with STT/LLM/TTS
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=openai.LLM(model="gpt-5-mini"),
        tts=openai.TTS(voice="onyx"),
        vad=silero.VAD.load(),
    )

    # Start session
    await session.start(agent=agent, room=ctx.room)

    # Initial greeting
    await session.generate_reply(instructions="Greet the user as their gym buddy!")


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
