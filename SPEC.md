# Technical Specification

## Oz's Order Management Agent

### 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (Next.js)                         │
│  ┌────────────────────────────┐  ┌────────────────────────────┐ │
│  │       Chat Page (/)        │  │    Settings Page (/settings)│ │
│  │  ┌─────────────┐           │  │  ┌─────────────────────┐   │ │
│  │  │ MessageList │           │  │  │  A2A Config Form    │   │ │
│  │  ├─────────────┤           │  │  │  - URL              │   │ │
│  │  │ QuickActions│           │  │  │  - Headers          │   │ │
│  │  ├─────────────┤           │  │  ├─────────────────────┤   │ │
│  │  │ InputArea   │           │  │  │  MCP Config Form    │   │ │
│  │  └─────────────┘           │  │  │  - URL              │   │ │
│  └────────────────────────────┘  │  │  - Headers          │   │ │
│                                   │  └─────────────────────┘   │ │
│                                   └────────────────────────────┘ │
│                       ┌──────────────┐                           │
│                       │   API Lib    │                           │
│                       └──────┬───────┘                           │
└──────────────────────────────┼───────────────────────────────────┘
                               │ HTTP/SSE + A2A Protocol
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐
│ Local Backend   │  │ External A2A   │  │  Other A2A Agents   │
│ (FastAPI)       │  │ Agent          │  │                     │
│ ┌─────────────┐ │  └─────────────────┘  └─────────────────────┘
│ │/api/config  │ │
│ │ (Config API)│ │
│ ├─────────────┤ │
│ │ /a2a/tasks  │ │
│ ├─────────────┤ │
│ │ Orders Agent│ │
│ └──────┬──────┘ │
│        │        │
│ ┌──────▼──────┐ │
│ │ config.json   │ │
│ │ (Config)    │ │
│ └─────────────┘ │
└────────┬────────┘
         │ HTTPS (Configurable)
         ▼
┌─────────────────────────────────────────┐
│  MCP Server (Orders or Configured)       │
└─────────────────────────────────────────┘
```

---

### 2. Backend Specification

#### 2.1 Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Runtime | Python | 3.11+ |
| Framework | FastAPI | 0.109+ |
| AI SDK | claude-agent-sdk | 0.1.19+ |
| AI Client | anthropic | 0.40+ |
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
  "message": "Show me all orders",
  "conversation_id": "optional-uuid"
}

Response (SSE stream):
event: message
data: {"type": "text", "content": "I'll fetch..."}

event: tool_use
data: {"type": "tool_use", "tool": "get_all_orders", "input": {...}}

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

##### Configuration API

```
GET /api/config
Response: Current configuration
{
  "a2a": {
    "url": "http://localhost:8000",
    "headers": {"Authorization": "Bearer xxx"},
    "is_local": true
  },
  "mcp": {
    "name": "orders",
    "url": "https://...",
    "headers": {"client_id": "xxx"},
    "is_active": true
  }
}

PUT /api/config/a2a
Request:
{
  "url": "https://external-agent.example.com",
  "headers": {
    "Authorization": "Bearer token123"
  }
}
Response: { "status": "saved", "connection_test": "success" }

PUT /api/config/mcp
Request (Legacy - updates first server):
{
  "name": "custom-mcp",
  "url": "https://my-mcp-server.com/mcp/",
  "headers": {
    "client_id": "my-client",
    "client_secret": "my-secret"
  }
}
Response: { "status": "saved", "reload_required": false }

POST /api/config/mcp
Request (Add new server):
{
  "name": "inventory",
  "url": "https://inventory-mcp.com/",
  "headers": { "api_key": "key123" }
}
Response: { "status": "added", "reload_required": false }

PUT /api/config/mcp/{server_id}
Request (Update existing server):
{
  "name": "updated-name",
  "url": "https://new-url.com/",
  "is_active": false
}
Response: { "status": "updated", "reload_required": false }

DELETE /api/config/mcp/{server_id}
Response: { "status": "deleted", "reload_required": false }

POST /api/config/a2a/test
Request: { "url": "https://...", "headers": {...} }
Response: {
  "success": true,
  "agent_card": { "name": "...", "description": "...", ... }
}

POST /api/config/mcp/test
Request: { "url": "https://...", "headers": {...} }
Response: {
  "success": true,
  "tools": ["tool1", "tool2", ...]
}

POST /api/config/reset
Response: { "status": "reset", "message": "Configuration reset to defaults" }
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

##### Configuration Models

