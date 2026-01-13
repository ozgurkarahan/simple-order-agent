"""FastAPI application entry point for Oz's Order Management Agent."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from dotenv import load_dotenv

# Load environment variables from .env file into os.environ
# This is required for Claude Agent SDK which reads ANTHROPIC_API_KEY from os.environ
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from a2a import TaskManager, a2a_router, get_agent_card
from agent import OrdersAgent
from api import config_router, get_config_store
from api.config_router import set_reload_agent_callback
from config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if get_settings().debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global instances
orders_agent: OrdersAgent | None = None
task_manager: TaskManager | None = None


async def reload_agent() -> None:
    """Reload the Orders Agent with new MCP configuration."""
    global orders_agent, task_manager
    
    logger.info("Reloading Orders Agent with new configuration...")
    
    # Get current MCP config from store
    config_store = get_config_store()
    config = config_store.load_config()
    
    # Create new agent with updated MCP config
    orders_agent = OrdersAgent(mcp_config=config.mcp)
    
    # Update task manager
    if task_manager:
        task_manager.agent = orders_agent
    
    logger.info("Orders Agent reloaded successfully")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown events."""
    global orders_agent, task_manager

    logger.info("Starting Oz's Order Management Agent...")

    # Set up the reload callback for config changes
    set_reload_agent_callback(reload_agent)

    # Load saved configuration or use defaults
    config_store = get_config_store()
    config = config_store.load_config()

    # Initialize the Orders Agent with MCP config
    orders_agent = OrdersAgent(mcp_config=config.mcp)

    # Initialize Task Manager for A2A
    task_manager = TaskManager(agent=orders_agent)

    logger.info("Oz's Order Management Agent started successfully")

    yield

    # Cleanup
    logger.info("Shutting down Oz's Order Management Agent...")


# Create FastAPI application
app = FastAPI(
    title="Oz's Order Management Agent",
    description="AI-powered order analytics with MCP and A2A support",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
settings = get_settings()
# #region agent log
import json as _json
with open("/Users/okarahan/claude-workspace/simple-order-agent/.cursor/debug.log", "a") as _f:
    _f.write(_json.dumps({"location":"main.py:CORS","message":"CORS origins configured","data":{"origins":settings.cors_origins_list},"timestamp":__import__("time").time()*1000,"sessionId":"debug-session","hypothesisId":"H1-backend"}) + "\n")
# #endregion
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(a2a_router)
app.include_router(config_router)


# Request/Response models
class ChatRequest(BaseModel):
    """Chat request model."""

    message: str
    conversation_id: str | None = None


class ChatMessage(BaseModel):
    """Chat message in response."""

    role: str
    content: str


# Health check endpoint
@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "orders-analytics-agent",
        "version": "1.0.0",
    }


# Agent Card endpoint (A2A discovery)
@app.get("/.well-known/agent.json")
async def agent_card() -> dict:
    """Return the A2A Agent Card for discovery."""
    return get_agent_card().model_dump(by_alias=True, exclude_none=True)


# Chat endpoint with streaming
@app.post("/api/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    """
    Chat endpoint for interacting with the Orders Agent.

    Returns a streaming response with Server-Sent Events (SSE).
    """
    if not orders_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    async def generate():
        """Generate SSE events from agent response."""
        try:
            async for event in orders_agent.chat(
                message=request.message,
                conversation_id=request.conversation_id,
            ):
                yield f"event: {event['type']}\ndata: {event['data']}\n\n"

            yield "event: done\ndata: {}\n\n"

        except Exception as e:
            logger.error(f"Chat error: {e}")
            yield f'event: error\ndata: {{"error": "{str(e)}"}}\n\n'

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# Non-streaming chat endpoint for simpler integrations
@app.post("/api/chat/sync")
async def chat_sync(request: ChatRequest) -> dict:
    """
    Synchronous chat endpoint (non-streaming).

    Returns the complete response at once.
    """
    if not orders_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        response = await orders_agent.chat_sync(
            message=request.message,
            conversation_id=request.conversation_id,
        )
        return {
            "message": response,
            "conversation_id": request.conversation_id,
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
