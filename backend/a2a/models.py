"""Pydantic models for A2A (Agent-to-Agent) protocol."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ============================================================================
# Agent Card Models
# ============================================================================


class AuthType(str, Enum):
    """Authentication types supported by the agent."""

    NONE = "none"
    BEARER = "bearer"
    API_KEY = "apiKey"
    OAUTH2 = "oauth2"


class AuthConfig(BaseModel):
    """Authentication configuration for the agent."""

    type: AuthType = AuthType.NONE
    credentials_url: str | None = Field(default=None, alias="credentialsUrl")


class AgentCapabilities(BaseModel):
    """Capabilities supported by the agent."""

    streaming: bool = True
    push_notifications: bool = Field(default=False, alias="pushNotifications")
    state_transition_history: bool = Field(default=False, alias="stateTransitionHistory")


class Skill(BaseModel):
    """A skill/capability that the agent can perform."""

    id: str
    name: str
    description: str
    tags: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)


class AgentCard(BaseModel):
    """
    A2A Agent Card describing the agent's capabilities.

    This is served at /.well-known/agent.json for discovery.
    """

    name: str
    description: str
    version: str
    url: str
    documentation_url: str | None = Field(default=None, alias="documentationUrl")
    capabilities: AgentCapabilities
    skills: list[Skill]
    authentication: AuthConfig | None = None
    default_input_modes: list[str] = Field(default=["text"], alias="defaultInputModes")
    default_output_modes: list[str] = Field(default=["text"], alias="defaultOutputModes")


# ============================================================================
# Task Models
# ============================================================================


class TaskState(str, Enum):
    """Possible states for an A2A task."""

    SUBMITTED = "submitted"
    PLANNING = "planning"
    AWAITING_APPROVAL = "awaiting-approval"
    EXECUTING = "executing"
    PAUSED = "paused"
    WORKING = "working"  # Legacy state, kept for backwards compatibility
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    CANCELED = "canceled"
    FAILED = "failed"


class TaskStatus(BaseModel):
    """Current status of a task."""

    state: TaskState
    message: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TaskItemStatus(str, Enum):
    """Status of individual task items in a plan."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskItem(BaseModel):
    """An individual task within a phase."""

    id: str
    description: str
    status: TaskItemStatus = TaskItemStatus.PENDING
    error: str | None = None


class Phase(BaseModel):
    """A phase containing multiple related tasks."""

    id: str
    name: str
    description: str | None = None
    tasks: list[TaskItem]
    status: TaskItemStatus = TaskItemStatus.PENDING


class Plan(BaseModel):
    """Execution plan with phases and tasks."""

    id: str
    description: str
    phases: list[Phase]
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")
    approved_at: datetime | None = Field(default=None, alias="approvedAt")


class Part(BaseModel):
    """A part of a message (text, file, data, etc.)."""

    type: str = "text"
    text: str | None = None
    mime_type: str | None = Field(default=None, alias="mimeType")
    data: str | None = None  # Base64 encoded for binary data
    uri: str | None = None


class Message(BaseModel):
    """A message in the A2A protocol."""

    role: str  # "user" or "agent"
    parts: list[Part]


class Artifact(BaseModel):
    """An artifact produced by a task."""

    id: str
    name: str
    description: str | None = None
    mime_type: str = Field(default="text/plain", alias="mimeType")
    parts: list[Part]


class Task(BaseModel):
    """
    An A2A task representing a unit of work.

    Tasks go through a lifecycle: submitted -> planning -> awaiting-approval -> executing -> completed/failed/canceled
    """

    id: str
    status: TaskStatus
    plan: Plan | None = None
    artifacts: list[Artifact] | None = None
    history: list[Message] | None = None
    metadata: dict[str, Any] | None = None


# ============================================================================
# Request/Response Models
# ============================================================================


class CreateTaskRequest(BaseModel):
    """Request to create a new task."""

    message: Message
    metadata: dict[str, Any] | None = None


class SendMessageRequest(BaseModel):
    """Request to send a message to an existing task."""

    message: Message


class ApprovePlanRequest(BaseModel):
    """Request to approve a task plan."""

    approved: bool = True


class RejectPlanRequest(BaseModel):
    """Request to reject a task plan with feedback."""

    feedback: str


class TaskStatusUpdate(BaseModel):
    """A status update event for SSE streaming."""

    task_id: str = Field(alias="taskId")
    status: TaskStatus
    plan: Plan | None = None
    artifact: Artifact | None = None
    message: Message | None = None


class ErrorResponse(BaseModel):
    """Error response format."""

    error: str
    details: str | None = None
    task_id: str | None = Field(default=None, alias="taskId")
