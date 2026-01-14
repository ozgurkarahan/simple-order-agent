"""Configuration store for JSON file persistence."""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from functools import lru_cache

from api.config_models import A2AConfig, MCPServerConfig, AppConfig
from config import get_settings

logger = logging.getLogger(__name__)

# Sensitive header keys that should be masked in responses
SENSITIVE_KEYS = {'authorization', 'token', 'secret', 'password', 'api_key', 'apikey', 'client_secret'}


def mask_sensitive_value(value: str) -> str:
    """Mask a sensitive value, showing only first and last 2 chars."""
    if len(value) <= 6:
        return '••••••'
    return value[:2] + '••••••' + value[-2:]


def mask_headers(headers: dict[str, str]) -> dict[str, str]:
    """Mask sensitive header values."""
    masked = {}
    for key, value in headers.items():
        key_lower = key.lower().replace('-', '_').replace(' ', '_')
        if any(sensitive in key_lower for sensitive in SENSITIVE_KEYS):
            masked[key] = mask_sensitive_value(value)
        else:
            masked[key] = value
    return masked


class ConfigStore:
    """Handles reading/writing configuration to JSON file."""
    
    def __init__(self, config_file_path: str | None = None):
        """
        Initialize the config store.
        
        Args:
            config_file_path: Path to the config file. If None, uses default.
        """
        if config_file_path:
            self.config_file = Path(config_file_path)
        else:
            # Check for environment variable override (useful for testing)
            env_path = os.environ.get('CONFIG_FILE_PATH')
            if env_path:
                self.config_file = Path(env_path)
            else:
                # Default path
                self.config_file = Path(__file__).parent.parent / 'data' / 'config.json'
        
        # Ensure parent directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _get_default_config(self) -> AppConfig:
        """Get default configuration."""
        settings = get_settings()
        return AppConfig(
            a2a=A2AConfig(
                url="http://localhost:8000",
                headers={},
                is_local=True
            ),
            mcp_servers=[
                MCPServerConfig(
                    name="orders",
                    url=settings.mcp_base_url,
                    headers={
                        "client_id": settings.mcp_client_id,
                        "client_secret": settings.mcp_client_secret
                    } if settings.mcp_client_id else {},
                    is_active=True
                )
            ],
            updated_at=datetime.now(timezone.utc)
        )
    
    def _migrate_single_to_list(self, data: dict) -> dict:
        """Migrate old single-server config to list format."""
        if "mcp" in data and "mcp_servers" not in data:
            old_mcp = data.pop("mcp")
            # Ensure the old config has an ID
            if "id" not in old_mcp:
                old_mcp["id"] = str(uuid.uuid4())
            data["mcp_servers"] = [old_mcp]
            logger.info("Migrated old single-server MCP config to list format")
        return data
    
    def load_config(self) -> AppConfig:
        """
        Load configuration from file or return defaults.
        
        Returns:
            AppConfig with current configuration
        """
        if not self.config_file.exists():
            logger.info("No config file found, using defaults")
            default_config = self._get_default_config()
            # Save defaults to disk so IDs are consistent across calls
            self.save_config(default_config)
            return default_config
        
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            # Migration: convert old single-server format to list
            data = self._migrate_single_to_list(data)
            
            # Parse the config
            config = AppConfig(
                a2a=A2AConfig(**data.get('a2a', {})),
                mcp_servers=[MCPServerConfig(**server) for server in data.get('mcp_servers', [])],
                updated_at=datetime.fromisoformat(data.get('updated_at', datetime.now(timezone.utc).isoformat()))
            )
            logger.info(f"Loaded config from {self.config_file}")
            return config
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error loading config file: {e}")
            default_config = self._get_default_config()
            # Save defaults to replace corrupted file
            self.save_config(default_config)
            return default_config
    
    def load_config_masked(self) -> dict:
        """
        Load configuration with sensitive headers masked.
        
        Returns:
            Config dict with masked sensitive values
        """
        config = self.load_config()
        return {
            'a2a': {
                'url': config.a2a.url,
                'headers': mask_headers(config.a2a.headers),
                'is_local': config.a2a.is_local
            },
            'mcp_servers': [
                {
                    'id': server.id,
                    'name': server.name,
                    'url': server.url,
                    'headers': mask_headers(server.headers),
                    'is_active': server.is_active
                }
                for server in config.mcp_servers
            ],
            'updated_at': config.updated_at.isoformat()
        }
    
    def save_config(self, config: AppConfig) -> None:
        """
        Save configuration to file.
        
        Args:
            config: The configuration to save
        """
        config.updated_at = datetime.now(timezone.utc)
        
        data = {
            'a2a': {
                'url': config.a2a.url,
                'headers': config.a2a.headers,
                'is_local': config.a2a.is_local
            },
            'mcp_servers': [
                {
                    'id': server.id,
                    'name': server.name,
                    'url': server.url,
                    'headers': server.headers,
                    'is_active': server.is_active
                }
                for server in config.mcp_servers
            ],
            'updated_at': config.updated_at.isoformat()
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved config to {self.config_file}")
    
    def update_a2a_config(self, url: str, headers: dict[str, str]) -> AppConfig:
        """
        Update A2A configuration while preserving MCP config.
        
        Args:
            url: New A2A agent URL
            headers: New A2A headers
            
        Returns:
            Updated AppConfig
        """
        config = self.load_config()
        config.a2a = A2AConfig(
            url=url,
            headers=headers,
            is_local=url.startswith('http://localhost')
        )
        self.save_config(config)
        return config
    
    def update_mcp_config(self, name: str, url: str, headers: dict[str, str]) -> AppConfig:
        """
        Update MCP configuration while preserving A2A config.
        (Legacy method - updates the first MCP server or adds a new one)
        
        Args:
            name: MCP server name
            url: MCP server URL
            headers: MCP headers
            
        Returns:
            Updated AppConfig
        """
        config = self.load_config()
        if config.mcp_servers:
            # Update the first server
            config.mcp_servers[0] = MCPServerConfig(
                id=config.mcp_servers[0].id,
                name=name,
                url=url,
                headers=headers,
                is_active=True
            )
        else:
            # Add new server if none exists
            config.mcp_servers = [
                MCPServerConfig(
                    name=name,
                    url=url,
                    headers=headers,
                    is_active=True
                )
            ]
        self.save_config(config)
        return config
    
    def add_mcp_server(self, server: MCPServerConfig) -> AppConfig:
        """
        Add a new MCP server.
        
        Args:
            server: MCP server configuration to add
            
        Returns:
            Updated AppConfig
        """
        config = self.load_config()
        config.mcp_servers.append(server)
        self.save_config(config)
        logger.info(f"Added MCP server: {server.name} (id={server.id})")
        return config
    
    def remove_mcp_server(self, server_id: str) -> AppConfig:
        """
        Remove an MCP server by ID.
        
        Args:
            server_id: ID of the server to remove
            
        Returns:
            Updated AppConfig
            
        Raises:
            ValueError: If server not found
        """
        config = self.load_config()
        original_count = len(config.mcp_servers)
        config.mcp_servers = [s for s in config.mcp_servers if s.id != server_id]
        
        if len(config.mcp_servers) == original_count:
            raise ValueError(f"MCP server with id '{server_id}' not found")
        
        self.save_config(config)
        logger.info(f"Removed MCP server: {server_id}")
        return config
    
    def update_mcp_server(self, server_id: str, updates: dict) -> AppConfig:
        """
        Update an existing MCP server.
        
        Args:
            server_id: ID of the server to update
            updates: Dictionary of fields to update
            
        Returns:
            Updated AppConfig
            
        Raises:
            ValueError: If server not found
        """
        config = self.load_config()
        server = self.get_mcp_server(server_id)
        
        if not server:
            raise ValueError(f"MCP server with id '{server_id}' not found")
        
        # Find and update the server
        for i, s in enumerate(config.mcp_servers):
            if s.id == server_id:
                # Create updated server with merged values
                server_dict = s.model_dump()
                server_dict.update({k: v for k, v in updates.items() if v is not None})
                config.mcp_servers[i] = MCPServerConfig(**server_dict)
                break
        
        self.save_config(config)
        logger.info(f"Updated MCP server: {server_id}")
        return config
    
    def get_mcp_server(self, server_id: str) -> MCPServerConfig | None:
        """
        Get an MCP server by ID.
        
        Args:
            server_id: ID of the server to retrieve
            
        Returns:
            MCPServerConfig if found, None otherwise
        """
        config = self.load_config()
        for server in config.mcp_servers:
            if server.id == server_id:
                return server
        return None
    
    def reset_config(self) -> None:
        """Delete config file to reset to defaults."""
        if self.config_file.exists():
            self.config_file.unlink()
            logger.info(f"Deleted config file: {self.config_file}")
        else:
            logger.info("No config file to delete")


# Global instance
_config_store: ConfigStore | None = None


def get_config_store() -> ConfigStore:
    """Get the global config store instance."""
    global _config_store
    if _config_store is None:
        _config_store = ConfigStore()
    return _config_store


def reset_config_store() -> None:
    """Reset the global config store instance (useful for testing)."""
    global _config_store
    _config_store = None
