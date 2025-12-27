# gymmando-api

The API repository for GYMMANDO, containing both the LiveKit agent service and the FastAPI service.

## Structure

- **`agent/`** - LiveKit agent service with multi-agent LangGraph system
  - `main.py` - Entry point for the LiveKit agent
  - `agents/` - Specialized agents (parsing, workout, nutrition, memory, motivation)
  - `graphs/` - LangGraph orchestration and state management
  - `database/` - Supabase client integration
  - `prompt_templates/` - System and greeting prompts
  - `tests/` - Test structure (unit, integration, e2e)

- **`api/`** - FastAPI service for LiveKit token generation

## Quick Start

### Agent Service

1. Install dependencies:
```bash
cd agent
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```env
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
OPENAI_API_KEY=your-openai-key
DEEPGRAM_API_KEY=your-deepgram-key
LIVEKIT_URL=your-livekit-url
LIVEKIT_API_KEY=your-livekit-key
LIVEKIT_API_SECRET=your-livekit-secret
LLM_CHOICE=gpt-4o-mini
```

3. Run the agent:
```bash
python main.py dev
```

### API Service

1. Install dependencies:
```bash
cd api
pip install -r requirements.txt
```

2. Run the API:
```bash
uvicorn api:app --reload
```

## Database Setup

See `agent/SUPABASE_SETUP.md` for detailed Supabase setup instructions.
