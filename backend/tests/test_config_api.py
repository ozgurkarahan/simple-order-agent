"""Tests for the Configuration API endpoints."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

# Import app and dependencies
from main import app
from api.config_store import ConfigStore, get_config_store, reset_config_store


@pytest.fixture(autouse=True)
def reset_store():
    """Reset config store before and after each test."""
    reset_config_store()
    yield
    reset_config_store()


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file path."""
    return tmp_path / "config.json"


@pytest.fixture
def test_client(temp_config_file):
    """Create a test client with temp config store."""
    # Create a store that uses the temp file
    test_store = ConfigStore(str(temp_config_file))
    
    # Override the dependency in the app
    app.dependency_overrides[get_config_store] = lambda: test_store
    
    client = TestClient(app)
    
    yield client, temp_config_file, test_store
    
    # Cleanup
    app.dependency_overrides.clear()


class TestConfigAPI:
    """Tests for /api/config endpoints."""

    def test_get_config_returns_defaults_when_no_file_exists(self, test_client):
        """GET /api/config should return default configuration when no config file exists."""
        client, config_file, store = test_client
        
        response = client.get("/api/config")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check A2A defaults
        assert "a2a" in data
        assert data["a2a"]["url"] == "http://localhost:8000"
        assert data["a2a"]["is_local"] is True
        
        # Check MCP servers defaults (list)
        assert "mcp_servers" in data
        assert isinstance(data["mcp_servers"], list)
        assert len(data["mcp_servers"]) > 0
        assert data["mcp_servers"][0]["name"] == "orders"
        assert "url" in data["mcp_servers"][0]
        assert data["mcp_servers"][0]["is_active"] is True

    def test_get_config_returns_saved_config(self, test_client):
        """GET /api/config should return saved configuration from file."""
        client, config_file, store = test_client
        
        # Create a config file with custom values
        config_data = {
            "a2a": {
                "url": "https://custom-agent.example.com",
                "headers": {"Authorization": "Bearer test-token"},
                "is_local": False
            },
            "mcp_servers": [
                {
                    "id": "test-id-123",
                    "name": "custom-mcp",
                    "url": "https://custom-mcp.example.com/",
                    "headers": {"client_id": "test-id"},
                    "is_active": True
                }
            ],
            "updated_at": "2025-01-12T10:00:00"
        }
        config_file.write_text(json.dumps(config_data))
        
        response = client.get("/api/config")
        
        assert response.status_code == 200
        data = response.json()
        assert data["a2a"]["url"] == "https://custom-agent.example.com"
        assert data["mcp_servers"][0]["name"] == "custom-mcp"


