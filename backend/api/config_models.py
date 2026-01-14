"""Configuration data models for Oz's Order Management Agent."""

from datetime import datetime, timezone
import re
import uuid

from pydantic import BaseModel, Field, field_validator


def validate_http_url(url: str) -> str:
    """Validate that URL is http or https."""
    if not re.match(r'^https?://', url, re.IGNORECASE):
        raise ValueError('URL must start with http:// or https://')
    return url


def validate_string_headers(headers: dict) -> dict:
    """Validate that headers are string key-value pairs."""
    for key, value in headers.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError('Headers must be string key-value pairs')
    return headers


class BaseConfigModel(BaseModel):
    """Base model with common URL and headers validation."""

    url: str
    headers: dict[str, str] = Field(default_factory=dict)

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        return validate_http_url(v)

    @field_validator('headers')
    @classmethod
    def validate_headers(cls, v: dict) -> dict:
        return validate_string_headers(v)


class A2AConfig(BaseConfigModel):
    """A2A agent connection configuration."""

    url: str = "http://localhost:8000"
    is_local: bool = True


class A2AConfigUpdate(BaseConfigModel):
    """Request model for updating A2A configuration."""
    pass


class MCPServerConfig(BaseConfigModel):
    """MCP server configuration."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "orders"
    is_active: bool = True


class MCPConfigUpdate(BaseConfigModel):
    """Request model for updating MCP configuration."""

    name: str


class MCPServerAdd(BaseConfigModel):
    """Request model for adding new MCP server."""

    name: str


class MCPServerUpdate(BaseModel):
    """Request model for updating existing MCP server."""

    name: str | None = None
    url: str | None = None
    headers: dict[str, str] | None = None
    is_active: bool | None = None


class AppConfig(BaseModel):
    """Complete application configuration."""

    a2a: A2AConfig
    mcp_servers: list[MCPServerConfig] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConnectionTestRequest(BaseConfigModel):
    """Request model for testing connections."""
    pass


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
