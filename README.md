# Orders Analytics Agent Dashboard

An AI-powered analytics dashboard that enables natural language querying of order data using the Claude Agent SDK, MCP protocol, and A2A compliance.

## Features

- **Natural Language Queries**: Ask questions about orders in plain English
- **Analytics Dashboard**: Visual charts and statistics for order insights
- **A2A Protocol Support**: Discoverable and callable by other AI agents
- **Comprehensive Testing**: Unit tests and agent evals included

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   Web Dashboard │     │  Other A2A      │
│   (Next.js)     │     │  Agents         │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       ▼
┌─────────────────────────────────────────┐
│           FastAPI Backend               │
│         Claude Agent + MCP Client       │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│         Orders MCP Server               │
└─────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Anthropic API key

### Backend Setup

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

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to access the dashboard.

## Environment Variables

Create a `.env` file in the `backend` directory:

```env
ANTHROPIC_API_KEY=your-anthropic-api-key
MCP_CLIENT_ID=your-mcp-client-id
MCP_CLIENT_SECRET=your-mcp-client-secret
MCP_BASE_URL=https://agent-network-ingress-gw-0zaqgg.lr8qeg.deu-c1.cloudhub.io/orders-mcp/
```

## API Documentation

### Chat API

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me all orders from last week"}'
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

## Testing

### Run Unit Tests

```bash
cd backend
pytest
```

### Run Agent Evals

```bash
cd backend
pytest tests/evals/ -v
```

### Run with Coverage

```bash
cd backend
pytest --cov=. --cov-report=html
```

## Project Structure

```
simple-order-agent/
├── claude.md           # Claude context file
├── PRD.md              # Product requirements
├── SPEC.md             # Technical specification
├── README.md           # This file
├── backend/
│   ├── main.py         # FastAPI entry point
│   ├── agent/          # Claude agent configuration
│   ├── mcp/            # MCP client implementation
│   ├── a2a/            # A2A protocol implementation
│   └── tests/          # Unit tests and evals
└── frontend/
    ├── src/
    │   ├── app/        # Next.js pages
    │   ├── components/ # React components
    │   └── lib/        # Utilities and API client
    └── package.json
```

## Example Queries

Try these queries in the chat interface:

- "Show me all orders from last week"
- "What's the status of order #12345?"
- "Which products are selling the most?"
- "Create an order for customer C001 with 2 units of product P100"
- "What's our total revenue this month?"

## A2A Protocol

This agent is A2A-compliant and can be discovered by other agents. The agent card is available at:

```
GET /.well-known/agent.json
```

Supported skills:
- `list_orders` - Query and filter orders
- `get_order` - Get order details by ID
- `create_order` - Create new orders
- `analyze_orders` - Perform analytics queries

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## License

MIT
