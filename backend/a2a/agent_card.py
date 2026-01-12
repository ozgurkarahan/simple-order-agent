"""Agent Card configuration for A2A discovery."""

from functools import lru_cache

from .models import AgentCard, AgentCapabilities, AuthConfig, AuthType, Skill


@lru_cache
def get_agent_card() -> AgentCard:
    """
    Get the Agent Card for A2A discovery.

    The Agent Card describes this agent's capabilities and is served
    at /.well-known/agent.json for discovery by other agents.
    """
    return AgentCard(
        name="Orders Analytics Agent",
        description="AI-powered agent for querying and analyzing order data. "
        "Supports natural language queries for order analytics, "
        "customer order lookup, and order creation.",
        version="1.0.0",
        url="http://localhost:8000",  # Updated dynamically in production
        documentation_url="http://localhost:8000/docs",
        capabilities=AgentCapabilities(
            streaming=True,
            push_notifications=False,
            state_transition_history=True,
        ),
        skills=[
            Skill(
                id="get_all_orders",
                name="Get All Orders",
                description="Retrieve all customer orders from the system. "
                "Returns comprehensive order data including product name, amount, size, and order date.",
                tags=["orders", "query", "analytics"],
                examples=[
                    "Show me all orders",
                    "List all orders in the system",
                    "What orders do we have?",
                    "Give me an overview of all orders",
                ],
            ),
            Skill(
                id="get_orders_by_customer_id",
                name="Get Customer Orders",
                description="Get a customer's complete order history by their customer ID. "
                "Returns orders including product name, quantity, price, size, and order date.",
                tags=["orders", "customer", "lookup"],
                examples=[
                    "Show orders for customer CUST001",
                    "What did customer C12345 order?",
                    "Get order history for customer ABC",
                    "Find orders by customer ID XYZ",
                ],
            ),
            Skill(
                id="create_order",
                name="Create Order",
                description="Create a new order record in the system. "
                "Requires customer ID, customer name, product name, price, and order date.",
                tags=["orders", "create", "transaction"],
                examples=[
                    "Create an order for customer CUST001 named John Doe for a laptop at $999",
                    "Place a new order for product Widget X",
                    "Add an order for customer ABC",
                ],
            ),
            Skill(
                id="analyze_orders",
                name="Analyze Orders",
                description="Perform analytics queries on order data. Calculate totals, "
                "averages, trends, and provide insights from order data.",
                tags=["analytics", "insights", "reporting"],
                examples=[
                    "What's our total revenue?",
                    "How many orders do we have?",
                    "What's the average order value?",
                    "Summarize our order data",
                ],
            ),
        ],
        authentication=AuthConfig(
            type=AuthType.BEARER,
        ),
        default_input_modes=["text"],
        default_output_modes=["text"],
    )
