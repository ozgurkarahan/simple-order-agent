"""FastAPI application entry point for Orders Analytics Agent."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from a2a import TaskManager, a2a_router, get_agent_card
from agent import OrdersAgent
from config import get_settings
from mcp import MCPClient

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if get_settings().debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global instances
mcp_client: MCPClient | None = None
orders_agent: OrdersAgent | None = None
task_manager: TaskManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown events."""
    global mcp_client, orders_agent, task_manager

    settings = get_settings()
    logger.info("Starting Orders Analytics Agent...")

    # Initialize MCP client
    mcp_client = MCPClient(
        base_url=settings.mcp_base_url,
        client_id=settings.mcp_client_id,
        client_secret=settings.mcp_client_secret,
    )

    # Initialize the Orders Agent
    orders_agent = OrdersAgent(
        api_key=settings.anthropic_api_key,
        mcp_client=mcp_client,
    )

    # Initialize Task Manager for A2A
    task_manager = TaskManager(agent=orders_agent)

    logger.info("Orders Analytics Agent started successfully")

    yield

    # Cleanup
    logger.info("Shutting down Orders Analytics Agent...")
    if mcp_client:
        await mcp_client.close()


# Create FastAPI application
app = FastAPI(
    title="Orders Analytics Agent",
    description="AI-powered order analytics with MCP and A2A support",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include A2A router
app.include_router(a2a_router)


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
