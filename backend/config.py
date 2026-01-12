"""Configuration management for the Orders Analytics Agent."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Anthropic API
    anthropic_api_key: str = ""

    # MCP Server Configuration
    mcp_base_url: str = "https://agent-network-ingress-gw-0zaqgg.lr8qeg.deu-c1.cloudhub.io/orders-mcp/"
    mcp_client_id: str = ""
    mcp_client_secret: str = ""

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # CORS Configuration
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
