"""Tests for A2A protocol endpoints."""

import pytest
from datetime import datetime

from a2a.models import (
    AgentCard,
    AgentCapabilities,
    AuthConfig,
    AuthType,
    Skill,
    Task,
    TaskState,
    TaskStatus,
    Message,
    Part,
    Artifact,
    CreateTaskRequest,
    TaskStatusUpdate,
)
from a2a.agent_card import get_agent_card


class TestAgentCard:
    """Test cases for Agent Card."""

    def test_get_agent_card(self):
        """Test getting the agent card."""
        card = get_agent_card()

        assert card.name == "Orders Analytics Agent"
        assert card.version == "1.0.0"
        assert card.capabilities.streaming is True
        assert len(card.skills) > 0

    def test_agent_card_serialization(self):
        """Test agent card JSON serialization."""
        card = get_agent_card()
        data = card.model_dump(by_alias=True, exclude_none=True)

        assert "name" in data
        assert "capabilities" in data
        assert "skills" in data
        assert data["capabilities"]["streaming"] is True

    def test_agent_card_skills(self):
        """Test agent card skills."""
        card = get_agent_card()
        skill_ids = [s.id for s in card.skills]

        assert "list_orders" in skill_ids
        assert "get_order" in skill_ids
        assert "create_order" in skill_ids
        assert "analyze_orders" in skill_ids


class TestA2AModels:
    """Test cases for A2A data models."""

    def test_task_state_enum(self):
        """Test TaskState enum values."""
        assert TaskState.SUBMITTED == "submitted"
        assert TaskState.WORKING == "working"
        assert TaskState.COMPLETED == "completed"
        assert TaskState.FAILED == "failed"
        assert TaskState.CANCELED == "canceled"

    def test_task_status(self):
        """Test TaskStatus model."""
        status = TaskStatus(
            state=TaskState.WORKING,
            message="Processing",
        )

        assert status.state == TaskState.WORKING
        assert status.message == "Processing"
        assert status.timestamp is not None

    def test_message(self):
        """Test Message model."""
        msg = Message(
            role="user",
            parts=[Part(type="text", text="Hello")],
        )

        assert msg.role == "user"
        assert len(msg.parts) == 1
        assert msg.parts[0].text == "Hello"

    def test_artifact(self):
        """Test Artifact model."""
        artifact = Artifact(
            id="art-001",
            name="Test Artifact",
            description="A test artifact",
            mime_type="application/json",
            parts=[Part(type="text", text='{"data": "value"}')],
        )

        assert artifact.id == "art-001"
        assert artifact.mime_type == "application/json"

    def test_task(self):
        """Test Task model."""
        task = Task(
            id="task-001",
            status=TaskStatus(state=TaskState.SUBMITTED),
            artifacts=[],
            history=[
                Message(role="user", parts=[Part(type="text", text="Hello")]),
            ],
        )

        assert task.id == "task-001"
        assert task.status.state == TaskState.SUBMITTED
        assert len(task.history) == 1

    def test_create_task_request(self):
        """Test CreateTaskRequest model."""
        request = CreateTaskRequest(
            message=Message(
                role="user",
                parts=[Part(type="text", text="List orders")],
            ),
            metadata={"source": "test"},
        )

        assert request.message.role == "user"
        assert request.metadata["source"] == "test"

    def test_task_status_update(self):
        """Test TaskStatusUpdate model."""
        update = TaskStatusUpdate(
            task_id="task-001",
            status=TaskStatus(state=TaskState.COMPLETED),
        )

        data = update.model_dump(by_alias=True)
        assert data["taskId"] == "task-001"
        assert data["status"]["state"] == "completed"


class TestAgentCardModel:
    """Test Agent Card model structure."""

    def test_full_agent_card(self):
        """Test creating a full agent card."""
        card = AgentCard(
            name="Test Agent",
            description="A test agent",
            version="1.0.0",
            url="http://localhost:8000",
            capabilities=AgentCapabilities(
                streaming=True,
                push_notifications=False,
            ),
            skills=[
                Skill(
                    id="test_skill",
                    name="Test Skill",
                    description="A test skill",
                    tags=["test"],
                    examples=["Example query"],
                ),
            ],
            authentication=AuthConfig(type=AuthType.BEARER),
        )

        assert card.name == "Test Agent"
        assert len(card.skills) == 1
        assert card.authentication.type == AuthType.BEARER

    def test_agent_card_json_aliases(self):
        """Test that JSON aliases are applied correctly."""
        card = AgentCard(
            name="Test",
            description="Test",
            version="1.0.0",
            url="http://test",
            capabilities=AgentCapabilities(
                streaming=True,
                push_notifications=True,
                state_transition_history=True,
            ),
            skills=[],
        )

        data = card.model_dump(by_alias=True)

        # Check that aliases are used
        assert "pushNotifications" in data["capabilities"]
        assert "stateTransitionHistory" in data["capabilities"]
        assert "defaultInputModes" in data
        assert "defaultOutputModes" in data

    def test_auth_config_types(self):
        """Test different authentication types."""
        for auth_type in AuthType:
            config = AuthConfig(type=auth_type)
            assert config.type == auth_type


class TestTaskLifecycle:
    """Test task lifecycle state transitions."""

    def test_valid_state_transitions(self):
        """Test that we can create tasks in all states."""
        for state in TaskState:
            task = Task(
                id=f"task-{state.value}",
                status=TaskStatus(state=state),
            )
            assert task.status.state == state

    def test_task_with_artifacts(self):
        """Test task with multiple artifacts."""
        task = Task(
            id="task-001",
            status=TaskStatus(state=TaskState.COMPLETED),
            artifacts=[
                Artifact(
                    id="art-1",
                    name="Result 1",
                    parts=[Part(text="Data 1")],
                ),
                Artifact(
                    id="art-2",
                    name="Result 2",
                    mime_type="application/json",
                    parts=[Part(text='{"key": "value"}')],
                ),
            ],
        )

        assert len(task.artifacts) == 2
        assert task.artifacts[0].name == "Result 1"
        assert task.artifacts[1].mime_type == "application/json"

    def test_task_with_history(self):
        """Test task with conversation history."""
        task = Task(
            id="task-001",
            status=TaskStatus(state=TaskState.COMPLETED),
            history=[
                Message(role="user", parts=[Part(text="Query")]),
                Message(role="agent", parts=[Part(text="Response")]),
                Message(role="user", parts=[Part(text="Follow-up")]),
                Message(role="agent", parts=[Part(text="More info")]),
            ],
        )

        assert len(task.history) == 4
        assert task.history[0].role == "user"
        assert task.history[1].role == "agent"
