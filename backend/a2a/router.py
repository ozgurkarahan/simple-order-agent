"""A2A protocol API endpoints."""

import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from .models import (
    CreateTaskRequest,
    ErrorResponse,
    SendMessageRequest,
    Task,
    TaskState,
)

if TYPE_CHECKING:
    from .task_manager import TaskManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/a2a", tags=["A2A Protocol"])


def get_task_manager(request: Request) -> "TaskManager":
    """Get the task manager from app state."""
    task_manager = (
        request.app.state.task_manager if hasattr(request.app.state, "task_manager") else None
    )
    if task_manager is None:
        # Get from global in main.py
        from main import task_manager as global_task_manager

        return global_task_manager
    return task_manager


@router.post("/tasks", response_model=Task)
async def create_task(request: Request, body: CreateTaskRequest) -> Task:
    """
    Create a new A2A task.

    The task will be created in 'submitted' state and immediately
    start processing asynchronously.
    """
    task_manager = get_task_manager(request)

    if not task_manager:
        raise HTTPException(status_code=503, detail="Task manager not initialized")

    try:
        task = await task_manager.create_task(body.message, body.metadata)
        logger.info(f"Created task: {task.id}")
        return task

    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/tasks/{task_id}", response_model=Task)
async def get_task(request: Request, task_id: str) -> Task:
    """
    Get the current status and details of a task.
    """
    task_manager = get_task_manager(request)

    if not task_manager:
        raise HTTPException(status_code=503, detail="Task manager not initialized")

    task = task_manager.get_task(task_id)

    if not task:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error="Task not found",
                task_id=task_id,
            ).model_dump(),
        )

    return task


@router.post("/tasks/{task_id}/cancel", response_model=Task)
async def cancel_task(request: Request, task_id: str) -> Task:
    """
    Cancel an in-progress task.

    Only tasks in 'submitted' or 'working' state can be canceled.
    """
    task_manager = get_task_manager(request)

    if not task_manager:
        raise HTTPException(status_code=503, detail="Task manager not initialized")

    task = task_manager.get_task(task_id)

    if not task:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error="Task not found",
                task_id=task_id,
            ).model_dump(),
        )

    if task.status.state not in [TaskState.SUBMITTED, TaskState.WORKING]:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error=f"Cannot cancel task in state: {task.status.state}",
                task_id=task_id,
            ).model_dump(),
        )

    updated_task = await task_manager.cancel_task(task_id)
    return updated_task


@router.post("/tasks/{task_id}/message", response_model=Task)
async def send_message(
    request: Request,
    task_id: str,
    body: SendMessageRequest,
) -> Task:
    """
    Send a follow-up message to an existing task.

    This is used when a task is in 'input-required' state and
    needs additional information from the user.
    """
    task_manager = get_task_manager(request)

    if not task_manager:
        raise HTTPException(status_code=503, detail="Task manager not initialized")

    task = task_manager.get_task(task_id)

    if not task:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error="Task not found",
                task_id=task_id,
            ).model_dump(),
        )

    if task.status.state not in [TaskState.INPUT_REQUIRED, TaskState.WORKING]:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error=f"Cannot send message to task in state: {task.status.state}",
                task_id=task_id,
            ).model_dump(),
        )

    updated_task = await task_manager.send_message(task_id, body.message)
    return updated_task


@router.get("/tasks/{task_id}/stream")
async def stream_task(request: Request, task_id: str) -> StreamingResponse:
    """
    Stream task updates via Server-Sent Events (SSE).

    The stream will send events as the task progresses through
    its lifecycle and produces artifacts.
    """
    task_manager = get_task_manager(request)

    if not task_manager:
        raise HTTPException(status_code=503, detail="Task manager not initialized")

    task = task_manager.get_task(task_id)

    if not task:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error="Task not found",
                task_id=task_id,
            ).model_dump(),
        )

    async def event_generator():
        """Generate SSE events for task updates."""
        async for event in task_manager.stream_task(task_id):
            yield f"event: {event['event']}\ndata: {event['data']}\n\n"

        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
