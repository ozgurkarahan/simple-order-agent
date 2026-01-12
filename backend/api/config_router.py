"""Configuration API router for the Orders Analytics Agent."""

import logging
from typing import Callable

import httpx
from fastapi import APIRouter, HTTPException, Depends

from api.config_models import (
    A2AConfigUpdate,
    MCPConfigUpdate,
    ConnectionTestRequest,
    A2ATestResponse,
    MCPTestResponse,
    ConfigUpdateResponse,
    ConfigResetResponse,
)
from api.config_store import ConfigStore, get_config_store

logger = logging.getLogger(__name__)

config_router = APIRouter(prefix="/api/config", tags=["config"])

# Connection test timeout in seconds
CONNECTION_TIMEOUT = 5.0

# Callback for reloading the agent (set by main.py)
_reload_agent_callback: Callable | None = None


def set_reload_agent_callback(callback: Callable) -> None:
    """Set the callback function for reloading the agent."""
    global _reload_agent_callback
    _reload_agent_callback = callback


@config_router.get("")
async def get_config(store: ConfigStore = Depends(get_config_store)) -> dict:
    """
    Get current configuration.
    
    Sensitive header values are masked in the response.
    """
    return store.load_config_masked()


@config_router.put("/a2a")
async def update_a2a_config(
    config: A2AConfigUpdate,
    store: ConfigStore = Depends(get_config_store)
) -> ConfigUpdateResponse:
    """
    Update A2A agent configuration.
    
    Saves the new URL and headers while preserving MCP configuration.
    """
    try:
        store.update_a2a_config(url=config.url, headers=config.headers)
        logger.info(f"Updated A2A config: url={config.url}")
        return ConfigUpdateResponse(status="saved")
    except Exception as e:
        logger.error(f"Failed to update A2A config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@config_router.put("/mcp")
async def update_mcp_config(
    config: MCPConfigUpdate,
    store: ConfigStore = Depends(get_config_store)
) -> ConfigUpdateResponse:
    """
    Update MCP server configuration.
    
    Saves the new name, URL, and headers while preserving A2A configuration.
    Triggers agent reload if callback is set.
    """
    try:
        store.update_mcp_config(name=config.name, url=config.url, headers=config.headers)
        logger.info(f"Updated MCP config: name={config.name}, url={config.url}")
        
        # Reload the agent with new MCP config
        reload_required = False
        if _reload_agent_callback:
            try:
                await _reload_agent_callback()
                logger.info("Agent reloaded with new MCP config")
            except Exception as e:
                logger.error(f"Failed to reload agent: {e}")
                reload_required = True
        
        return ConfigUpdateResponse(status="saved", reload_required=reload_required)
    except Exception as e:
        logger.error(f"Failed to update MCP config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@config_router.post("/a2a/test")
async def test_a2a_connection(request: ConnectionTestRequest) -> A2ATestResponse:
    """
    Test connection to an A2A agent.
    
    Attempts to fetch the agent card from the specified URL.
    Returns the agent card on success, or an error message on failure.
    """
    agent_card_url = f"{request.url.rstrip('/')}/.well-known/agent.json"
    
    try:
        async with httpx.AsyncClient(timeout=CONNECTION_TIMEOUT) as client:
            response = await client.get(agent_card_url, headers=request.headers)
            
            if response.status_code == 200:
                agent_card = response.json()
                return A2ATestResponse(success=True, agent_card=agent_card)
            else:
                return A2ATestResponse(
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text[:200]}"
                )
                
    except httpx.TimeoutException:
        return A2ATestResponse(success=False, error="Connection timeout - server did not respond within 5 seconds")
    except httpx.ConnectError as e:
        return A2ATestResponse(success=False, error=f"Connection refused: {str(e)}")
    except Exception as e:
        logger.error(f"A2A connection test failed: {e}")
        return A2ATestResponse(success=False, error=str(e))


@config_router.post("/mcp/test")
async def test_mcp_connection(request: ConnectionTestRequest) -> MCPTestResponse:
    """
    Test connection to an MCP server.
    
    Attempts to list available tools from the MCP server.
    Returns the tools list on success, or an error message on failure.
    """
    # MCP servers expose tools at various endpoints
    # Try common patterns
    tools_endpoints = [
        f"{request.url.rstrip('/')}/tools",
        f"{request.url.rstrip('/')}/mcp/tools",
        request.url.rstrip('/'),  # Some MCP servers respond with capabilities at root
    ]
    
    try:
        async with httpx.AsyncClient(timeout=CONNECTION_TIMEOUT) as client:
            for endpoint in tools_endpoints:
                try:
                    response = await client.get(endpoint, headers=request.headers)
                    if response.status_code == 200:
                        data = response.json()
                        # Try to extract tools from various response formats
                        if isinstance(data, list):
                            tools = [t.get('name', str(t)) for t in data]
                        elif isinstance(data, dict):
                            if 'tools' in data:
                                tools = [t.get('name', str(t)) for t in data['tools']]
                            elif 'capabilities' in data and 'tools' in data['capabilities']:
                                tools = list(data['capabilities']['tools'].keys())
                            else:
                                continue
                        else:
                            continue
                        
                        return MCPTestResponse(success=True, tools=tools)
                except Exception:
                    continue
            
            # If none of the endpoints worked, try a simple connectivity check
            response = await client.get(request.url.rstrip('/'), headers=request.headers)
            if response.status_code in (200, 404):
                # Server is reachable but tools endpoint not found
                return MCPTestResponse(
                    success=True, 
                    tools=[],
                    error="Server reachable but tools endpoint not found"
                )
            else:
                return MCPTestResponse(
                    success=False,
                    error=f"HTTP {response.status_code}"
                )
                
    except httpx.TimeoutException:
        return MCPTestResponse(success=False, error="Connection timeout")
    except httpx.ConnectError as e:
        return MCPTestResponse(success=False, error=f"Connection refused: {str(e)}")
    except Exception as e:
        logger.error(f"MCP connection test failed: {e}")
        return MCPTestResponse(success=False, error=str(e))


@config_router.post("/reset")
async def reset_config(store: ConfigStore = Depends(get_config_store)) -> ConfigResetResponse:
    """
    Reset configuration to defaults.
    
    Deletes the config file, causing the system to use default values.
    """
    try:
        store.reset_config()
        logger.info("Configuration reset to defaults")
        return ConfigResetResponse(
            status="reset",
            message="Configuration reset to defaults"
        )
    except Exception as e:
        logger.error(f"Failed to reset config: {e}")
        raise HTTPException(status_code=500, detail=str(e))
