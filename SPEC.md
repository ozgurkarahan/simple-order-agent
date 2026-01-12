# Technical Specification

## Orders Analytics Agent Dashboard

### 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │    Chat     │  │  Analytics  │  │     Orders Table        │  │
│  │  Component  │  │   Charts    │  │      Component          │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
│         └────────────────┼─────────────────────┘                │
│                          │                                       │
│                   ┌──────▼──────┐                                │
│                   │   API Lib   │                                │
│                   └──────┬──────┘                                │
└──────────────────────────┼──────────────────────────────────────┘
                           │ HTTP/SSE
┌──────────────────────────┼──────────────────────────────────────┐
│                    BACKEND (FastAPI)                             │
│  ┌─────────────────┐  ┌──┴───────────┐  ┌───────────────────┐   │
│  │  /api/chat      │  │ /a2a/tasks   │  │ /.well-known/     │   │
│  │  (Chat API)     │  │ (A2A Tasks)  │  │  agent.json       │   │
│  └────────┬────────┘  └──────┬───────┘  └─────────┬─────────┘   │
│           └──────────────────┼────────────────────┘             │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │   Orders Agent    │                        │
│                    │  (Claude + Tools) │                        │
│                    └─────────┬─────────┘                        │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │    MCP Client     │                        │
│                    └─────────┬─────────┘                        │
└──────────────────────────────┼──────────────────────────────────┘
                               │ HTTPS
                    ┌──────────▼──────────┐
                    │  Orders MCP Server  │
                    │    (CloudHub)       │
                    └─────────────────────┘
```

---

### 2. Backend Specification

#### 2.1 Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Runtime | Python | 3.11+ |
| Framework | FastAPI | 0.109+ |
| AI SDK | anthropic | 0.40+ |
| HTTP Client | httpx | 0.27+ |
| Validation | Pydantic | 2.0+ |
| Testing | pytest | 8.0+ |

#### 2.2 API Endpoints

##### Chat API

```
POST /api/chat
Content-Type: application/json

Request:
{
  "message": "Show me orders from last week",
  "conversation_id": "optional-uuid"
}

Response (SSE stream):
event: message
data: {"type": "text", "content": "I'll fetch..."}

event: tool_use
data: {"type": "tool_use", "tool": "list_orders", "input": {...}}

event: tool_result
data: {"type": "tool_result", "content": [...]}

event: message
data: {"type": "text", "content": "Here are the orders..."}

event: done
data: {"type": "done"}
```

##### A2A Endpoints

```
GET /.well-known/agent.json
Response: AgentCard JSON

POST /a2a/tasks
Request: {
  "message": {"role": "user", "parts": [{"text": "..."}]}
}
Response: Task JSON with id, status

GET /a2a/tasks/{task_id}
Response: Task JSON with current status and artifacts

POST /a2a/tasks/{task_id}/cancel
Response: Updated Task JSON

GET /a2a/tasks/{task_id}/stream
Response: SSE stream of TaskStatusUpdate events
```

#### 2.3 Data Models

##### Agent Card (A2A)

```python
class AgentCard(BaseModel):
    name: str
    description: str
    version: str
    url: str
    capabilities: AgentCapabilities
    skills: list[Skill]
    authentication: AuthConfig | None
```

##### Task (A2A)

```python
class TaskState(str, Enum):
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    CANCELED = "canceled"
    FAILED = "failed"

class Task(BaseModel):
    id: str
    status: TaskStatus
    artifacts: list[Artifact] | None
    history: list[Message] | None
```

#### 2.4 MCP Client

The MCP client communicates with the Orders MCP server using:

- **Transport**: HTTP with SSE for streaming
- **Authentication**: Custom headers (`client_id`, `client_secret`)
- **Base URL**: `https://agent-network-ingress-gw-0zaqgg.lr8qeg.deu-c1.cloudhub.io/orders-mcp/`

##### Available Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_orders` | Query orders with filters | `status`, `date_from`, `date_to`, `customer_id`, `limit` |
| `get_order` | Get order by ID | `order_id` |
| `create_order` | Create new order | `customer_id`, `items`, `shipping_address` |

---

### 3. Frontend Specification

#### 3.1 Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | Next.js | 14+ |
| UI Library | React | 18+ |
| Styling | Tailwind CSS | 3.4+ |
| Components | shadcn/ui | latest |
| Charts | Recharts | 2.12+ |
| State | React Query | 5+ |

#### 3.2 Page Structure

```
/                    - Main dashboard with chat and analytics
```

#### 3.3 Component Hierarchy

```
Layout
├── Sidebar
│   ├── Navigation
│   └── AgentCard (A2A info)
├── MainContent
│   ├── Chat
│   │   ├── MessageList
│   │   ├── MessageInput
│   │   └── QuickActions
│   ├── Analytics
│   │   ├── StatsCards
│   │   └── Charts
│   └── OrdersTable
│       ├── DataTable
│       └── OrderDetails (modal)
```

#### 3.4 State Management

- **Server State**: React Query for API calls with caching
- **UI State**: React useState/useReducer for local state
- **Chat State**: Conversation history in React state, optional localStorage persistence

---

### 4. Testing Specification

#### 4.1 Unit Tests

| Module | Test Coverage |
|--------|---------------|
| MCP Client | Request formatting, response parsing, error handling |
| A2A Models | Schema validation, serialization |
| A2A Router | Endpoint behavior, status codes |
| Task Manager | State transitions, streaming |

#### 4.2 Agent Evals

##### Eval Dataset Structure

```json
{
  "version": "1.0",
  "evals": [
    {
      "id": "unique-id",
      "category": "tool_selection|response_quality|clarification",
      "input": "User message",
      "expected_tool": "tool_name",
      "expected_params": {},
      "response_must_contain": [],
      "response_must_not_contain": [],
      "tags": ["happy_path", "edge_case"]
    }
  ]
}
```

##### Eval Metrics

| Metric | Calculation | Target |
|--------|-------------|--------|
| Tool Accuracy | correct_tool / total | >95% |
| Param Accuracy | correct_params / total | >90% |
| Response Score | LLM judge 1-5 scale | >4.0 |
| Completion Rate | successful / total | >85% |

#### 4.3 CI Pipeline

```yaml
# GitHub Actions workflow
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements-dev.txt
      - run: pytest --cov=. --cov-report=xml
      - run: ruff check .
  
  evals:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements-dev.txt
      - run: pytest tests/evals/ -v
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

---

### 5. Security Considerations

| Area | Measure |
|------|---------|
| API Keys | Stored in environment variables, never committed |
| MCP Auth | Headers sent over HTTPS only |
| CORS | Restricted to frontend origin in production |
| Input Validation | Pydantic models for all inputs |
| Rate Limiting | Consider adding for production use |

---

### 6. Error Handling

| Error Type | HTTP Code | Response Format |
|------------|-----------|-----------------|
| Validation Error | 422 | `{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}` |
| MCP Server Error | 502 | `{"error": "MCP server unavailable", "details": "..."}` |
| Agent Error | 500 | `{"error": "Agent processing failed", "details": "..."}` |
| A2A Task Not Found | 404 | `{"error": "Task not found", "task_id": "..."}` |
