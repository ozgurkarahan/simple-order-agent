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
| Conversation History | Persist and recall past conversations |
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

## Configuration Feature

### Problem Statement

Currently, the frontend is tightly coupled to the local Orders Agent backend. Users cannot:
- Connect to different A2A-compliant agents without code changes
- Dynamically switch between MCP server configurations
- Test external A2A agents they are developing

**Solution**: A configuration system that allows users to dynamically configure A2A agent connections and MCP servers through a dedicated settings page, with persistence in a JSON configuration file.

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
| MCP Server URL Config | Input field to set the MCP server URL |
| MCP Custom Headers | Key-value input for optional MCP authentication headers |
| Configuration Persistence | Store configuration in JSON file |
| Connection Status | Display current connection status in header |

#### P1 (Should Have)

| Feature | Description |
|---------|-------------|
| Agent Card Preview | Fetch and display agent card from configured A2A URL |
| Connection Test | Button to test connectivity before saving |
| MCP Tools Discovery | Display available tools from configured MCP server |

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
