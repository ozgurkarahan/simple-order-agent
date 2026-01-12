"""Pytest configuration and fixtures."""

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client."""
    client = AsyncMock()

    # Mock responses
    client.list_orders.return_value = [
        {
            "order_id": "ORD-001",
            "customer_id": "CUST-001",
            "status": "pending",
            "total": 150.00,
            "created_at": "2024-01-15T10:00:00Z",
        },
        {
            "order_id": "ORD-002",
            "customer_id": "CUST-002",
            "status": "shipped",
            "total": 275.50,
            "created_at": "2024-01-14T15:30:00Z",
        },
    ]

    client.get_order.return_value = {
        "order_id": "ORD-001",
        "customer_id": "CUST-001",
        "status": "pending",
        "total": 150.00,
        "items": [
            {"product_id": "PROD-001", "quantity": 2, "price": 50.00},
            {"product_id": "PROD-002", "quantity": 1, "price": 50.00},
        ],
        "shipping_address": {
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip": "12345",
            "country": "USA",
        },
        "created_at": "2024-01-15T10:00:00Z",
    }

    client.create_order.return_value = {
        "order_id": "ORD-003",
        "customer_id": "CUST-001",
        "status": "pending",
        "total": 100.00,
        "items": [
            {"product_id": "PROD-001", "quantity": 2, "price": 50.00},
        ],
        "created_at": "2024-01-16T12:00:00Z",
    }

    client.call_tool.return_value = {"success": True}
    client.close = AsyncMock()

    return client


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client."""
    client = MagicMock()

    # Create a mock response
    mock_response = MagicMock()
    mock_response.content = [MagicMock(type="text", text="Here are the orders you requested.")]
    mock_response.stop_reason = "end_turn"

    client.messages.create = AsyncMock(return_value=mock_response)

    return client


@pytest.fixture
def sample_orders():
    """Sample order data for testing."""
    return [
        {
            "order_id": "ORD-001",
            "customer_id": "CUST-001",
            "status": "pending",
            "total": 150.00,
            "items": [
                {"product_id": "PROD-001", "quantity": 2, "price": 50.00},
                {"product_id": "PROD-002", "quantity": 1, "price": 50.00},
            ],
            "created_at": "2024-01-15T10:00:00Z",
        },
        {
            "order_id": "ORD-002",
            "customer_id": "CUST-002",
            "status": "shipped",
            "total": 275.50,
            "items": [
                {"product_id": "PROD-003", "quantity": 1, "price": 275.50},
            ],
            "created_at": "2024-01-14T15:30:00Z",
        },
        {
            "order_id": "ORD-003",
            "customer_id": "CUST-001",
            "status": "delivered",
            "total": 89.99,
            "items": [
                {"product_id": "PROD-004", "quantity": 1, "price": 89.99},
            ],
            "created_at": "2024-01-10T09:15:00Z",
        },
    ]


@pytest.fixture
def agent_tools():
    """
    Tool definitions for testing.

    These mirror the tools exposed by the Orders MCP server.
    Used for unit tests and evals that don't need to hit the actual MCP server.
    """
    return [
        {
            "name": "get_all_orders",
            "description": "Retrieve all customer orders from the system.",
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "get_orders_by_customer_id",
            "description": "Get a customer's complete order history by their customer ID.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "The unique identifier of the customer",
                    },
                },
                "required": ["customer_id"],
            },
        },
        {
            "name": "create_order",
            "description": "Create a new order record in the system.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "Customer ID"},
                    "customer_name": {"type": "string", "description": "Customer name"},
                    "product_name": {"type": "string", "description": "Product name"},
                    "price": {"type": "number", "description": "Price"},
                    "order_date": {"type": "string", "description": "Order date ISO 8601"},
                },
                "required": ["customer_id", "customer_name", "product_name", "price", "order_date"],
            },
        },
    ]


# Also export as a module-level constant for non-fixture usage (e.g., evals)
TOOLS = [
    {
        "name": "get_all_orders",
        "description": "Retrieve all customer orders from the system.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_orders_by_customer_id",
        "description": "Get a customer's complete order history by their customer ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "The unique identifier of the customer",
                },
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "create_order",
        "description": "Create a new order record in the system.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Customer ID"},
                "customer_name": {"type": "string", "description": "Customer name"},
                "product_name": {"type": "string", "description": "Product name"},
                "price": {"type": "number", "description": "Price"},
                "order_date": {"type": "string", "description": "Order date ISO 8601"},
            },
            "required": ["customer_id", "customer_name", "product_name", "price", "order_date"],
        },
    },
]


@pytest.fixture
def sample_agent_card():
    """Sample agent card for testing."""
    return {
        "name": "Orders Analytics Agent",
        "description": "AI-powered agent for querying and analyzing order data.",
        "version": "1.0.0",
        "url": "http://localhost:8000",
        "capabilities": {
            "streaming": True,
            "pushNotifications": False,
            "stateTransitionHistory": True,
        },
        "skills": [
            {
                "id": "list_orders",
                "name": "List Orders",
                "description": "Query and filter orders",
                "tags": ["orders", "query"],
                "examples": ["Show me all orders"],
            },
        ],
        "authentication": {"type": "bearer"},
        "defaultInputModes": ["text"],
        "defaultOutputModes": ["text"],
    }
