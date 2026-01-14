# Oz's Order Management Agent

A **learning project** to explore the integration of a MuleSoft MCP server with the Claude Agent SDK. This project serves as a hands-on sandbox for:

- Testing MCP protocol implementation with MuleSoft CloudHub
- Building and evaluating AI agents with Anthropic's Claude
- Learning agent evaluation (evals) best practices
- Experimenting with tool definitions and A2A protocol

## Features

- **Natural Language Chat**: Ask questions about orders in plain English
- **Real-time Streaming**: See responses as they're generated
- **Multi-Conversation Support**: Create and manage multiple separate conversation threads
- **A2A Protocol Support**: Discoverable and callable by other AI agents
- **MCP Integration**: Connects to external Orders MCP server
- **Dynamic Configuration**: Configure A2A agents and MCP servers via Settings page
- **Agent Card Display**: View comprehensive agent details including skills, capabilities, and authentication
- **Comprehensive Testing**: Unit tests and agent evals included
- **Claude Desktop UI**: Warm cream theme, serif typography, minimal design inspired by Claude desktop
- **Collapsible Tool Results**: Accordion-style display for MCP tool outputs with formatted tables
- **MCP Connectors Display**: Visual indicator of connected MCP servers in input toolbar

## What You'll Learn

| Topic | Description |
|-------|-------------|
| **MCP Protocol** | How to connect Claude to external APIs via Model Context Protocol |
| **Agent Tools** | Defining tools, input schemas, and handling tool responses |
| **Agent Evals** | Writing evaluation datasets to test tool selection accuracy |
| **A2A Protocol** | Making your agent discoverable by other AI agents |
| **Streaming** | Implementing SSE for real-time agent responses |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Anthropic API key
- MCP server credentials

### Simple Startup (Recommended)

Run both backend and frontend with a single command:

```bash
# First time setup
npm install              # Install concurrently
cd frontend && npm install && cd ..  # Or: npm run setup

# Configure backend environment
cd backend
cp .env.example .env
# Edit .env with your API keys
cd ..

# Run both services
npm start
```

Both services will run with color-coded output (green for backend, blue for frontend). Press `Ctrl+C` to stop both.

- Backend: [http://localhost:8000](http://localhost:8000)
- Frontend: [http://localhost:3001](http://localhost:3001) (or 3000 if available)
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Manual Setup (Alternative)

<details>
<summary>Click to expand manual setup instructions</summary>

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the server
uvicorn main:app --reload
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to access the chat interface.

</details>

## Using Multiple Conversations

The dashboard supports multiple conversation threads to help you organize different tasks:

### Creating Conversations

1. Click the **sidebar toggle button** (top-left corner) to open the conversation list
2. Click **"New Conversation"** to start a fresh conversation
3. Your first message automatically becomes the conversation title (truncated to 50 characters)

### Managing Conversations

- **Switch conversations**: Click any conversation in the sidebar to activate it
- **Rename conversations**: Click the edit icon (✏️) next to a conversation, type the new name, and press Enter or click the checkmark
- **Delete conversations**: Click the trash icon (🗑️) and confirm deletion
- **View metadata**: Each conversation shows when it was last updated and the message count

### Keyboard & UI Tips

- The **active conversation** is highlighted with a blue accent
- Conversations are **sorted by most recent update** at the top
- The sidebar **auto-hides on mobile** devices and can be toggled with the button
- **Switching conversations** clears the current chat view and loads the selected conversation's context
- Each conversation maintains its **own isolated history** with the AI agent

### Conversation Persistence

- All conversations are **automatically saved** to the backend
- Conversations persist across browser sessions
- The agent maintains separate context for each conversation
- Deleting a conversation removes both the metadata and the conversation history

## Environment Variables

Create a `.env` file in the `backend` directory:

```env
ANTHROPIC_API_KEY=your-anthropic-api-key
MCP_CLIENT_ID=your-mcp-client-id
MCP_CLIENT_SECRET=your-mcp-client-secret
# MCP server URL is configured in backend/.mcp.json
```

## API Documentation

### Chat API

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me all orders"}'
```

### A2A Agent Discovery

```bash
curl http://localhost:8000/.well-known/agent.json
```

### A2A Task Creation

```bash
curl -X POST http://localhost:8000/a2a/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "role": "user",
      "parts": [{"text": "List recent orders"}]
    }
  }'
```

### Configuration API

```bash
# Get current configuration
curl http://localhost:8000/api/config

# Update A2A agent URL
curl -X PUT http://localhost:8000/api/config/a2a \
  -H "Content-Type: application/json" \
  -d '{"url": "http://localhost:8000", "headers": {}}'