```python
class A2AConfig(BaseModel):
    """A2A agent connection configuration."""
    url: str = "http://localhost:8000"
    headers: dict[str, str] = {}
    is_local: bool = True  # True if pointing to local backend

class MCPServerConfig(BaseModel):
    """MCP server configuration."""
    id: str  # Unique identifier (auto-generated UUID)
    name: str
    url: str
    headers: dict[str, str] = {}
    is_active: bool = True

class AppConfig(BaseModel):
    """Complete application configuration."""
    a2a: A2AConfig
    mcp_servers: list[MCPServerConfig]  # List of MCP servers
    updated_at: datetime
```

#### 2.4 Configuration File

The configuration is persisted in a JSON file for simplicity and human readability.

##### JSON File Structure

```json
{
  "a2a": {
    "url": "http://localhost:8000",
    "headers": {},
    "is_local": true
  },
  "mcp_servers": [
    {
      "id": "uuid-generated-123",
      "name": "orders",
      "url": "https://agent-network-ingress-gw-0zaqgg.lr8qeg.deu-c1.cloudhub.io/orders-mcp/",
      "headers": {
        "client_id": "xxx",
        "client_secret": "xxx"
      },
      "is_active": true
    },
    {
      "id": "uuid-generated-456",
      "name": "inventory",
      "url": "https://inventory-mcp.example.com/",
      "headers": {
        "api_key": "yyy"
      },
      "is_active": false
    }
  ],
  "updated_at": "2025-01-12T10:00:00Z"
}
```

**Migration Support**: The system automatically migrates old single-server configs (with `mcp` field) to the new list format (with `mcp_servers` field) on first load.

##### File Location

- **File**: `backend/data/config.json`
- **Creation**: Auto-created on first save with defaults
- **Gitignore**: File is gitignored (contains sensitive headers)

#### 2.5 MCP Configuration

##### Static Configuration (Default)

The Claude Agent SDK connects to the external MCP server using `.mcp.json` configuration:

```json
{
  "mcpServers": {
    "orders": {
      "type": "http",
      "url": "https://agent-network-ingress-gw-0zaqgg.lr8qeg.deu-c1.cloudhub.io/orders-mcp/",
      "headers": {
        "client_id": "${MCP_CLIENT_ID}",
        "client_secret": "${MCP_CLIENT_SECRET}"
      }
    }
  }
}
```

- **Transport**: HTTP with SSE for streaming (handled by SDK)
- **Authentication**: Custom headers from environment variables
- **Configuration**: `backend/.mcp.json`

##### Dynamic Configuration (New)

When users configure MCP servers through the Settings page:

1. **Configuration Builder**: The backend passes a list of active MCP servers to the Claude Agent SDK
2. **Server Selection**: Only servers with `is_active: true` are included
3. **Hot Reload**: When configuration changes, the agent is reinitialized with new servers
4. **Multi-Server Support**: Agent can access tools from all active servers simultaneously

```python
# Example: Building options with multiple servers
mcp_servers = {}
for config in active_configs:
    mcp_servers[config.name] = {
        "type": "http",
        "url": config.url,
        "headers": config.headers
    }

options = ClaudeAgentOptions(
    model="claude-sonnet-4-20250514",
    mcp_servers=mcp_servers,  # Multiple servers
    permission_mode="bypassPermissions"
)
```

1. **Configuration Saved**: New MCP URL and headers stored in JSON config file
2. **Agent Reload**: The Orders Agent is re-initialized with new MCP config
3. **Hot Swap**: No server restart required; agent instance replaced in memory

```python
# Dynamic MCP configuration flow
async def update_mcp_config(config: MCPServerConfig) -> None:
    # 1. Save to config file
    config_store.save_mcp_config(config)
    
    # 2. Rebuild MCP configuration dict
    mcp_config = {
        "mcpServers": {
            config.name: {
                "type": "http",
                "url": config.url,
                "headers": config.headers
            }
        }
    }
    
    # 3. Re-initialize agent with new config
    global orders_agent
    orders_agent = await create_agent_with_mcp(mcp_config)
```

##### Configuration Priority

1. **JSON config file** (if exists) - Takes precedence
2. **`.mcp.json` file** - Default fallback
3. **Environment variables** - For sensitive headers

##### Available Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get-all-orders` | Retrieve all orders | None |
| `get-orders-by-customer-id` | Get orders for a customer | `id` (customer ID) |
| `create-order` | Create new order | `customerID`, `customerName`, `productName`, `price`, `orderDate` |

---

### 3. Frontend Specification

