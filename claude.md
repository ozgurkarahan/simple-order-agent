# Orders Analytics Agent

## Project Overview

This is a test project for the Claude Agent SDK that connects to an Orders MCP server and exposes itself as an A2A-compliant agent. The project demonstrates:

- **MCP Integration**: Connecting to external tools via Model Context Protocol
- **A2A Protocol**: Exposing the agent for discovery and interaction by other agents
- **Agent Evals**: Comprehensive testing framework for AI agent behavior

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   Web Dashboard │     │  Other A2A      │
│   (Next.js)     │     │  Agents         │
└────────┬────────┘     └────────┬────────┘
         │                       │
         │ REST API              │ A2A Protocol
         │                       │
         ▼                       ▼
┌─────────────────────────────────────────┐
│           FastAPI Backend               │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │ Chat API    │  │ A2A Endpoints   │   │
│  └──────┬──────┘  └────────┬────────┘   │
│         │                  │            │
│         ▼                  ▼            │
│  ┌──────────────────────────────────┐   │
│  │     Claude Agent (Anthropic)     │   │
│  └──────────────┬───────────────────┘   │
│                 │                       │
│                 ▼                       │
│  ┌──────────────────────────────────┐   │
│  │         MCP Client               │   │
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
- `mcp/client.py` - MCP client for Orders server communication
- `a2a/` - A2A protocol implementation (models, router, task manager)
- `tests/` - Unit tests and agent evals

### Frontend (`/frontend`)

- Next.js 14 application with App Router
- Chat interface for natural language interaction
- Analytics dashboard for order insights
- Agent Card display component

## MCP Server Details

- **URL**: `https://agent-network-ingress-gw-0zaqgg.lr8qeg.deu-c1.cloudhub.io/orders-mcp/`
- **Auth**: Custom headers (`client_id`, `client_secret`)
- **Operations**: list_orders, get_order, create_order

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

Backend requires:
- `ANTHROPIC_API_KEY` - Claude API key
- `MCP_CLIENT_ID` - Orders MCP server client ID
- `MCP_CLIENT_SECRET` - Orders MCP server client secret

## Code Style

- Python: Use type hints, follow PEP 8, use async/await for I/O
- TypeScript: Strict mode, use React hooks, prefer functional components
- Tests: Descriptive test names, use fixtures, aim for >80% coverage
