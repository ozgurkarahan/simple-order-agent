"""Configuration API router for Oz's Order Management Agent."""

import json
import logging
from typing import Callable

import httpx
from fastapi import APIRouter, HTTPException, Depends

from api.config_models import (
    A2AConfigUpdate,
    MCPConfigUpdate,
    MCPServerAdd,
    MCPServerUpdate,
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


async def _try_mcp_post_protocol(
    client: httpx.AsyncClient, 
    url: str, 
    headers: dict[str, str]
) -> MCPTestResponse | None:
    """
    Try HTTP MCP protocol (JSON-RPC 2.0) with POST request.
    
    Returns MCPTestResponse if successful, None if should try other methods.
    """
    try:
        # HTTP MCP protocol uses JSON-RPC 2.0
        # For connection testing, use 'initialize' which is always supported
        mcp_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mcp-connection-test", "version": "1.0.0"}
            },
            "id": 1
        }
        
        # Ensure Accept header is set for HTTP MCP protocol
        # Some MCP servers require both application/json and text/event-stream
        mcp_headers = dict(headers)
        if "Accept" not in mcp_headers and "accept" not in mcp_headers:
            mcp_headers["Accept"] = "application/json, text/event-stream"
        
        logger.debug(f"Trying POST to {url.rstrip('/')} with headers: {mcp_headers}")
        
        # Use streaming mode for SSE responses
        async with client.stream(
            "POST",
            url.rstrip('/'),
            json=mcp_request,
            headers=mcp_headers,
            timeout=CONNECTION_TIMEOUT
        ) as response:
            logger.debug(f"POST response status: {response.status_code}, content-type: {response.headers.get('content-type')}")
            
            if response.status_code != 200:
                return None
            
            # Check if it's a streaming response (SSE)
            content_type = response.headers.get("content-type", "")
            
            if "text/event-stream" in content_type:
                # Handle SSE response - read first few events
                buffer = b""
                lines = []
                
                # Read chunks from the stream
                async for chunk in response.aiter_bytes():
                    buffer += chunk
                    # Stop after reading enough data or timeout
                    if len(buffer) > 5000:  # Limit to 5KB for connection test
                        break
                
                # Decode and split into lines
                try:
                    text = buffer.decode('utf-8')
                    lines = text.split('\n')
                except UnicodeDecodeError:
                    logger.debug("Failed to decode SSE response")
                    return MCPTestResponse(success=True, tools=[], error="Connected but response not readable")
                
                logger.debug(f"Received {len(lines)} SSE lines, first few: {lines[:5]}")
                
                # Try to parse response from SSE data
                # Format: "event: message" followed by "data: {json}"
                for i, line in enumerate(lines):
                    line = line.strip()
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])  # Remove "data: " prefix
                            logger.debug(f"Parsed SSE data: {data}")
                            
                            # Check if it's a successful response
                            if "result" in data:
                                result = data["result"]
                                # For initialize response, check capabilities
                                if isinstance(result, dict) and "capabilities" in result:
                                    # Extract tools info from capabilities
                                    caps = result.get("capabilities", {})
                                    tools_cap = caps.get("tools", {})
                                    server_info = result.get("serverInfo", {})
                                    server_name = server_info.get("name", "Unknown MCP Server")
                                    
                                    # Connection successful, return minimal info
                                    # (tools list requires a stateful session, so we just confirm connection)
                                    return MCPTestResponse(
                                        success=True,
                                        tools=[],
                                        error=f"Connected to {server_name} (tools available via stateful session)"
                                    )
                                # Handle tools/list response if it ever works
                                elif isinstance(result, dict) and "tools" in result:
                                    tools_data = result.get("tools", [])
                                    tools = [t.get("name", str(t)) for t in tools_data if isinstance(t, dict)]
                                    return MCPTestResponse(success=True, tools=tools)
                            # Handle error responses
                            elif "error" in data:
                                error_msg = data["error"].get("message", str(data["error"]))
                                logger.debug(f"MCP server returned error: {error_msg}")
                                return None
                        except json.JSONDecodeError as e:
                            logger.debug(f"Failed to parse SSE line: {line[:100]}, error: {e}")
                            continue
                
                # If we got here, no valid response found
                return MCPTestResponse(success=True, tools=[], error="Connected but response format not recognized")
            else:
                # Regular JSON response
                data = await response.aread()
                json_data = json.loads(data)
                logger.debug(f"Received JSON response: {json_data}")
                
                # Parse JSON-RPC response
                if "result" in json_data and isinstance(json_data["result"], dict):
                    tools_data = json_data["result"].get("tools", [])
                    if isinstance(tools_data, list):
                        tools = [t.get("name", str(t)) for t in tools_data if isinstance(t, dict)]
                        return MCPTestResponse(success=True, tools=tools)
                # Also handle direct tools array in result
                elif "result" in json_data and isinstance(json_data["result"], list):
                    tools = [t.get("name", str(t)) for t in json_data["result"] if isinstance(t, dict)]
                    return MCPTestResponse(success=True, tools=tools)
                # Handle error responses
                elif "error" in json_data:
                    logger.debug(f"MCP server returned error: {json_data['error']}")
                    return None
        
        return None
    except Exception as e:
        logger.debug(f"HTTP MCP protocol attempt failed: {e}")
        return None


