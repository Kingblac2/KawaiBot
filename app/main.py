import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.models import ChatRequest, ChatResponse
from app import orchestrator, database

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("app.main")

app = FastAPI(
    title="ViperAI Secure Chatbot Backend",
    description="Secure AI Chatbot showcasing CoT, Prompt Chaining, ReAct framework, and Safety Guardrails.",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Database JSON
database.init_db()

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        response_data = orchestrator.run_chat_pipeline(request.message)
        return response_data
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error executing chat pipeline.")

@app.get("/api/history")
async def history_endpoint():
    try:
        history = database.get_history()
        return history
    except Exception as e:
        logger.error(f"Error fetching history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not read chat history database.")

# Serve Frontend static assets
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"

if frontend_dir.exists():
    # Mount everything in frontend folder under /frontend or just mount static
    # To avoid conflict with api endpoints, we will serve index.html directly on root
    @app.get("/")
    async def serve_index():
        return FileResponse(frontend_dir / "index.html")

    # Mount remaining assets (css, js) if we want, or just mount the whole directory
    # under the root except the specific /api routes
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
else:
    logger.warning("Frontend directory not found. Running in API-only mode.")