class TestA2AConfigAPI:
    """Tests for A2A configuration endpoints."""

    def test_update_a2a_config_saves_to_file(self, test_client):
        """PUT /api/config/a2a should save A2A configuration to file."""
        client, config_file, store = test_client
        
        new_config = {
            "url": "https://external-agent.example.com",
            "headers": {"Authorization": "Bearer new-token"}
        }
        
        response = client.put("/api/config/a2a", json=new_config)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "saved"
        
        # Verify file was written
        assert config_file.exists()
        saved_config = json.loads(config_file.read_text())
        assert saved_config["a2a"]["url"] == "https://external-agent.example.com"

    def test_update_a2a_config_validates_url(self, test_client):
        """PUT /api/config/a2a should reject invalid URLs."""
        client, config_file, store = test_client
        
        invalid_config = {
            "url": "not-a-valid-url",
            "headers": {}
        }
        
        response = client.put("/api/config/a2a", json=invalid_config)
        
        assert response.status_code == 422

    def test_a2a_connection_test_success(self, test_client):
        """POST /api/config/a2a/test should return agent card on success."""
        client, config_file, store = test_client
        
        test_request = {
            "url": "http://localhost:8000",
            "headers": {}
        }
        
        # Mock successful connection to agent
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "Test Agent",
            "description": "A test agent",
            "version": "1.0.0"
        }
        
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            response = client.post("/api/config/a2a/test", json=test_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "agent_card" in data
        assert data["agent_card"]["name"] == "Test Agent"

    def test_a2a_connection_test_failure(self, test_client):
        """POST /api/config/a2a/test should return error on connection failure."""
        client, config_file, store = test_client
        
        test_request = {
            "url": "https://unreachable-agent.example.com",
            "headers": {}
        }
        
        # Mock failed connection
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection refused")
            
            response = client.post("/api/config/a2a/test", json=test_request)
        
        assert response.status_code == 200  # Endpoint returns 200 with success=false
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    def test_a2a_connection_test_timeout(self, test_client):
        """POST /api/config/a2a/test should timeout after 5 seconds."""
        client, config_file, store = test_client
        
        test_request = {
            "url": "https://slow-agent.example.com",
            "headers": {}
        }
        
        # Mock timeout
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Request timed out")
            
            response = client.post("/api/config/a2a/test", json=test_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "timeout" in data.get("error", "").lower()


class TestMCPConfigAPI:
    """Tests for MCP configuration endpoints."""

    def test_update_mcp_config_saves_to_file(self, test_client):
        """PUT /api/config/mcp should save MCP configuration to file (updates first server)."""
        client, config_file, store = test_client
        
        new_config = {
            "name": "custom-mcp",
            "url": "https://custom-mcp.example.com/",
            "headers": {"client_id": "my-id", "client_secret": "my-secret"}
        }
        
        response = client.put("/api/config/mcp", json=new_config)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "saved"
        
        # Verify file was written
        saved_config = json.loads(config_file.read_text())
        assert saved_config["mcp_servers"][0]["name"] == "custom-mcp"
        assert saved_config["mcp_servers"][0]["url"] == "https://custom-mcp.example.com/"

    def test_update_mcp_config_validates_url(self, test_client):
        """PUT /api/config/mcp should reject invalid URLs."""
        client, config_file, store = test_client
        
        invalid_config = {
            "name": "test",
            "url": "invalid-url",
            "headers": {}
        }
        
        response = client.put("/api/config/mcp", json=invalid_config)
        
        assert response.status_code == 422

    def test_update_mcp_config_requires_name(self, test_client):
        """PUT /api/config/mcp should require a server name."""
        client, config_file, store = test_client
        
        invalid_config = {
            "url": "https://mcp.example.com/",
            "headers": {}
        }
        
        response = client.put("/api/config/mcp", json=invalid_config)
        
        assert response.status_code == 422

    def test_mcp_connection_test_success(self, test_client):
        """POST /api/config/mcp/test should return tools list on success."""
        client, config_file, store = test_client
        
        test_request = {
            "url": "https://mcp-server.example.com/",
            "headers": {"client_id": "test"}
        }
        
        # Mock successful MCP connection
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tools": [
                {"name": "get-all-orders"},
                {"name": "get-orders-by-customer-id"},
                {"name": "create-order"}
            ]
        }
        
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            response = client.post("/api/config/mcp/test", json=test_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "tools" in data
        assert len(data["tools"]) == 3

    def test_mcp_connection_test_failure(self, test_client):
        """POST /api/config/mcp/test should return error on connection failure."""
        client, config_file, store = test_client
        
        test_request = {
            "url": "https://unreachable-mcp.example.com/",
            "headers": {}
        }
        
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection refused")
            
            response = client.post("/api/config/mcp/test", json=test_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False


class TestConfigReset:
    """Tests for configuration reset endpoint."""

    def test_reset_config_deletes_file(self, test_client):
        """POST /api/config/reset should delete config file and return defaults."""
        client, config_file, store = test_client
        
        # First, create a config file
        config_data = {
            "a2a": {"url": "https://custom.com", "headers": {}, "is_local": False},
            "mcp_servers": [
                {
                    "id": "test-789",
                    "name": "custom",
                    "url": "https://mcp.com/",
                    "headers": {},
                    "is_active": True
                }
            ],
            "updated_at": "2025-01-12T10:00:00"
        }
        config_file.write_text(json.dumps(config_data))
        
        response = client.post("/api/config/reset")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "reset"
        
        # Config file should be deleted
        assert not config_file.exists()

    def test_reset_config_when_no_file_exists(self, test_client):
        """POST /api/config/reset should succeed even if no config file exists."""
        client, config_file, store = test_client
        
        response = client.post("/api/config/reset")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "reset"


class TestConfigPersistence:
    """Tests for configuration file persistence."""

    def test_config_includes_updated_at_timestamp(self, test_client):
        """Saved config should include updated_at timestamp."""
        client, config_file, store = test_client
        
        new_config = {
            "url": "https://agent.example.com",
            "headers": {}
        }
        
        client.put("/api/config/a2a", json=new_config)
        
        saved_config = json.loads(config_file.read_text())
        assert "updated_at" in saved_config
        # Timestamp should be in ISO 8601 format
        assert "T" in saved_config["updated_at"]

    def test_config_preserves_other_sections_on_update(self, test_client):
        """Updating A2A config should preserve MCP config and vice versa."""
        client, config_file, store = test_client
        
        # Set initial config
        initial_config = {
            "a2a": {"url": "https://a2a.example.com", "headers": {}, "is_local": False},
            "mcp_servers": [
                {
                    "id": "test-123",
                    "name": "orders",
                    "url": "https://mcp.example.com/",
                    "headers": {},
                    "is_active": True
                }
            ],
            "updated_at": "2025-01-12T10:00:00"
        }
        config_file.write_text(json.dumps(initial_config))
        
        # Update only A2A
        a2a_update = {"url": "https://new-a2a.example.com", "headers": {}}
        client.put("/api/config/a2a", json=a2a_update)
        
        # MCP config should be preserved
        saved_config = json.loads(config_file.read_text())
        assert saved_config["mcp_servers"][0]["url"] == "https://mcp.example.com/"
        assert saved_config["a2a"]["url"] == "https://new-a2a.example.com"

    def test_sensitive_headers_masked_in_response(self, test_client):
        """API responses should mask sensitive header values."""
        client, config_file, store = test_client
        
        config_data = {
            "a2a": {
                "url": "https://agent.example.com",
                "headers": {"Authorization": "Bearer secret-token-12345"},
                "is_local": False
            },
            "mcp_servers": [
                {
                    "id": "test-456",
                    "name": "orders",
                    "url": "https://mcp.example.com/",
                    "headers": {"client_secret": "super-secret-value"},
                    "is_active": True
                }
            ],
            "updated_at": "2025-01-12T10:00:00"
        }
        config_file.write_text(json.dumps(config_data))
        
        response = client.get("/api/config")
        data = response.json()
        
        # Sensitive headers should be masked
        assert "secret-token" not in str(data)
        assert "super-secret" not in str(data)


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_a2a_url_must_be_valid_http_or_https(self, test_client):
        """A2A URL must be http or https."""
        client, config_file, store = test_client
        
        invalid_configs = [
            {"url": "ftp://agent.example.com", "headers": {}},
            {"url": "file:///etc/passwd", "headers": {}},
            {"url": "javascript:alert(1)", "headers": {}},
        ]
        
        for config in invalid_configs:
            response = client.put("/api/config/a2a", json=config)
            assert response.status_code == 422, f"Expected 422 for URL: {config['url']}"

    def test_mcp_url_must_be_valid_http_or_https(self, test_client):
        """MCP URL must be http or https."""
        client, config_file, store = test_client
        
        invalid_config = {
            "name": "test",
            "url": "ftp://mcp.example.com",
            "headers": {}
        }
        
        response = client.put("/api/config/mcp", json=invalid_config)
        assert response.status_code == 422

    def test_headers_must_be_string_dict(self, test_client):
        """Headers must be a dictionary with string keys and values."""
        client, config_file, store = test_client
        
        invalid_config = {
            "url": "https://agent.example.com",
            "headers": {"key": 123}  # Value should be string
        }
        
        response = client.put("/api/config/a2a", json=invalid_config)
        assert response.status_code == 422


class TestMultiMCPServers:
    """Tests for multiple MCP servers functionality."""

    def test_add_mcp_server(self, test_client):
        """POST /api/config/mcp should add a new MCP server."""
        client, config_file, store = test_client
        
        new_server = {
            "name": "inventory",
            "url": "https://inventory-mcp.example.com/",
            "headers": {"api_key": "test-key"}
        }
        
        response = client.post("/api/config/mcp", json=new_server)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "added"
        
        # Verify server was added
        config_response = client.get("/api/config")
        config = config_response.json()
        assert len(config["mcp_servers"]) >= 1
        inventory_server = next((s for s in config["mcp_servers"] if s["name"] == "inventory"), None)
        assert inventory_server is not None
        assert inventory_server["url"] == "https://inventory-mcp.example.com/"

    def test_update_mcp_server(self, test_client):
        """PUT /api/config/mcp/{server_id} should update an existing MCP server."""
        client, config_file, store = test_client
        
        # First, get the default config to get server ID
        config_response = client.get("/api/config")
        config = config_response.json()
        server_id = config["mcp_servers"][0]["id"]
        
        # Update the server
        updates = {
            "name": "updated-orders",
            "is_active": False
        }
        
        response = client.put(f"/api/config/mcp/{server_id}", json=updates)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
        
        # Verify update
        config_response = client.get("/api/config")
        config = config_response.json()
        updated_server = next((s for s in config["mcp_servers"] if s["id"] == server_id), None)
        assert updated_server is not None
        assert updated_server["name"] == "updated-orders"
        assert updated_server["is_active"] is False

    def test_delete_mcp_server(self, test_client):
        """DELETE /api/config/mcp/{server_id} should delete an MCP server."""
        client, config_file, store = test_client
        
        # First, add a server to delete
        new_server = {
            "name": "temp-server",
            "url": "https://temp.example.com/",
            "headers": {}
        }
        client.post("/api/config/mcp", json=new_server)
        
        # Get the server ID
        config_response = client.get("/api/config")
        config = config_response.json()
        temp_server = next((s for s in config["mcp_servers"] if s["name"] == "temp-server"), None)
        assert temp_server is not None
        server_id = temp_server["id"]
        
        # Delete the server
        response = client.delete(f"/api/config/mcp/{server_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"
        
        # Verify deletion
        config_response = client.get("/api/config")
        config = config_response.json()
        deleted_server = next((s for s in config["mcp_servers"] if s["id"] == server_id), None)
        assert deleted_server is None

    def test_update_nonexistent_server_returns_404(self, test_client):
        """Updating a non-existent server should return 404."""
        client, config_file, store = test_client
        
        updates = {"name": "new-name"}
        response = client.put("/api/config/mcp/nonexistent-id", json=updates)
        
        assert response.status_code == 404

    def test_delete_nonexistent_server_returns_404(self, test_client):
        """Deleting a non-existent server should return 404."""
        client, config_file, store = test_client
        
        response = client.delete("/api/config/mcp/nonexistent-id")
        
        assert response.status_code == 404

    def test_migration_from_single_to_multi_server(self, test_client):
        """Old single-server config should be migrated to list format."""
        client, config_file, store = test_client
        
        # Create old-style config with single 'mcp' field
        old_config = {
            "a2a": {"url": "http://localhost:8000", "headers": {}, "is_local": True},
            "mcp": {
                "name": "legacy-orders",
                "url": "https://legacy-mcp.example.com/",
                "headers": {"key": "value"},
                "is_active": True
            },
            "updated_at": "2025-01-12T10:00:00"
        }
        config_file.write_text(json.dumps(old_config))
        
        # Load config (should trigger migration)
        response = client.get("/api/config")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have mcp_servers list instead of mcp
        assert "mcp_servers" in data
        assert isinstance(data["mcp_servers"], list)
        assert len(data["mcp_servers"]) == 1
        assert data["mcp_servers"][0]["name"] == "legacy-orders"
        assert data["mcp_servers"][0]["url"] == "https://legacy-mcp.example.com/"
        assert "id" in data["mcp_servers"][0]  # Should have generated ID

    def test_multiple_active_servers(self, test_client):
        """System should support multiple active MCP servers simultaneously."""
        client, config_file, store = test_client
        
        # Add multiple servers
        servers = [
            {"name": "orders", "url": "https://orders.example.com/", "headers": {}},
            {"name": "inventory", "url": "https://inventory.example.com/", "headers": {}},
            {"name": "shipping", "url": "https://shipping.example.com/", "headers": {}},
        ]
        
        for server in servers[1:]:  # First one is already there by default
            client.post("/api/config/mcp", json=server)
        
        # Verify all servers are present and active
        config_response = client.get("/api/config")
        config = config_response.json()
        
        assert len(config["mcp_servers"]) >= 3
        active_servers = [s for s in config["mcp_servers"] if s["is_active"]]
        assert len(active_servers) >= 3