async def _try_rest_get_endpoints(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str]
) -> MCPTestResponse | None:
    """
    Try REST-style GET endpoints for tools listing.
    
    Returns MCPTestResponse if successful, None if should try other methods.
    """
    # MCP servers expose tools at various endpoints
    # Try common patterns
    tools_endpoints = [
        f"{url.rstrip('/')}/tools",
        f"{url.rstrip('/')}/mcp/tools",
        url.rstrip('/'),  # Some MCP servers respond with capabilities at root
    ]
    
    for endpoint in tools_endpoints:
        try:
            response = await client.get(endpoint, headers=headers)
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
            elif response.status_code == 405:
                # Method not allowed - this is a POST-only endpoint
                logger.debug(f"GET {endpoint} returned 405 - server requires POST")
                return None  # Signal to try POST protocol
        except Exception as e:
            logger.debug(f"GET {endpoint} failed: {e}")
            continue
    
    return None


@config_router.post("/mcp/test")
async def test_mcp_connection(request: ConnectionTestRequest) -> MCPTestResponse:
    """
    Test connection to an MCP server.
    
    Supports both HTTP MCP protocol (POST/JSON-RPC 2.0) and REST-style GET endpoints.
    Returns the tools list on success, or an error message on failure.
    """
    try:
        async with httpx.AsyncClient(timeout=CONNECTION_TIMEOUT) as client:
            # 1. First, try HTTP MCP protocol (POST with JSON-RPC)
            # This is the standard for modern MCP servers
            result = await _try_mcp_post_protocol(client, request.url, request.headers)
            if result:
                return result
            
            # 2. Try REST-style GET endpoints
            # For backward compatibility with REST-style MCP servers
            result = await _try_rest_get_endpoints(client, request.url, request.headers)
            if result:
                return result
            
            # 3. If none of the endpoints worked, try a simple connectivity check
            response = await client.get(request.url.rstrip('/'), headers=request.headers)
            if response.status_code in (200, 404):
                # Server is reachable but tools endpoint not found
                return MCPTestResponse(
                    success=True, 
                    tools=[],
                    error="Server reachable but tools endpoint not found"
                )
            elif response.status_code == 405:
                # Server returned 405 on GET, try POST one more time with different payload
                response = await client.post(
                    request.url.rstrip('/'),
                    json={"method": "tools/list"},
                    headers=request.headers
                )
                if response.status_code == 200:
                    return MCPTestResponse(
                        success=True,
                        tools=[],
                        error="Server responded but tools format not recognized"
                    )
                return MCPTestResponse(
                    success=False,
                    error=f"HTTP 405 - Server requires POST but protocol not recognized"
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


@config_router.post("/mcp")
async def add_mcp_server(
    config: MCPServerAdd,
    store: ConfigStore = Depends(get_config_store)
) -> ConfigUpdateResponse:
    """
    Add a new MCP server.
    
    Creates a new MCP server entry with the provided configuration.
    Triggers agent reload if callback is set.
    """
    try:
        from api.config_models import MCPServerConfig
        
        # Create new server with generated ID
        new_server = MCPServerConfig(
            name=config.name,
            url=config.url,
            headers=config.headers,
            is_active=True
        )
        
        store.add_mcp_server(new_server)
        logger.info(f"Added MCP server: {new_server.name} (id={new_server.id})")
        
        # Reload the agent with new MCP config
        reload_required = False
        if _reload_agent_callback:
            try:
                await _reload_agent_callback()
                logger.info("Agent reloaded with new MCP server")
            except Exception as e:
                logger.error(f"Failed to reload agent: {e}")
                reload_required = True
        
        return ConfigUpdateResponse(
            status="added",
            reload_required=reload_required
        )
    except Exception as e:
        logger.error(f"Failed to add MCP server: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@config_router.put("/mcp/{server_id}")
async def update_mcp_server(
    server_id: str,
    updates: MCPServerUpdate,
    store: ConfigStore = Depends(get_config_store)
) -> ConfigUpdateResponse:
    """
    Update an existing MCP server.
    
    Updates the specified MCP server with the provided fields.
    Triggers agent reload if callback is set.
    """
    try:
        # Build updates dict, excluding None values
        update_dict = {}
        if updates.name is not None:
            update_dict["name"] = updates.name
        if updates.url is not None:
            update_dict["url"] = updates.url
        if updates.headers is not None:
            update_dict["headers"] = updates.headers
        if updates.is_active is not None:
            update_dict["is_active"] = updates.is_active
        
        store.update_mcp_server(server_id, update_dict)
        logger.info(f"Updated MCP server: {server_id}")
        
        # Reload the agent with updated MCP config
        reload_required = False
        if _reload_agent_callback:
            try:
                await _reload_agent_callback()
                logger.info("Agent reloaded with updated MCP server")
            except Exception as e:
                logger.error(f"Failed to reload agent: {e}")
                reload_required = True
        
        return ConfigUpdateResponse(status="updated", reload_required=reload_required)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update MCP server: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@config_router.delete("/mcp/{server_id}")
async def delete_mcp_server(
    server_id: str,
    store: ConfigStore = Depends(get_config_store)
) -> ConfigUpdateResponse:
    """
    Delete an MCP server.
    
    Removes the specified MCP server from the configuration.
    Triggers agent reload if callback is set.
    """
    try:
        store.remove_mcp_server(server_id)
        logger.info(f"Deleted MCP server: {server_id}")
        
        # Reload the agent with updated MCP config
        reload_required = False
        if _reload_agent_callback:
            try:
                await _reload_agent_callback()
                logger.info("Agent reloaded after server deletion")
            except Exception as e:
                logger.error(f"Failed to reload agent: {e}")
                reload_required = True
        
        return ConfigUpdateResponse(status="deleted", reload_required=reload_required)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete MCP server: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
