"""Conversation models and storage for multi-conversation support."""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ConversationMetadata(BaseModel):
    """Metadata for a conversation."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(default="New Conversation")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message_count: int = Field(default=0)


class ConversationStore:
    """Handles reading/writing conversation metadata to JSON file."""
    
    def __init__(self, data_file_path: Optional[str] = None):
        """
        Initialize the conversation store.
        
        Args:
            data_file_path: Path to the conversations file. If None, uses default.
        """
        if data_file_path:
            self.data_file = Path(data_file_path)
        else:
            # Check for environment variable override (useful for testing)
            env_path = os.environ.get('CONVERSATION_FILE_PATH')
            if env_path:
                self.data_file = Path(env_path)
            else:
                # Default path in data directory
                self.data_file = Path(__file__).parent.parent / 'data' / 'conversations.json'
        
        # Ensure parent directory exists
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize with empty list if file doesn't exist
        if not self.data_file.exists():
            self._save_conversations([])
    
    def _save_conversations(self, conversations: list[ConversationMetadata]) -> None:
        """Save conversations to file."""
        data = {
            'conversations': [
                {
                    'id': conv.id,
                    'title': conv.title,
                    'created_at': conv.created_at.isoformat(),
                    'updated_at': conv.updated_at.isoformat(),
                    'message_count': conv.message_count
                }
                for conv in conversations
            ]
        }
        
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.debug(f"Saved {len(conversations)} conversations to {self.data_file}")
    
    def _load_conversations(self) -> list[ConversationMetadata]:
        """Load conversations from file."""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            conversations = []
            for conv_data in data.get('conversations', []):
                conversations.append(ConversationMetadata(
                    id=conv_data['id'],
                    title=conv_data['title'],
                    created_at=datetime.fromisoformat(conv_data['created_at']),
                    updated_at=datetime.fromisoformat(conv_data['updated_at']),
                    message_count=conv_data.get('message_count', 0)
                ))
            
            return conversations
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Error loading conversations file: {e}")
            # Reset to empty if corrupted
            self._save_conversations([])
            return []
    
    def list_conversations(self) -> list[ConversationMetadata]:
        """
        Get all conversations, sorted by most recently updated.
        
        Returns:
            List of ConversationMetadata sorted by updated_at descending
        """
        conversations = self._load_conversations()
        # Sort by updated_at descending (most recent first)
        conversations.sort(key=lambda c: c.updated_at, reverse=True)
        return conversations
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationMetadata]:
        """
        Get a specific conversation by ID.
        
        Args:
            conversation_id: ID of the conversation to retrieve
            
        Returns:
            ConversationMetadata if found, None otherwise
        """
        conversations = self._load_conversations()
        for conv in conversations:
            if conv.id == conversation_id:
                return conv
        return None
    
    def create_conversation(self, title: Optional[str] = None) -> ConversationMetadata:
        """
        Create a new conversation.
        
        Args:
            title: Optional title for the conversation
            
        Returns:
            Newly created ConversationMetadata
        """
        conversations = self._load_conversations()
        
        new_conv = ConversationMetadata(
            title=title or "New Conversation"
        )
        
        conversations.append(new_conv)
        self._save_conversations(conversations)
        
        logger.info(f"Created conversation: {new_conv.id} - '{new_conv.title}'")
        return new_conv
    
    def update_conversation(
        self,
        conversation_id: str,
        title: Optional[str] = None,
        increment_message_count: bool = False
    ) -> Optional[ConversationMetadata]:
        """
        Update a conversation's metadata.
        
        Args:
            conversation_id: ID of the conversation to update
            title: New title (if provided)
            increment_message_count: Whether to increment the message count
            
        Returns:
            Updated ConversationMetadata if found, None otherwise
        """
        conversations = self._load_conversations()
        
        for i, conv in enumerate(conversations):
            if conv.id == conversation_id:
                if title is not None:
                    conv.title = title
                
                if increment_message_count:
                    conv.message_count += 1
                
                conv.updated_at = datetime.now(timezone.utc)
                conversations[i] = conv
                
                self._save_conversations(conversations)
                logger.info(f"Updated conversation: {conversation_id}")
                return conv
        
        return None
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: ID of the conversation to delete
            
        Returns:
            True if deleted, False if not found
        """
        conversations = self._load_conversations()
        original_count = len(conversations)
        
        conversations = [c for c in conversations if c.id != conversation_id]
        
        if len(conversations) < original_count:
            self._save_conversations(conversations)
            logger.info(f"Deleted conversation: {conversation_id}")
            return True
        
        return False


# Global instance
_conversation_store: Optional[ConversationStore] = None


def get_conversation_store() -> ConversationStore:
    """Get the global conversation store instance."""
    global _conversation_store
    if _conversation_store is None:
        _conversation_store = ConversationStore()
    return _conversation_store


def reset_conversation_store() -> None:
    """Reset the global conversation store instance (useful for testing)."""
    global _conversation_store
    _conversation_store = None
