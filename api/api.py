import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from livekit import api
import firebase_admin
from firebase_admin import credentials, auth

load_dotenv()

app = FastAPI()

# Initialize Firebase Admin SDK
firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
if firebase_credentials_path and os.path.exists(firebase_credentials_path):
    cred = credentials.Certificate(firebase_credentials_path)
    firebase_admin.initialize_app(cred)
    print("✅ Firebase Admin SDK initialized")
else:
    # Try using service account from environment variable (for GCP deployment)
    try:
        firebase_admin.initialize_app()
        print("✅ Firebase Admin SDK initialized (using default credentials)")
    except Exception as e:
        print(f"⚠️  Firebase Admin SDK not initialized: {e}")
        print("⚠️  Token verification will be disabled")


def verify_firebase_token(id_token: str) -> Optional[dict]:
    """Verify Firebase ID token and return decoded token."""
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print(f"❌ Firebase token verification failed: {e}")
        return None


def create_livekit_token(user_id: str, user_name: str = "Gym User"):
    """Create LiveKit access token with user identity."""
    token = api.AccessToken(
        api_key=os.getenv("LIVEKIT_API_KEY"), api_secret=os.getenv("LIVEKIT_API_SECRET")
    )

    # Set identity to user_id (Firebase UID) - this will be available as participant.identity
    token.with_identity(user_id)
    token.with_name(user_name)
    token.with_grants(api.VideoGrants(room_join=True, room="gym-room"))

    return token.to_jwt()


@app.get("/token")
def get_token(authorization: Optional[str] = Header(None)):
    """
    Generate LiveKit token after verifying Firebase authentication.
    
    Expects: Authorization header with "Bearer <firebase_id_token>"
    """
    if not authorization:
        print("❌ No authorization header provided")
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Extract token from "Bearer <token>"
    try:
        scheme, id_token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise ValueError("Invalid authorization scheme")
        print(f"✅ Extracted Firebase token (length: {len(id_token)})")
    except ValueError as e:
        print(f"❌ Invalid authorization header format: {e}")
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    # Verify Firebase token
    decoded_token = verify_firebase_token(id_token)
    if not decoded_token:
        print("❌ Firebase token verification failed")
        raise HTTPException(status_code=401, detail="Invalid or expired Firebase token")
    
    # Extract user info
    user_id = decoded_token.get("uid")
    user_name = decoded_token.get("name", decoded_token.get("email", "Gym User"))
    
    print(f"✅ Verified Firebase user: {user_id} ({user_name})")
    
    # Generate LiveKit token with user identity
    token = create_livekit_token(user_id, user_name)
    print(f"✅ Generated LiveKit token with identity: {user_id}")
    return {"token": token}
