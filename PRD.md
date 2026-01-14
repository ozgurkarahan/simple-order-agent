# Product Requirements Document (PRD)

## Oz's Order Management Agent Dashboard

### Executive Summary

Build an AI-powered analytics dashboard that enables natural language querying of order data. The system connects to an existing Orders MCP server and provides both a web interface for human users and an A2A-compliant API for other AI agents.

---

## Problem Statement

Accessing and analyzing order data typically requires:
- Writing SQL queries or using complex filters
- Understanding the data schema
- Manual data aggregation for insights

**Solution**: An AI agent that understands natural language queries and automatically translates them into the appropriate API calls, presenting results in a user-friendly format.

---

## Goals

1. **Enable natural language order analytics** - Users can ask questions like "What were our top-selling products last week?"
2. **Provide a modern web dashboard** - Visual interface with chat, tables, and charts
3. **Support agent-to-agent communication** - Expose capabilities via A2A protocol
4. **Establish testing best practices** - Comprehensive eval framework for agent behavior

---

## User Personas

### Primary: Business Analyst
- Needs quick access to order insights
- Not technical, prefers natural language
- Values visual representations of data

### Secondary: Developer
- Testing Claude Agent SDK capabilities
- Learning MCP and A2A protocols
- Building integrations with the agent

### Tertiary: Other AI Agents
- Automated systems needing order data
- Multi-agent workflows
- Scheduled analytics tasks

---

## Features

### P0 (Must Have)

| Feature | Description |
|---------|-------------|
| Chat Interface | Natural language input with streaming responses |
| Order Listing | Query and filter orders via conversation |
| Order Details | Get specific order information by ID |
| Order Creation | Create new orders through natural language |
| A2A Agent Card | Discoverable agent metadata |
| A2A Task API | Create and track tasks from other agents |

### P1 (Should Have)

| Feature | Description |
|---------|-------------|
| Analytics Charts | Visual representation of order trends |
| **Multi-Conversation Support** | Create, manage, and switch between multiple conversation threads |
| Quick Actions | Pre-built query buttons for common requests |
| Streaming Responses | Real-time token streaming in UI |
| Claude Desktop UI | Warm cream theme, serif headings, minimal design |
| Tool Result Accordion | Collapsible display for MCP tool outputs with "M" badge |
| MCP Status Indicator | Display connected MCP servers in chat input toolbar |
| Connectors Popover | Quick access to view/manage MCP server connections |

### P2 (Nice to Have)

| Feature | Description |
|---------|-------------|
| Export Data | Download query results as CSV/JSON |
| Dark Mode | Theme toggle for UI |
| Multi-language | Support for non-English queries |

---

## Multi-Conversation Feature

### Problem Statement

Users need to maintain separate conversation contexts for different tasks or questions. Currently, all chat happens in a single continuous conversation, which makes it difficult to:
- Start fresh on a new topic without losing context
- Organize different analysis tasks separately
- Return to previous conversations for reference
- Keep track of multiple ongoing investigations

**Solution**: A multi-conversation system that allows users to create, switch between, rename, and delete separate conversation threads, with each conversation maintaining its own history and context.

### User Stories

| ID | As a... | I want to... | So that... |
|----|---------|--------------|------------|
| MC1 | Business Analyst | Create multiple conversations | I can organize different analysis tasks separately |
| MC2 | User | Switch between conversations | I can work on multiple topics without losing context |
| MC3 | User | Rename conversations | I can easily identify and find specific conversations |
| MC4 | User | Delete old conversations | I can clean up and remove conversations I no longer need |
| MC5 | User | See conversation metadata | I know when a conversation was last updated and message count |

### Multi-Conversation Features

#### P0 (Must Have)

| Feature | Description |
|---------|-------------|
| Conversation Sidebar | Collapsible sidebar displaying all conversations |
| Create Conversation | Button to start a new empty conversation |
| Switch Conversations | Click to activate and load a different conversation |
| Auto-Title Generation | First user message (truncated to 50 chars) becomes the title |
| Rename Conversation | Inline editing to change conversation title |
| Delete Conversation | Remove conversation and clear its history |
| Conversation Metadata | Display title, timestamp, and message count |
| Conversation Persistence | Store conversations in backend JSON file |
| Active Conversation Indicator | Highlight the currently active conversation |
| Sidebar Toggle | Button to show/hide the sidebar |

#### P1 (Should Have)

| Feature | Description |
|---------|-------------|
| Keyboard Shortcuts | Quick keys for new conversation, navigation |
| Conversation Search | Filter conversations by title |
| Conversation Export | Download a conversation's full history |

#### P2 (Nice to Have)

