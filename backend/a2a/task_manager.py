"""Task lifecycle manager for A2A protocol."""

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from datetime import datetime

from .models import (
    Artifact,
    Message,
    Part,
    Phase,
    Plan,
    Task,
    TaskItem,
    TaskItemStatus,
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
        self._paused_tasks: set[str] = set()
        self._approval_events: dict[str, asyncio.Event] = {}
        self._resume_events: dict[str, asyncio.Event] = {}

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
        await self._emit_event(
            task_id,
            "status",
            TaskStatusUpdate(
                task_id=task_id,
                status=task.status,
            ),
        )

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

    async def approve_plan(self, task_id: str) -> Task:
        """
        Approve a task's plan and start execution.

        Args:
            task_id: ID of the task

        Returns:
            Updated task
        """
        task = self.tasks[task_id]

        if task.status.state != TaskState.AWAITING_APPROVAL:
            raise ValueError(f"Task {task_id} is not awaiting approval")

        # Mark plan as approved
        if task.plan:
            task.plan.approved_at = datetime.utcnow()

        # Update status
        task.status = TaskStatus(
            state=TaskState.EXECUTING,
            message="Plan approved, starting execution",
        )

        await self._emit_event(
            task_id,
            "status",
            TaskStatusUpdate(
                task_id=task_id,
                status=task.status,
                plan=task.plan,
            ),
        )

        # Signal approval event to continue processing
        if task_id in self._approval_events:
            self._approval_events[task_id].set()

        return task

    async def reject_plan(self, task_id: str, feedback: str) -> Task:
        """
        Reject a task's plan and request a new one.

        Args:
            task_id: ID of the task
            feedback: User feedback on why the plan was rejected

        Returns:
            Updated task
        """
        task = self.tasks[task_id]

        if task.status.state != TaskState.AWAITING_APPROVAL:
            raise ValueError(f"Task {task_id} is not awaiting approval")

        # Add feedback to history
        feedback_message = Message(
            role="user",
            parts=[Part(type="text", text=f"Plan rejected. Feedback: {feedback}")],
        )
        if task.history is None:
            task.history = []
        task.history.append(feedback_message)

        # Update status back to planning
        task.status = TaskStatus(
            state=TaskState.PLANNING,
            message="Plan rejected, creating new plan",
        )

        await self._emit_event(
            task_id,
            "status",
            TaskStatusUpdate(
                task_id=task_id,
                status=task.status,
            ),
        )

        # Reset approval event and continue processing
        if task_id in self._approval_events:
            self._approval_events[task_id].clear()

        # Re-generate plan with feedback
        asyncio.create_task(self._generate_plan(task_id, feedback))

        return task

    async def pause_task(self, task_id: str) -> Task:
        """
        Pause an executing task.

        Args:
            task_id: ID of the task

        Returns:
            Updated task
        """
        task = self.tasks[task_id]

        if task.status.state != TaskState.EXECUTING:
            raise ValueError(f"Task {task_id} is not executing")

        self._paused_tasks.add(task_id)

        task.status = TaskStatus(
            state=TaskState.PAUSED,
            message="Task paused by user",
        )

        await self._emit_event(
            task_id,
            "status",
            TaskStatusUpdate(
                task_id=task_id,
                status=task.status,
                plan=task.plan,
            ),
        )

        return task

    async def resume_task(self, task_id: str) -> Task:
        """
        Resume a paused task.

        Args:
            task_id: ID of the task

        Returns:
            Updated task
        """
        task = self.tasks[task_id]

        if task.status.state != TaskState.PAUSED:
            raise ValueError(f"Task {task_id} is not paused")

        self._paused_tasks.discard(task_id)

        task.status = TaskStatus(
            state=TaskState.EXECUTING,
            message="Task resumed",
        )

        await self._emit_event(
            task_id,
            "status",
            TaskStatusUpdate(
                task_id=task_id,
                status=task.status,
                plan=task.plan,
            ),
        )

        # Signal resume event
        if task_id in self._resume_events:
            self._resume_events[task_id].set()

        return task

    async def _process_task(self, task_id: str) -> None:
        """
        Process a task asynchronously with planning-first approach.

        Flow: SUBMITTED -> PLANNING -> AWAITING_APPROVAL -> EXECUTING -> COMPLETED

        Args:
            task_id: ID of the task to process
        """
        if task_id in self._processing_tasks:
            return

        self._processing_tasks.add(task_id)

        try:
            task = self.tasks[task_id]

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
                await self._emit_event(
                    task_id,
                    "status",
                    TaskStatusUpdate(
                        task_id=task_id,
                        status=task.status,
                    ),
                )
                return

            # PHASE 1: Generate Plan
            await self._generate_plan(task_id)

            # PHASE 2: Wait for Approval
            await self._wait_for_approval(task_id)

            # PHASE 3: Execute Plan
            await self._execute_plan(task_id)

        except Exception as e:
            logger.error(f"Task processing error: {e}")
            task = self.tasks[task_id]
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message=f"Processing failed: {str(e)}",
            )
            await self._emit_event(
                task_id,
                "status",
                TaskStatusUpdate(
                    task_id=task_id,
                    status=task.status,
                ),
            )

        finally:
            self._processing_tasks.discard(task_id)

    async def _generate_plan(self, task_id: str, feedback: str | None = None) -> None:
        """
        Generate execution plan for a task.

        Args:
            task_id: ID of the task
            feedback: Optional feedback from plan rejection
        """
        task = self.tasks[task_id]

        # Update status to planning
        task.status = TaskStatus(
            state=TaskState.PLANNING,
            message="Generating execution plan",
        )
        await self._emit_event(
            task_id,
            "status",
            TaskStatusUpdate(
                task_id=task_id,
                status=task.status,
            ),
        )

        # Get user message
        user_message = ""
        if task.history:
            for msg in reversed(task.history):
                if msg.role == "user":
                    for part in msg.parts:
                        if part.text:
                            user_message = part.text
                            break
                    break

        # Add feedback if plan was rejected
        if feedback:
            user_message = f"{user_message}\n\nPrevious plan was rejected. User feedback: {feedback}"

        # Generate plan using agent
        plan_dict = await self.agent.generate_plan(user_message)

        # Convert to Plan model
        phases = []
        for phase_dict in plan_dict.get("phases", []):
            tasks = []
            for task_dict in phase_dict.get("tasks", []):
                tasks.append(
                    TaskItem(
                        id=task_dict["id"],
                        description=task_dict["description"],
                        status=TaskItemStatus.PENDING,
                    )
                )

            phases.append(
                Phase(
                    id=phase_dict["id"],
                    name=phase_dict["name"],
                    description=phase_dict.get("description"),
                    tasks=tasks,
                    status=TaskItemStatus.PENDING,
                )
            )

        plan = Plan(
            id=f"plan-{uuid.uuid4().hex[:8]}",
            description=plan_dict.get("description", "Execution plan"),
            phases=phases,
        )

        task.plan = plan

        # Update status to awaiting approval
        task.status = TaskStatus(
            state=TaskState.AWAITING_APPROVAL,
            message="Plan ready for approval",
        )

        await self._emit_event(
            task_id,
            "status",
            TaskStatusUpdate(
                task_id=task_id,
                status=task.status,
                plan=plan,
            ),
        )

    async def _wait_for_approval(self, task_id: str) -> None:
        """
        Wait for user to approve the plan.

        Args:
            task_id: ID of the task
        """
        # Create approval event
        self._approval_events[task_id] = asyncio.Event()

        # Wait for approval (blocking until approve_plan is called)
        await self._approval_events[task_id].wait()

        # Clean up
        del self._approval_events[task_id]

    async def _execute_plan(self, task_id: str) -> None:
        """
        Execute the approved plan task by task.

        Args:
            task_id: ID of the task
        """
        task = self.tasks[task_id]

        if not task.plan:
            raise ValueError("No plan to execute")

        # Create resume event for pause handling
        self._resume_events[task_id] = asyncio.Event()
        self._resume_events[task_id].set()  # Initially not paused

        try:
            # Execute each phase
            for phase in task.plan.phases:
                # Update phase status
                phase.status = TaskItemStatus.IN_PROGRESS

                await self._emit_event(
                    task_id,
                    "plan_update",
                    TaskStatusUpdate(
                        task_id=task_id,
                        status=task.status,
                        plan=task.plan,
                    ),
                )

                # Execute each task in the phase
                for task_item in phase.tasks:
                    # Check for pause
                    if task_id in self._paused_tasks:
                        await self._resume_events[task_id].wait()

                    # Update task item status
                    task_item.status = TaskItemStatus.IN_PROGRESS

                    await self._emit_event(
                        task_id,
                        "plan_update",
                        TaskStatusUpdate(
                            task_id=task_id,
                            status=task.status,
                            plan=task.plan,
                        ),
                    )

                    try:
                        # Execute the task using agent
                        await self._execute_task_item(task_id, task_item)

                        task_item.status = TaskItemStatus.COMPLETED

                    except Exception as e:
                        logger.error(f"Task item execution error: {e}")
                        task_item.status = TaskItemStatus.FAILED
                        task_item.error = str(e)

                    await self._emit_event(
                        task_id,
                        "plan_update",
                        TaskStatusUpdate(
                            task_id=task_id,
                            status=task.status,
                            plan=task.plan,
                        ),
                    )

                # Mark phase as completed
                phase.status = TaskItemStatus.COMPLETED

            # Mark task as completed
            task.status = TaskStatus(
                state=TaskState.COMPLETED,
                message="All tasks completed successfully",
            )

            await self._emit_event(
                task_id,
                "status",
                TaskStatusUpdate(
                    task_id=task_id,
                    status=task.status,
                    plan=task.plan,
                ),
            )

        finally:
            # Clean up resume event
            if task_id in self._resume_events:
                del self._resume_events[task_id]

    async def _execute_task_item(self, task_id: str, task_item: TaskItem) -> None:
        """
        Execute a single task item using the agent.

        Args:
            task_id: ID of the parent task
            task_item: Task item to execute
        """
        task = self.tasks[task_id]

        # Get original user message for context
        user_message = ""
        if task.history:
            for msg in task.history:
                if msg.role == "user":
                    for part in msg.parts:
                        if part.text:
                            user_message = part.text
                            break
                    break

        # Create instruction for this specific task item
        instruction = f"You are executing a plan. Current task: {task_item.description}\n\nOriginal request: {user_message}\n\nExecute this task and provide results."

        # Execute with agent
        response_parts: list[Part] = []

        async for event in self.agent.chat(instruction):
            event_data = json.loads(event["data"])

            if event_data.get("type") == "text":
                response_parts.append(
                    Part(
                        type="text",
                        text=event_data["content"],
                    )
                )

                # Emit message event
                await self._emit_event(
                    task_id,
                    "message",
                    {
                        "taskId": task_id,
                        "message": {
                            "role": "agent",
                            "parts": [{"type": "text", "text": event_data["content"]}],
                        },
                    },
                )

            elif event_data.get("type") == "tool_use":
                # Emit tool use event
                await self._emit_event(
                    task_id,
                    "tool_use",
                    {
                        "taskId": task_id,
                        "tool": event_data.get("tool"),
                        "input": event_data.get("input", {}),
                    },
                )

            elif event_data.get("type") == "tool_result":
                # Create an artifact for tool results
                artifact = Artifact(
                    id=self._generate_artifact_id(),
                    name=f"Result: {task_item.description}",
                    description=f"Result from: {task_item.description}",
                    mime_type="application/json",
                    parts=[
                        Part(
                            type="text",
                            text=event_data.get("result", ""),
                        )
                    ],
                )

                if task.artifacts is None:
                    task.artifacts = []
                task.artifacts.append(artifact)

                # Emit artifact event
                await self._emit_event(
                    task_id,
                    "artifact",
                    TaskStatusUpdate(
                        task_id=task_id,
                        status=task.status,
                        artifact=artifact,
                    ),
                )

        # Add agent response to history
        if response_parts:
            agent_message = Message(
                role="agent",
                parts=response_parts,
            )
            if task.history is None:
                task.history = []
            task.history.append(agent_message)

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

            await self.task_events[task_id].put(
                {
                    "event": event_type,
                    "data": event_data,
                }
            )

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
        # Also check for awaiting approval state (needs user interaction)
        interactive_states = {TaskState.AWAITING_APPROVAL}

        while task.status.state not in terminal_states:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield event

                # Update our reference to task status
                task = self.tasks[task_id]

            except TimeoutError:
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
