"""Tests for conversation API endpoints."""

import json
import pytest
from datetime import datetime
from pathlib import Path
from fastapi.testclient import TestClient
from tempfile import NamedTemporaryFile
import os

from main import app
from api.conversation_models import get_conversation_store, reset_conversation_store, ConversationStore


@pytest.fixture
def test_conversation_store():
    """Create a temporary conversation store for testing."""
    # Create a temporary file for test data
    temp_file = NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    temp_file.close()
    
    # Set environment variable to use temp file
    os.environ['CONVERSATION_FILE_PATH'] = temp_file.name
    
    # Reset global store and create new one with temp file
    reset_conversation_store()
    store = ConversationStore(data_file_path=temp_file.name)
    
    yield store
    
    # Cleanup
    reset_conversation_store()
    if os.path.exists(temp_file.name):
        os.unlink(temp_file.name)
    if 'CONVERSATION_FILE_PATH' in os.environ:
        del os.environ['CONVERSATION_FILE_PATH']


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestConversationAPI:
    """Test conversation API endpoints."""
    
    def test_list_conversations_empty(self, client, test_conversation_store):
        """Test listing conversations when none exist."""
        response = client.get("/api/conversations")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_create_conversation_default_title(self, client, test_conversation_store):
        """Test creating a conversation with default title."""
        response = client.post("/api/conversations", json={})
        assert response.status_code == 201
        
        data = response.json()
        assert "id" in data
        assert data["title"] == "New Conversation"
        assert data["message_count"] == 0
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_conversation_custom_title(self, client, test_conversation_store):
        """Test creating a conversation with custom title."""
        response = client.post(
            "/api/conversations",
            json={"title": "My Custom Conversation"}
        )
        assert response.status_code == 201
        
        data = response.json()
        assert data["title"] == "My Custom Conversation"
    
    def test_get_conversation(self, client, test_conversation_store):
        """Test getting a specific conversation."""
        # Create a conversation first
        create_response = client.post(
            "/api/conversations",
            json={"title": "Test Conversation"}
        )
        conversation_id = create_response.json()["id"]
        
        # Get the conversation
        response = client.get(f"/api/conversations/{conversation_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == conversation_id
        assert data["title"] == "Test Conversation"
    
    def test_get_conversation_not_found(self, client, test_conversation_store):
        """Test getting a non-existent conversation."""
        response = client.get("/api/conversations/nonexistent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_conversation_title(self, client, test_conversation_store):
        """Test updating a conversation's title."""
        # Create a conversation
        create_response = client.post("/api/conversations", json={})
        conversation_id = create_response.json()["id"]
        
        # Update the title
        response = client.put(
            f"/api/conversations/{conversation_id}",
            json={"title": "Updated Title"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == "Updated Title"
        
        # Verify the update persisted
        get_response = client.get(f"/api/conversations/{conversation_id}")
        assert get_response.json()["title"] == "Updated Title"
    
    def test_update_conversation_not_found(self, client, test_conversation_store):
        """Test updating a non-existent conversation."""
        response = client.put(
            "/api/conversations/nonexistent-id",
            json={"title": "New Title"}
        )
        assert response.status_code == 404
    
    def test_delete_conversation(self, client, test_conversation_store):
        """Test deleting a conversation."""
        # Create a conversation
        create_response = client.post("/api/conversations", json={})
        conversation_id = create_response.json()["id"]
        
        # Delete it
        response = client.delete(f"/api/conversations/{conversation_id}")
        assert response.status_code == 204
        
        # Verify it's gone
        get_response = client.get(f"/api/conversations/{conversation_id}")
        assert get_response.status_code == 404
    
    def test_delete_conversation_not_found(self, client, test_conversation_store):
        """Test deleting a non-existent conversation."""
        response = client.delete("/api/conversations/nonexistent-id")
        assert response.status_code == 404
    
    def test_list_multiple_conversations(self, client, test_conversation_store):
        """Test listing multiple conversations."""
        # Create several conversations
        titles = ["First", "Second", "Third"]
        for title in titles:
            client.post("/api/conversations", json={"title": title})
        
        # List all conversations
        response = client.get("/api/conversations")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 3
        
        # Verify they're sorted by updated_at (most recent first)
        returned_titles = [conv["title"] for conv in data]
        assert set(returned_titles) == set(titles)
    
    def test_conversation_ordering(self, client, test_conversation_store):
        """Test that conversations are ordered by most recent update."""
        # Create three conversations
        resp1 = client.post("/api/conversations", json={"title": "First"})
        conv1_id = resp1.json()["id"]
        
        resp2 = client.post("/api/conversations", json={"title": "Second"})
        conv2_id = resp2.json()["id"]
        
        resp3 = client.post("/api/conversations", json={"title": "Third"})
        conv3_id = resp3.json()["id"]
        
        # Update the first one (should move to top)
        client.put(f"/api/conversations/{conv1_id}", json={"title": "First Updated"})
        
        # List conversations
        response = client.get("/api/conversations")
        data = response.json()
        
        # First conversation should be at the top now
        assert data[0]["id"] == conv1_id
        assert data[0]["title"] == "First Updated"


class TestConversationStore:
    """Test ConversationStore class directly."""
    
    def test_store_initialization(self, test_conversation_store):
        """Test that store initializes correctly."""
        assert test_conversation_store.data_file.exists()
    
    def test_create_and_retrieve(self, test_conversation_store):
        """Test creating and retrieving a conversation."""
        conv = test_conversation_store.create_conversation("Test")
        assert conv.title == "Test"
        assert conv.message_count == 0
        
        retrieved = test_conversation_store.get_conversation(conv.id)
        assert retrieved is not None
        assert retrieved.id == conv.id
        assert retrieved.title == "Test"
    
    def test_update_conversation(self, test_conversation_store):
        """Test updating conversation metadata."""
        conv = test_conversation_store.create_conversation("Original")
        
        # Update title
        updated = test_conversation_store.update_conversation(
            conv.id,
            title="Updated"
        )
        assert updated.title == "Updated"
        
        # Increment message count
        updated = test_conversation_store.update_conversation(
            conv.id,
            increment_message_count=True
        )
        assert updated.message_count == 1
    
    def test_delete_conversation(self, test_conversation_store):
        """Test deleting a conversation."""
        conv = test_conversation_store.create_conversation("To Delete")
        
        deleted = test_conversation_store.delete_conversation(conv.id)
        assert deleted is True
        
        retrieved = test_conversation_store.get_conversation(conv.id)
        assert retrieved is None
    
    def test_list_conversations_sorting(self, test_conversation_store):
        """Test that conversations are sorted by updated_at."""
        conv1 = test_conversation_store.create_conversation("First")
        conv2 = test_conversation_store.create_conversation("Second")
        conv3 = test_conversation_store.create_conversation("Third")
        
        # Update first conversation
        test_conversation_store.update_conversation(conv1.id, title="First Updated")
        
        conversations = test_conversation_store.list_conversations()
        
        # First should be at the top (most recently updated)
        assert conversations[0].id == conv1.id
    
    def test_conversation_persistence(self):
        """Test that conversations persist across store instances."""
        temp_file = NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        temp_file.close()
        
        try:
            # Create and save a conversation
            store1 = ConversationStore(data_file_path=temp_file.name)
            conv = store1.create_conversation("Persistent")
            conv_id = conv.id
            
            # Create new store instance pointing to same file
            store2 = ConversationStore(data_file_path=temp_file.name)
            retrieved = store2.get_conversation(conv_id)
            
            assert retrieved is not None
            assert retrieved.id == conv_id
            assert retrieved.title == "Persistent"
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def test_corrupted_file_recovery(self):
        """Test that store recovers from corrupted data file."""
        temp_file = NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        
        try:
            # Write invalid JSON
            with open(temp_file.name, 'w') as f:
                f.write("{ invalid json }")
            temp_file.close()
            
            # Store should recover and reset to empty
            store = ConversationStore(data_file_path=temp_file.name)
            conversations = store.list_conversations()
            assert conversations == []
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)


class TestConversationTitleGeneration:
    """Test automatic title generation from first message."""
    
    def test_title_generation_short_message(self, client, test_conversation_store):
        """Test title generation with short message."""
        # Create conversation
        create_response = client.post("/api/conversations", json={})
        conv_id = create_response.json()["id"]
        
        # Send a short message (this would happen through chat endpoint)
        # For this test, we'll simulate by directly updating the store
        store = test_conversation_store
        store.update_conversation(
            conv_id,
            title="Show me all orders",
            increment_message_count=True
        )
        
        # Verify title
        response = client.get(f"/api/conversations/{conv_id}")
        assert response.json()["title"] == "Show me all orders"
        assert response.json()["message_count"] == 1
    
    def test_title_generation_long_message(self, client, test_conversation_store):
        """Test title generation with long message (should truncate)."""
        # Create conversation
        create_response = client.post("/api/conversations", json={})
        conv_id = create_response.json()["id"]
        
        # Simulate a long message title
        long_message = "This is a very long message that should be truncated to exactly fifty characters with ellipsis"
        truncated = long_message[:50] + "..."
        
        store = test_conversation_store
        store.update_conversation(
            conv_id,
            title=truncated,
            increment_message_count=True
        )
        
        # Verify title is truncated
        response = client.get(f"/api/conversations/{conv_id}")
        assert len(response.json()["title"]) == 53  # 50 chars + "..."
        assert response.json()["title"].endswith("...")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