| Feature | Description |
|---------|-------------|
| Conversation Tags | Organize conversations with custom tags |
| Conversation Archive | Archive old conversations without deleting |
| Shared Conversations | Share conversation links with team members |

### Implementation Details

**Backend:**
- `ConversationMetadata` model with id, title, created_at, updated_at, message_count
- `ConversationStore` class for JSON file-based storage
- REST API endpoints: GET/POST/PUT/DELETE at `/api/conversations`
- Auto-generate title from first message (max 50 chars)
- Clear conversation history when deleted

**Frontend:**
- `ConversationSidebar` component with list and controls
- Chat component accepts `conversationId` prop
- Main page orchestrates sidebar + chat state
- Create new conversation on app load if none exist
- Clear messages when switching conversations

---

## Configuration Feature

### Problem Statement

Currently, the frontend is tightly coupled to the local Orders Agent backend. Users cannot:
- Connect to different A2A-compliant agents without code changes
- Dynamically switch between MCP server configurations
- Test external A2A agents they are developing
- **Configure multiple MCP servers simultaneously**
- **Enable/disable MCP servers without removing them**

**Solution**: A configuration system that allows users to dynamically configure A2A agent connections and multiple MCP servers through a dedicated settings page, with persistence in a JSON configuration file.

### User Stories

| ID | As a... | I want to... | So that... |
|----|---------|--------------|------------|
| C1 | Developer | Configure the A2A agent URL from the UI | I can test different A2A agents without modifying code |
| C2 | Developer | Add custom headers to A2A connections | I can authenticate with external agents |
| C3 | Developer | Configure MCP server URLs dynamically | I can switch between different data sources |
| C4 | Developer | Add custom headers to MCP connections | I can authenticate with secured MCP servers |
| C5 | User | See which agent/MCP server I'm connected to | I know which system I'm interacting with |
| C6 | Developer | Persist my configuration across sessions | I don't have to reconfigure every time |

### Configuration Features

#### P0 (Must Have)

| Feature | Description |
|---------|-------------|
| Settings Page | Dedicated `/settings` route for configuration management |
| A2A Agent URL Config | Input field to set the A2A agent base URL |
| A2A Custom Headers | Key-value input for optional authentication headers |
| **Multiple MCP Servers** | Support for adding and managing multiple MCP servers |
| **Add MCP Server** | Form to add new MCP servers with name, URL, and headers |
| **Edit MCP Server** | Inline editing of server name, URL, headers |
| **Delete MCP Server** | Remove MCP servers from configuration |
| **Enable/Disable Servers** | Toggle server active status without deletion |
| **MCP Server List View** | Display all configured servers with status indicators |
| Configuration Persistence | Store configuration in JSON file |
| Connection Status | Display current connection status in header |

#### P1 (Should Have)

| Feature | Description |
|---------|-------------|
| Agent Card Display | Full agent card display with expandable UI showing skills, capabilities, authentication info, and documentation links |
| Connection Test | Button to test connectivity before saving (per server) |
| MCP Tools Discovery | Display available tools from configured MCP server |
| **Server Status in Popover** | Display all servers with active/inactive status in connectors popover |

#### P2 (Nice to Have)

| Feature | Description |
|---------|-------------|
| Configuration Profiles | Save multiple named configurations |
| Import/Export Config | Download/upload configuration as JSON |
| Configuration History | Track recent configuration changes |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| UI Visual Consistency | Match Claude desktop aesthetic |
| Tool Result Readability | Accordion expand/collapse in <100ms |
| Tool Selection Accuracy | >95% |
| Response Relevance | >4.0/5 (LLM-judged) |
| Task Completion Rate | >85% |
| UI Response Time | <2s to first token |
| A2A Compliance | Pass all protocol tests |
| Config Save Success | 100% (valid configs) |
| A2A Connection Success | >95% (valid URLs) |
| MCP Hot-Reload Success | >99% |
| Conversation Switch Time | <500ms |
| Conversation Storage Reliability | 100% (no data loss) |

---

## Technical Constraints

- Must use Claude Agent SDK for the AI agent
- MCP server is external and read-heavy (rate limit awareness)
- A2A implementation must follow Google's specification
- Frontend must be accessible and responsive

---

## Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Setup | Day 1 | Project structure, documentation |
| Backend Core | Day 1-2 | FastAPI, Agent, MCP client |
| A2A Protocol | Day 2-3 | Models, endpoints, task manager |
| Testing | Day 3 | Unit tests, eval framework |
| Frontend | Day 3-4 | Dashboard, chat, analytics |
| Polish | Day 4-5 | CI/CD, documentation, cleanup |

---

## Out of Scope

- User authentication (will use simple API keys)
- Multi-tenant support
- Production deployment infrastructure
- Mobile-specific UI
