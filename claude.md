# Oz's Order Management Agent

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
- `api/` - Configuration API (config_models.py, config_store.py, config_router.py)
- `data/config.json` - Runtime configuration file (gitignored)
- `tests/` - Unit tests and agent evals

### Frontend (`/frontend`)

- Next.js 14 application with App Router
- Chat interface (`/`) for natural language interaction
- Settings page (`/settings`) for A2A and MCP configuration
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

### Quick Start (Recommended)

```bash
# First time setup
npm install              # Install concurrently
cd frontend && npm install && cd ..
cd backend && cp .env.example .env && cd ..

# Run both services
npm start                # Runs backend + frontend with color-coded output
```

### Individual Services

```bash
# Backend only
npm run backend          # or: cd backend && uvicorn main:app --reload

# Frontend only
npm run frontend         # or: cd frontend && npm run dev
```

### Testing

```bash
# Run tests
cd backend
pytest

# Run evals
cd backend
pytest tests/evals/

# Run with coverage
cd backend
pytest --cov=. --cov-report=html
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

- **Migrated to ClaudeSDKClient for Stateful Conversations**:
  - Replaced stateless `query()` function with `ClaudeSDKClient` class
  - Enables true multi-turn conversation support with automatic context management
  - Added client lifecycle management with per-conversation instances
  - Added `clear_conversation()` and `clear_all_conversations()` methods
  - Conversation history now properly maintained by Claude Agent SDK
  - Fixed bug where conversation history was collected but never used
- **Agent Card Display Feature**: Full expandable agent card display in Settings page
  - Created `AgentCardDisplay.tsx` component with collapsible UI
  - Updated TypeScript types for full `AgentCard` structure with authentication and documentation fields
  - Integrated agent card state management in Settings page
  - Shows comprehensive agent information: skills, capabilities, authentication, links
  - Smooth expand/collapse animations with Lucide React icons
  - Automatically fetches and displays agent card when testing A2A connections
- **Added Simple Startup Script**: Single `npm start` command runs both services with color-coded output
  - Uses `concurrently` for parallel execution
  - Cross-platform compatible (Mac, Linux, Windows)
  - Direct venv path usage (no manual activation needed)
  - Root-level `package.json` with convenient scripts
- Migrated to Claude Agent SDK with external MCP server via `.mcp.json`
- Removed custom MCP client (SDK handles MCP communication natively)
- Simplified UI to chat-only interface (removed Analytics and Orders table views)
- Full-screen conversational experience with agent status header
- Quick action buttons: "Show all orders", "Search customer", "Revenue summary", "Create order"
- **Added Configuration Feature**: Settings page for dynamic A2A and MCP configuration
  - Configure A2A agent URLs and custom headers
  - Configure MCP server URLs and authentication headers
  - Test connections before saving
  - Hot-reload agent with new MCP settings (no restart required)
  - JSON file persistence (`backend/data/config.json`)
- **Renamed Agent**: Now "Oz's Order Management Agent"
- **Claude Desktop UI Redesign**:
  - Warm cream color palette with coral/terracotta accents
  - Libre Baskerville serif font for headings
  - Collapsible ToolAccordion for MCP tool results with "M" badge
  - ConnectorsPopover showing connected MCP servers
  - InputToolbar with pill-shaped input and model badge
  - Minimal header with status indicators
