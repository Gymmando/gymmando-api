import os

from dotenv import load_dotenv
from fastapi import FastAPI
from livekit import api

load_dotenv()

app = FastAPI()


def create_livekit_token():
    token = api.AccessToken(
        api_key=os.getenv("LIVEKIT_API_KEY"), api_secret=os.getenv("LIVEKIT_API_SECRET")
    )

    token.with_identity("user_123")
    token.with_name("Gym User")
    token.with_grants(api.VideoGrants(room_join=True, room="gym-room"))

    return token.to_jwt()


@app.get("/token")
def get_token():
    token = create_livekit_token()
    return {"token": token}
