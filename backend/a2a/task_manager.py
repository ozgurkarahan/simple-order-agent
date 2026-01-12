"""Task lifecycle manager for A2A protocol."""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, AsyncGenerator, TYPE_CHECKING

from .models import (
    Artifact,
    Message,
    Part,
    Task,
    TaskState,
    TaskStatus,
    TaskStatusUpdate,
)

if TYPE_CHECKING:
    from agent import OrdersAgent

logger = logging.getLogger(__name__)


class TaskManager:
    """
    Manages A2A task lifecycle.

    Handles task creation, state transitions, and streaming updates.
    """

    def __init__(self, agent: "OrdersAgent"):
        """
        Initialize the task manager.

        Args:
            agent: The Orders Agent to use for processing tasks
        """
        self.agent = agent
        self.tasks: dict[str, Task] = {}
        self.task_events: dict[str, asyncio.Queue] = {}
        self._processing_tasks: set[str] = set()

    def _generate_task_id(self) -> str:
        """Generate a unique task ID."""
        return f"task-{uuid.uuid4().hex[:12]}"

    def _generate_artifact_id(self) -> str:
        """Generate a unique artifact ID."""
        return f"artifact-{uuid.uuid4().hex[:8]}"

    async def create_task(
        self,
        message: Message,
        metadata: dict[str, Any] | None = None,
    ) -> Task:
        """
        Create a new task and start processing.

        Args:
            message: Initial message from the user
            metadata: Optional task metadata

        Returns:
            Created task
        """
        task_id = self._generate_task_id()

        task = Task(
            id=task_id,
            status=TaskStatus(
                state=TaskState.SUBMITTED,
                message="Task created",
            ),
            artifacts=[],
            history=[message],
            metadata=metadata,
        )

        self.tasks[task_id] = task
        self.task_events[task_id] = asyncio.Queue()

        # Start processing asynchronously
        asyncio.create_task(self._process_task(task_id))

        return task

    def get_task(self, task_id: str) -> Task | None:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    async def cancel_task(self, task_id: str) -> Task:
        """
        Cancel a task.

        Args:
            task_id: ID of the task to cancel

        Returns:
            Updated task
        """
        task = self.tasks[task_id]

        task.status = TaskStatus(
            state=TaskState.CANCELED,
            message="Task canceled by user",
        )

        # Notify streaming clients
        await self._emit_event(task_id, "status", TaskStatusUpdate(
            task_id=task_id,
            status=task.status,
        ))

        return task

    async def send_message(self, task_id: str, message: Message) -> Task:
        """
        Send a follow-up message to a task.

        Args:
            task_id: ID of the task
            message: Message to send

        Returns:
            Updated task
        """
        task = self.tasks[task_id]

        # Add message to history
        if task.history is None:
            task.history = []
        task.history.append(message)

        # Continue processing
        asyncio.create_task(self._process_task(task_id))

        return task

    async def _process_task(self, task_id: str) -> None:
        """
        Process a task asynchronously.

        Args:
            task_id: ID of the task to process
        """
        if task_id in self._processing_tasks:
            return

        self._processing_tasks.add(task_id)

        try:
            task = self.tasks[task_id]

            # Update status to working
            task.status = TaskStatus(
                state=TaskState.WORKING,
                message="Processing request",
            )
            await self._emit_event(task_id, "status", TaskStatusUpdate(
                task_id=task_id,
                status=task.status,
            ))

            # Get the last user message
            user_message = ""
            if task.history:
                for msg in reversed(task.history):
                    if msg.role == "user":
                        for part in msg.parts:
                            if part.text:
                                user_message = part.text
                                break
                        break

            if not user_message:
                task.status = TaskStatus(
                    state=TaskState.FAILED,
                    message="No user message found",
                )
                await self._emit_event(task_id, "status", TaskStatusUpdate(
                    task_id=task_id,
                    status=task.status,
                ))
                return

            # Process with the agent
            response_parts: list[Part] = []

            async for event in self.agent.chat(user_message):
                event_data = json.loads(event["data"])

                if event_data.get("type") == "text":
                    response_parts.append(Part(
                        type="text",
                        text=event_data["content"],
                    ))

                    # Emit message event
                    await self._emit_event(task_id, "message", {
                        "taskId": task_id,
                        "message": {
                            "role": "agent",
                            "parts": [{"type": "text", "text": event_data["content"]}],
                        },
                    })

                elif event_data.get("type") == "tool_result":
                    # Create an artifact for tool results
                    artifact = Artifact(
                        id=self._generate_artifact_id(),
                        name=f"Tool Result",
                        description="Result from tool execution",
                        mime_type="application/json",
                        parts=[Part(
                            type="text",
                            text=event_data.get("result", ""),
                        )],
                    )

                    if task.artifacts is None:
                        task.artifacts = []
                    task.artifacts.append(artifact)

                    # Emit artifact event
                    await self._emit_event(task_id, "artifact", TaskStatusUpdate(
                        task_id=task_id,
                        status=task.status,
                        artifact=artifact,
                    ))

            # Add agent response to history
            if response_parts:
                agent_message = Message(
                    role="agent",
                    parts=response_parts,
                )
                if task.history is None:
                    task.history = []
                task.history.append(agent_message)

            # Mark as completed
            task.status = TaskStatus(
                state=TaskState.COMPLETED,
                message="Task completed successfully",
            )
            await self._emit_event(task_id, "status", TaskStatusUpdate(
                task_id=task_id,
                status=task.status,
            ))

        except Exception as e:
            logger.error(f"Task processing error: {e}")
            task = self.tasks[task_id]
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message=f"Processing failed: {str(e)}",
            )
            await self._emit_event(task_id, "status", TaskStatusUpdate(
                task_id=task_id,
                status=task.status,
            ))

        finally:
            self._processing_tasks.discard(task_id)

    async def _emit_event(
        self,
        task_id: str,
        event_type: str,
        data: TaskStatusUpdate | dict,
    ) -> None:
        """
        Emit an event to streaming clients.

        Args:
            task_id: Task ID
            event_type: Type of event (status, message, artifact)
            data: Event data
        """
        if task_id in self.task_events:
            if isinstance(data, TaskStatusUpdate):
                event_data = data.model_dump_json(by_alias=True)
            else:
                event_data = json.dumps(data)

            await self.task_events[task_id].put({
                "event": event_type,
                "data": event_data,
            })

    async def stream_task(self, task_id: str) -> AsyncGenerator[dict, None]:
        """
        Stream task events.

        Args:
            task_id: Task ID to stream

        Yields:
            Event dictionaries with event type and data
        """
        if task_id not in self.task_events:
            return

        queue = self.task_events[task_id]
        task = self.tasks[task_id]

        # Send initial status
        yield {
            "event": "status",
            "data": TaskStatusUpdate(
                task_id=task_id,
                status=task.status,
            ).model_dump_json(by_alias=True),
        }

        # Stream events until task is in terminal state
        terminal_states = {TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELED}

        while task.status.state not in terminal_states:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield event

                # Update our reference to task status
                task = self.tasks[task_id]

            except asyncio.TimeoutError:
                # Send keepalive
                yield {
                    "event": "keepalive",
                    "data": "{}",
                }
                task = self.tasks[task_id]

        # Drain any remaining events
        while not queue.empty():
            event = queue.get_nowait()
            yield event