# Update MCP server configuration
curl -X PUT http://localhost:8000/api/config/mcp \
  -H "Content-Type: application/json" \
  -d '{"name": "orders", "url": "https://your-mcp-server.com/mcp/", "headers": {}}'
```

## Testing and Evals

This project includes a comprehensive testing setup for learning evaluation best practices.

### Unit Tests

Test individual components (A2A endpoints, agent tools, MCP configuration):

```bash
cd backend
pytest
```

### Agent Evals

The eval framework tests agent behavior - tool selection, parameter accuracy, response quality:

- **Dataset**: `backend/tests/evals/dataset.json` - Contains test cases with expected tools and parameters
- **Runner**: `backend/tests/evals/run_evals.py` - Executes evals and calculates metrics

```bash
cd backend
pytest tests/evals/ -v
```

### Run with Coverage

```bash
cd backend
pytest --cov=. --cov-report=html
```

## Available Scripts

From the root directory:

| Command | Description |
|---------|-------------|
| `npm start` | Run both backend and frontend (recommended) |
| `npm run dev` | Alias for `npm start` |
| `npm run backend` | Run backend only |
| `npm run frontend` | Run frontend only |
| `npm run setup` | Install frontend dependencies |

## Project Structure

```
simple-order-agent/
├── package.json        # Root npm scripts (runs both services)
├── claude.md           # Claude context file
├── PRD.md              # Product requirements
├── SPEC.md             # Technical specification
├── README.md           # This file
├── backend/
│   ├── main.py         # FastAPI entry point
│   ├── .mcp.json       # MCP server configuration for Claude Agent SDK
│   ├── agent/          # Claude agent configuration
│   ├── a2a/            # A2A protocol implementation
│   ├── api/            # Configuration & Conversation APIs
│   │   ├── config_models.py          # Configuration Pydantic models
│   │   ├── config_store.py           # JSON file persistence
│   │   ├── config_router.py          # Configuration FastAPI routes
│   │   ├── conversation_models.py    # Conversation models & storage
│   │   └── conversation_router.py    # Conversation FastAPI routes
│   ├── data/           # Runtime data (gitignored)
│   │   ├── config.json         # User configuration file
│   │   └── conversations.json  # Conversation metadata
│   └── tests/          # Unit tests and evals
│       ├── evals/      # Agent evaluation framework
│       │   ├── dataset.json   # Eval test cases
│       │   └── run_evals.py   # Eval runner
│       ├── test_agent_tools.py
│       ├── test_a2a_endpoints.py
│       └── test_config_api.py
└── frontend/
    ├── src/
    │   ├── app/        # Next.js pages
    │   │   ├── page.tsx      # Chat page
    │   │   └── settings/     # Settings page
    │   ├── components/ # React components (Chat, UI)
    │   └── lib/        # Utilities and API client
    └── package.json
```

## Recent Changes

- **Multi-Conversation Feature**: Create and manage multiple conversation threads
  - Collapsible sidebar with conversation list
  - Create, switch, rename, and delete conversations
  - Auto-generate titles from first message
  - Conversation metadata (timestamp, message count)
  - Persistent storage in backend
  - Each conversation maintains separate context with the AI agent
- **ClaudeSDKClient Migration**: Improved conversation handling
  - Migrated from stateless `query()` to stateful `ClaudeSDKClient`
  - Conversations now properly maintain context across messages
  - Added conversation cleanup methods for memory management
  - True multi-turn conversation support with automatic history tracking
- **Agent Card Display Feature**: Full expandable agent card display in Settings page
  - Shows comprehensive agent information (skills, capabilities, authentication)
  - Collapsible UI with smooth transitions
  - Automatically updates when testing A2A connections
  - Displays skill tags, example queries, and documentation links

## Example Queries

Try these in the chat interface:

- "Show me all orders"
- "Find orders for customer 003KB000004r85iYAA"
- "What's our total revenue?"
- "Create an order for customer C001 named John Doe for a Laptop at $999"
- "Help me create a new order"

## A2A Protocol

This agent is A2A-compliant and can be discovered by other agents:

```
GET /.well-known/agent.json
```

Supported skills:
- `get_all_orders` - Retrieve all orders
- `get_orders_by_customer_id` - Get customer order history
- `create_order` - Create new orders
- `analyze_orders` - Perform analytics queries

## Architecture

```
┌─────────────────────────────────────────┐
│      Chat Interface (Next.js)           │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│           FastAPI Backend               │
│    Claude Agent SDK + .mcp.json         │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│     Orders MCP Server (MuleSoft)        │
└─────────────────────────────────────────┘
```

## License

MIT