#### 3.1 Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | Next.js | 14+ |
| UI Library | React | 18+ |
| Styling | Tailwind CSS | 3.4+ |
| Components | shadcn/ui | latest |
| State | React Query | 5+ |

#### 3.2 Page Structure

```
/                    - Full-screen chat interface
/settings            - Configuration page
```

#### 3.3 Component Hierarchy

```
Layout
├── Header (minimal, right-aligned)
│   ├── StatusIndicators (online, streaming badges)
│   └── SettingsLink (gear icon → /settings)
├── Chat (/) - Claude Desktop-inspired design
│   ├── EmptyState (centered when no messages)
│   │   ├── AgentBranding (✦ logo + serif title)
│   │   ├── InputToolbar (pill-shaped input)
│   │   └── QuickActionsText (subtle links below)
│   ├── MessageList (when messages exist)
│   │   ├── UserMessage (right-aligned, muted bg)
│   │   └── AgentMessage (left-aligned)
│   │       └── ToolAccordion (collapsible MCP results)
│   └── InputToolbar
│       ├── TextArea (auto-resize)
│       ├── ConnectorsPopover (MCP status display)
│       ├── ModelBadge ("Claude Sonnet")
│       └── SendButton (coral accent)
└── Settings (/settings)
    ├── SettingsHeader
    │   ├── BackLink (← Back to Chat)
    │   └── Title
    ├── A2AConfigSection
    │   ├── URLInput (with validation)
    │   ├── HeadersEditor (key-value pairs)
    │   ├── TestConnectionButton
    │   └── AgentCardDisplay (if connected)
    │       ├── Header (always visible - name, version, description)
    │       ├── ExpandButton (show/hide details)
    │       └── ExpandedContent (collapsible)
    │           ├── Capabilities (streaming, push notifications, state history)
    │           ├── Skills (with tags and examples)
    │           ├── Authentication (type and credentials URL)
    │           ├── Links (agent URL and documentation)
    │           └── InputOutputModes
    ├── MCPServersSection
    │   ├── ServersList (shows all configured servers)
    │   │   └── MCPServerCard (for each server)
    │   │       ├── ServerHeader (name, active/inactive badge)
    │   │       ├── ServerURL
    │   │       ├── TestConnectionButton
    │   │       ├── EditButton (inline editing)
    │   │       └── DeleteButton
    │   └── AddServerButton (+ Add MCP Server)
    │       └── AddServerForm (shown when clicked)
    │           ├── ServerNameInput
    │           ├── URLInput (with validation)
    │           └── HeadersEditor (key-value pairs)
    └── ActionButtons
        └── ResetToDefaultsButton
```

#### 3.4 Design System

##### Color Palette (Warm Cream Theme)

| Token | HSL Value | Description |
|-------|-----------|-------------|
| background | 36 33% 95% | Warm cream background |
| foreground | 25 20% 15% | Dark warm text |
| card | 0 0% 100% | Pure white cards |
| primary | 15 75% 55% | Coral/terracotta accent |
| muted | 36 20% 90% | Subtle warm gray |
| border | 36 15% 88% | Light warm border |

##### Typography

| Family | Font | Usage |
|--------|------|-------|
| Serif | Libre Baskerville | Headings, branding |
| Sans | Inter | Body text, UI |
| Mono | JetBrains Mono | Code, tool names |

##### Component Patterns

- **ToolAccordion**: Collapsible panel with "M" badge for MCP tool results
- **ConnectorsPopover**: Dropdown showing connected MCP servers
- **InputToolbar**: Pill-shaped input with bottom toolbar (actions, model badge, send)

#### 3.5 Settings Page Specification

##### URL: `/settings`

##### Layout

