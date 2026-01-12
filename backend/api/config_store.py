"""Configuration store for JSON file persistence."""

import json
import logging
import os
from datetime import datetime
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
            mcp=MCPServerConfig(
                name="orders",
                url=settings.mcp_base_url,
                headers={
                    "client_id": settings.mcp_client_id,
                    "client_secret": settings.mcp_client_secret
                } if settings.mcp_client_id else {},
                is_active=True
            ),
            updated_at=datetime.utcnow()
        )
    
    def load_config(self) -> AppConfig:
        """
        Load configuration from file or return defaults.
        
        Returns:
            AppConfig with current configuration
        """
        if not self.config_file.exists():
            logger.info("No config file found, using defaults")
            return self._get_default_config()
        
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            # Parse the config
            config = AppConfig(
                a2a=A2AConfig(**data.get('a2a', {})),
                mcp=MCPServerConfig(**data.get('mcp', {})),
                updated_at=datetime.fromisoformat(data.get('updated_at', datetime.utcnow().isoformat()))
            )
            logger.info(f"Loaded config from {self.config_file}")
            return config
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error loading config file: {e}")
            return self._get_default_config()
    
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
            'mcp': {
                'name': config.mcp.name,
                'url': config.mcp.url,
                'headers': mask_headers(config.mcp.headers),
                'is_active': config.mcp.is_active
            },
            'updated_at': config.updated_at.isoformat()
        }
    
    def save_config(self, config: AppConfig) -> None:
        """
        Save configuration to file.
        
        Args:
            config: The configuration to save
        """
        config.updated_at = datetime.utcnow()
        
        data = {
            'a2a': {
                'url': config.a2a.url,
                'headers': config.a2a.headers,
                'is_local': config.a2a.is_local
            },
            'mcp': {
                'name': config.mcp.name,
                'url': config.mcp.url,
                'headers': config.mcp.headers,
                'is_active': config.mcp.is_active
            },
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
        
        Args:
            name: MCP server name
            url: MCP server URL
            headers: MCP headers
            
        Returns:
            Updated AppConfig
        """
        config = self.load_config()
        config.mcp = MCPServerConfig(
            name=name,
            url=url,
            headers=headers,
            is_active=True
        )
        self.save_config(config)
        return config
    
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
