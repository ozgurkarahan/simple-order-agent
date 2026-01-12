"""Configuration data models for the Orders Analytics Agent."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_validator
import re


def validate_http_url(url: str) -> str:
    """Validate that URL is http or https."""
    if not re.match(r'^https?://', url, re.IGNORECASE):
        raise ValueError('URL must start with http:// or https://')
    return url


class A2AConfig(BaseModel):
    """A2A agent connection configuration."""
    
    url: Annotated[str, Field(default="http://localhost:8000")]
    headers: dict[str, str] = Field(default_factory=dict)
    is_local: bool = True
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        return validate_http_url(v)
    
    @field_validator('headers')
    @classmethod
    def validate_headers(cls, v: dict) -> dict:
        for key, value in v.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError('Headers must be string key-value pairs')
        return v


class A2AConfigUpdate(BaseModel):
    """Request model for updating A2A configuration."""
    
    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        return validate_http_url(v)
    
    @field_validator('headers')
    @classmethod
    def validate_headers(cls, v: dict) -> dict:
        for key, value in v.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError('Headers must be string key-value pairs')
        return v


class MCPServerConfig(BaseModel):
    """MCP server configuration."""
    
    name: str = "orders"
    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    is_active: bool = True
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        return validate_http_url(v)
    
    @field_validator('headers')
    @classmethod
    def validate_headers(cls, v: dict) -> dict:
        for key, value in v.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError('Headers must be string key-value pairs')
        return v


class MCPConfigUpdate(BaseModel):
    """Request model for updating MCP configuration."""
    
    name: str
    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        return validate_http_url(v)
    
    @field_validator('headers')
    @classmethod
    def validate_headers(cls, v: dict) -> dict:
        for key, value in v.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError('Headers must be string key-value pairs')
        return v


class AppConfig(BaseModel):
    """Complete application configuration."""
    
    a2a: A2AConfig
    mcp: MCPServerConfig
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ConnectionTestRequest(BaseModel):
    """Request model for testing connections."""
    
    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        return validate_http_url(v)


class A2ATestResponse(BaseModel):
    """Response model for A2A connection test."""
    
    success: bool
    agent_card: dict | None = None
    error: str | None = None


class MCPTestResponse(BaseModel):
    """Response model for MCP connection test."""
    
    success: bool
    tools: list[str] | None = None
    error: str | None = None


class ConfigUpdateResponse(BaseModel):
    """Response model for config updates."""
    
    status: str
    connection_test: str | None = None
    reload_required: bool = False


class ConfigResetResponse(BaseModel):
    """Response model for config reset."""
    
    status: str
    message: str