```
┌─────────────────────────────────────────────────────────────┐
│  ← Back to Chat                        Configuration        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  A2A Agent Connection                               │   │
│  │  ────────────────────────────────────────────────── │   │
│  │  Agent URL:  [http://localhost:8000_____________]   │   │
│  │                                                     │   │
│  │  Custom Headers (optional):                         │   │
│  │  ┌──────────────┬─────────────────────┬────┐       │   │
│  │  │ Key          │ Value               │ ✕  │       │   │
│  │  ├──────────────┼─────────────────────┼────┤       │   │
│  │  │ Authorization│ Bearer xxx          │ ✕  │       │   │
│  │  └──────────────┴─────────────────────┴────┘       │   │
│  │  [+ Add Header]                                     │   │
│  │                                                     │   │
│  │  [Test Connection]  ✓ Connected: Orders Agent v1.0 │   │
│  │                                                     │   │
│  │  ┌───────────────────────────────────────────────┐ │   │
│  │  │ 🛡️ Oz's Order Management Agent v1.0.0    [▼] │ │   │
│  │  │ AI-powered agent for querying and analyzing  │ │   │
│  │  │ order data.                                   │ │   │
│  │  │                                               │ │   │
│  │  │ [Expanded] Skills, Capabilities, Auth, Links │ │   │
│  │  └───────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  MCP Server Configuration                           │   │
│  │  ────────────────────────────────────────────────── │   │
│  │  Server Name: [orders________________________]      │   │
│  │  Server URL:  [https://...cloudhub.io/orders-mcp/]  │   │
│  │                                                     │   │
│  │  Custom Headers (optional):                         │   │
│  │  ┌──────────────┬─────────────────────┬────┐       │   │
│  │  │ client_id    │ abc123              │ ✕  │       │   │
│  │  ├──────────────┼─────────────────────┼────┤       │   │
│  │  │ client_secret│ ••••••••            │ ✕  │       │   │
│  │  └──────────────┴─────────────────────┴────┘       │   │
│  │  [+ Add Header]                                     │   │
│  │                                                     │   │
│  │  [Test Connection]  ✓ 3 tools available            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│         [Reset to Defaults]        [Save Configuration]    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

##### Header Examples (UI Helper Text)

Display examples to help users understand common header patterns:

**A2A Headers Examples:**
- `Authorization: Bearer <token>` - Bearer token auth
- `X-API-Key: <key>` - API key auth

**MCP Headers Examples:**
- `client_id: <id>` - MuleSoft client ID
- `client_secret: <secret>` - MuleSoft client secret
- `Authorization: Basic <base64>` - Basic auth

#### 3.5 State Management

- **Server State**: React Query for API calls with caching
- **UI State**: React useState for local state
- **Chat State**: Conversation history in React state
- **Config State**: React Query for config CRUD with optimistic updates

##### Configuration State Flow

```
1. Page Load → GET /api/config → Populate form
2. User Edits → Local state updates (no API call)
3. Test Connection → POST /api/config/a2a/test or /mcp/test
4. Success → Extract agent_card and store in state → Display AgentCardDisplay
5. Save → PUT /api/config/a2a and/or PUT /api/config/mcp
6. Success → Invalidate queries, refresh config
```

##### Agent Card State Management

```typescript
// State in settings page
const [agentCard, setAgentCard] = useState<AgentCard | null>(null);

// On successful connection test
testA2AMutation.onSuccess = (data) => {
  if (data.success && data.agent_card) {
    setAgentCard(data.agent_card);  // Full agent card with all fields
  }
};

// Clear on error or reset
setAgentCard(null);
```

---

### 4. Testing Specification

#### 4.1 Unit Tests

| Module | Test Coverage |
|--------|---------------|
| MCP Configuration | .mcp.json validation, SDK integration |
| A2A Models | Schema validation, serialization |
| A2A Router | Endpoint behavior, status codes |
| Task Manager | State transitions, streaming |
| Config API | CRUD operations, validation, defaults |
| Config Store | JSON file read/write, default values |
| Connection Tests | A2A/MCP test endpoints, timeout handling |

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
| Config Headers | Stored encrypted in database (sensitive values) |
| URL Validation | Validate URL format before saving |
| Connection Test | Timeout limits on test connections (5s max) |

##### Configuration Security Notes

1. **Header Storage**: Sensitive headers (secrets, tokens) should be masked in API responses
2. **File Security**: Config file permissions restricted to application user
3. **URL Allowlist**: Consider optional allowlist for external A2A/MCP URLs in production
4. **Audit Log**: Log configuration changes with timestamps

---

### 6. Error Handling

| Error Type | HTTP Code | Response Format |
|------------|-----------|-----------------|
| Validation Error | 422 | `{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}` |
| MCP Server Error | 502 | `{"error": "MCP server unavailable", "details": "..."}` |
| Agent Error | 500 | `{"error": "Agent processing failed", "details": "..."}` |
| A2A Task Not Found | 404 | `{"error": "Task not found", "task_id": "..."}` |
| Config Not Found | 404 | `{"error": "Configuration not found"}` |
| Connection Test Failed | 400 | `{"error": "Connection failed", "details": "timeout/unreachable/auth"}` |
| Invalid URL | 422 | `{"error": "Invalid URL format", "field": "url"}` |
| MCP Reload Failed | 500 | `{"error": "Failed to reload MCP configuration", "details": "..."}` |