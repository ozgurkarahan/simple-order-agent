# Orders Analytics Agent

## Project Overview

This is a test project for the Claude Agent SDK that connects to an Orders MCP server and exposes itself as an A2A-compliant agent. The project demonstrates:

- **MCP Integration**: Connecting to external tools via Model Context Protocol
- **A2A Protocol**: Exposing the agent for discovery and interaction by other agents
- **Agent Evals**: Comprehensive testing framework for AI agent behavior

## Architecture

```
┌─────────────────────────────────────────┐
│         Chat Interface (Next.js)        │
│    Full-screen conversational UI        │
└────────────────┬────────────────────────┘
                 │ REST API / SSE
                 ▼
┌─────────────────────────────────────────┐
│           FastAPI Backend               │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │ Chat API    │  │ A2A Endpoints   │   │
│  └──────┬──────┘  └────────┬────────┘   │
│         │                  │            │
│         ▼                  ▼            │
│  ┌──────────────────────────────────┐   │
│  │   Claude Agent SDK + .mcp.json   │   │
│  └──────────────┬───────────────────┘   │
└─────────────────┼───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│         Orders MCP Server               │
│  (External - MuleSoft CloudHub)         │
└─────────────────────────────────────────┘
```

## Key Components

### Backend (`/backend`)

- `main.py` - FastAPI application entry point
- `agent/orders_agent.py` - Claude agent configuration with MCP tools
- `.mcp.json` - MCP server configuration for Claude Agent SDK
- `a2a/` - A2A protocol implementation (models, router, task manager)
- `tests/` - Unit tests and agent evals

### Frontend (`/frontend`)

- Next.js 14 application with App Router
- Single-page chat interface for natural language interaction
- Real-time streaming responses
- Quick action buttons for common queries

## MCP Server Details

- **URL**: `https://agent-network-ingress-gw-0zaqgg.lr8qeg.deu-c1.cloudhub.io/orders-mcp/`
- **Auth**: Custom headers (`client_id`, `client_secret`)
- **Tools**:
  - `get-all-orders` - Retrieve all orders
  - `get-orders-by-customer-id` - Get orders for a specific customer
  - `create-order` - Create a new order

## Development Commands

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Run tests
cd backend
pytest

# Run evals
cd backend
pytest tests/evals/
```

## Environment Variables

Backend requires (in `backend/.env`):
- `ANTHROPIC_API_KEY` - Claude API key
- `MCP_CLIENT_ID` - Orders MCP server client ID
- `MCP_CLIENT_SECRET` - Orders MCP server client secret

Note: MCP server URL is configured in `backend/.mcp.json`

## Code Style

- Python: Use type hints, follow PEP 8, use async/await for I/O
- TypeScript: Strict mode, use React hooks, prefer functional components
- Tests: Descriptive test names, use fixtures, aim for >80% coverage

## Recent Changes

- Migrated to Claude Agent SDK with external MCP server via `.mcp.json`
- Removed custom MCP client (SDK handles MCP communication natively)
- Simplified UI to chat-only interface (removed Analytics and Orders table views)
- Full-screen conversational experience with agent status header
- Quick action buttons: "Show all orders", "Search customer", "Revenue summary", "Create order"
