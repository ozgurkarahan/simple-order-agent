# Product Requirements Document (PRD)

## Orders Analytics Agent Dashboard

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

### P2 (Nice to Have)

| Feature | Description |
|---------|-------------|
| Export Data | Download query results as CSV/JSON |
| Dark Mode | Theme toggle for UI |
| Multi-language | Support for non-English queries |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Tool Selection Accuracy | >95% |
| Response Relevance | >4.0/5 (LLM-judged) |
| Task Completion Rate | >85% |
| UI Response Time | <2s to first token |
| A2A Compliance | Pass all protocol tests |

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
