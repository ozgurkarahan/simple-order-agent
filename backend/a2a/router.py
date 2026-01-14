"""A2A protocol API endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from .models import (
    ApprovePlanRequest,
    CreateTaskRequest,
    ErrorResponse,
    RejectPlanRequest,
    SendMessageRequest,
    Task,
    TaskState,
)
from .task_manager import TaskManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/a2a", tags=["A2A Protocol"])


def get_task_manager(request: Request) -> TaskManager | None:
    """Get the task manager from app state or global."""
    task_manager = (
        request.app.state.task_manager if hasattr(request.app.state, "task_manager") else None
    )
    if task_manager is None:
        # Get from global in main.py
        from main import task_manager as global_task_manager
        return global_task_manager
    return task_manager


def require_task_manager(request: Request) -> TaskManager:
    """Dependency that ensures task manager is initialized."""
    task_manager = get_task_manager(request)
    if not task_manager:
        raise HTTPException(status_code=503, detail="Task manager not initialized")
    return task_manager


# Type alias for cleaner endpoint signatures
TaskManagerDep = Annotated[TaskManager, Depends(require_task_manager)]


def get_task_or_404(task_manager: TaskManager, task_id: str) -> Task:
    """Get a task by ID or raise 404 if not found."""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(error="Task not found", task_id=task_id).model_dump(),
        )
    return task


@router.post("/tasks", response_model=Task)
async def create_task(body: CreateTaskRequest, task_manager: TaskManagerDep) -> Task:
    """
    Create a new A2A task.

    The task will be created in 'submitted' state and immediately
    start processing asynchronously.
    """
    try:
        task = await task_manager.create_task(body.message, body.metadata)
        logger.info(f"Created task: {task.id}")
        return task

    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str, task_manager: TaskManagerDep) -> Task:
    """Get the current status and details of a task."""
    return get_task_or_404(task_manager, task_id)


@router.post("/tasks/{task_id}/cancel", response_model=Task)
async def cancel_task(task_id: str, task_manager: TaskManagerDep) -> Task:
    """
    Cancel an in-progress task.

    Only tasks in 'submitted' or 'working' state can be canceled.
    """
    task = get_task_or_404(task_manager, task_id)

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
    task_id: str,
    body: SendMessageRequest,
    task_manager: TaskManagerDep,
) -> Task:
    """
    Send a follow-up message to an existing task.

    This is used when a task is in 'input-required' state and
    needs additional information from the user.
    """
    task = get_task_or_404(task_manager, task_id)

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


@router.post("/tasks/{task_id}/approve", response_model=Task)
async def approve_plan(
    task_id: str,
    body: ApprovePlanRequest,
    task_manager: TaskManagerDep,
) -> Task:
    """
    Approve a task's execution plan.

    The task must be in 'awaiting-approval' state.
    """
    task = get_task_or_404(task_manager, task_id)

    if task.status.state != TaskState.AWAITING_APPROVAL:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error=f"Cannot approve task in state: {task.status.state}",
                task_id=task_id,
            ).model_dump(),
        )

    try:
        updated_task = await task_manager.approve_plan(task_id)
        logger.info(f"Approved plan for task: {task_id}")
        return updated_task
    except Exception as e:
        logger.error(f"Failed to approve plan: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/tasks/{task_id}/reject", response_model=Task)
async def reject_plan(
    task_id: str,
    body: RejectPlanRequest,
    task_manager: TaskManagerDep,
) -> Task:
    """
    Reject a task's execution plan and request a new one.

    The task must be in 'awaiting-approval' state.
    """
    task = get_task_or_404(task_manager, task_id)

    if task.status.state != TaskState.AWAITING_APPROVAL:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error=f"Cannot reject task in state: {task.status.state}",
                task_id=task_id,
            ).model_dump(),
        )

    try:
        updated_task = await task_manager.reject_plan(task_id, body.feedback)
        logger.info(f"Rejected plan for task: {task_id}")
        return updated_task
    except Exception as e:
        logger.error(f"Failed to reject plan: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/tasks/{task_id}/pause", response_model=Task)
async def pause_task(
    task_id: str,
    task_manager: TaskManagerDep,
) -> Task:
    """
    Pause an executing task.

    The task must be in 'executing' state.
    """
    task = get_task_or_404(task_manager, task_id)

    if task.status.state != TaskState.EXECUTING:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error=f"Cannot pause task in state: {task.status.state}",
                task_id=task_id,
            ).model_dump(),
        )

    try:
        updated_task = await task_manager.pause_task(task_id)
        logger.info(f"Paused task: {task_id}")
        return updated_task
    except Exception as e:
        logger.error(f"Failed to pause task: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/tasks/{task_id}/resume", response_model=Task)
async def resume_task(
    task_id: str,
    task_manager: TaskManagerDep,
) -> Task:
    """
    Resume a paused task.

    The task must be in 'paused' state.
    """
    task = get_task_or_404(task_manager, task_id)

    if task.status.state != TaskState.PAUSED:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error=f"Cannot resume task in state: {task.status.state}",
                task_id=task_id,
            ).model_dump(),
        )

    try:
        updated_task = await task_manager.resume_task(task_id)
        logger.info(f"Resumed task: {task_id}")
        return updated_task
    except Exception as e:
        logger.error(f"Failed to resume task: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/tasks/{task_id}/stream")
async def stream_task(task_id: str, task_manager: TaskManagerDep) -> StreamingResponse:
    """
    Stream task updates via Server-Sent Events (SSE).

    The stream will send events as the task progresses through
    its lifecycle and produces artifacts.
    """
    # Verify task exists before streaming
    get_task_or_404(task_manager, task_id)

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
