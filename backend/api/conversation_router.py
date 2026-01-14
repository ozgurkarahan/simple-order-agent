"""API router for conversation management."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.conversation_models import (
    ConversationMetadata,
    get_conversation_store,
)

logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/api/conversations", tags=["conversations"])


class CreateConversationRequest(BaseModel):
    """Request model for creating a conversation."""
    
    title: Optional[str] = Field(default=None, description="Optional conversation title")


class UpdateConversationRequest(BaseModel):
    """Request model for updating a conversation."""
    
    title: str = Field(..., description="New conversation title")


class ConversationResponse(BaseModel):
    """Response model for conversation metadata."""
    
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int


def _to_response(conv: ConversationMetadata) -> ConversationResponse:
    """Convert ConversationMetadata to response model."""
    return ConversationResponse(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at.isoformat(),
        updated_at=conv.updated_at.isoformat(),
        message_count=conv.message_count
    )


@router.get("", response_model=list[ConversationResponse])
async def list_conversations() -> list[ConversationResponse]:
    """
    List all conversations, sorted by most recently updated.
    
    Returns:
        List of conversation metadata
    """
    store = get_conversation_store()
    conversations = store.list_conversations()
    return [_to_response(conv) for conv in conversations]


@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    request: CreateConversationRequest
) -> ConversationResponse:
    """
    Create a new conversation.
    
    Args:
        request: Create conversation request
        
    Returns:
        Created conversation metadata
    """
    store = get_conversation_store()
    conversation = store.create_conversation(title=request.title)
    return _to_response(conversation)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str) -> ConversationResponse:
    """
    Get a specific conversation by ID.
    
    Args:
        conversation_id: ID of the conversation to retrieve
        
    Returns:
        Conversation metadata
        
    Raises:
        HTTPException: If conversation not found
    """
    store = get_conversation_store()
    conversation = store.get_conversation(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return _to_response(conversation)


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    request: UpdateConversationRequest
) -> ConversationResponse:
    """
    Update a conversation's title.
    
    Args:
        conversation_id: ID of the conversation to update
        request: Update conversation request
        
    Returns:
        Updated conversation metadata
        
    Raises:
        HTTPException: If conversation not found
    """
    store = get_conversation_store()
    conversation = store.update_conversation(
        conversation_id=conversation_id,
        title=request.title
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return _to_response(conversation)


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(conversation_id: str) -> None:
    """
    Delete a conversation and clear its history.
    
    Args:
        conversation_id: ID of the conversation to delete
        
    Raises:
        HTTPException: If conversation not found
    """
    store = get_conversation_store()
    
    # Delete the conversation metadata
    deleted = store.delete_conversation(conversation_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Clear the conversation history from the agent
    # This will be handled by the agent's clear_conversation method
    from main import orders_agent
    if orders_agent:
        orders_agent.clear_conversation(conversation_id)
        logger.info(f"Cleared conversation history for: {conversation_id}")
