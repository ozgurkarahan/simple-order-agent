# Planning-First Agent Implementation

## Overview

This document describes the planning-first agent implementation that transforms the agent to follow a "Claude Code" style approach:
1. **Plan first** - Generate a structured execution plan before any action
2. **Propose steps** - Show the plan as a todo list with phases and tasks
3. **Wait for validation** - User approves or rejects the plan
4. **Execute task-by-task** - Run through approved tasks one by one
5. **Show progress** - Display real-time progress to frontend

## What Was Implemented

### 1. Backend - Data Models (`backend/a2a/models.py`)

**New Task States:**
- `PLANNING` - Agent is generating an execution plan
- `AWAITING_APPROVAL` - Plan is ready, waiting for user approval
- `EXECUTING` - Plan approved, executing tasks
- `PAUSED` - Execution temporarily paused by user

**New Models:**
- `TaskItemStatus` - Status enum for individual tasks (pending, in_progress, completed, failed, skipped)
- `TaskItem` - Individual task within a phase with description and status
- `Phase` - Group of related tasks with a name and description
- `Plan` - Full execution plan with multiple phases
- `ApprovePlanRequest` - API request to approve a plan
- `RejectPlanRequest` - API request to reject a plan with feedback

### 2. Backend - Agent Planning (`backend/agent/orders_agent.py`)

**New System Prompt:**
- `PLANNING_PROMPT` - Instructs the agent to generate structured JSON plans
- Guides the agent to create phases (Data Collection, Analysis, Presentation)
- Mixed granularity: combines business goals with technical steps
- Returns valid JSON format for easy parsing

**New Method:**
- `generate_plan(message, conversation_id)` - Generates a structured plan for any user request
- Uses a separate Claude client instance for planning
- Parses JSON from agent response
- Includes fallback plan if generation fails

### 3. Backend - Task Management (`backend/a2a/task_manager.py`)

**Enhanced TaskManager Class:**

New instance variables:
- `_paused_tasks` - Track which tasks are paused
- `_approval_events` - Async events for plan approval
- `_resume_events` - Async events for pause/resume

New public methods:
- `approve_plan(task_id)` - Approve plan and start execution
- `reject_plan(task_id, feedback)` - Reject plan and generate new one
- `pause_task(task_id)` - Pause task execution
- `resume_task(task_id)` - Resume paused task

New private methods:
- `_generate_plan(task_id, feedback)` - Generate and emit plan
- `_wait_for_approval(task_id)` - Block until user approves
- `_execute_plan(task_id)` - Execute all phases and tasks sequentially
- `_execute_task_item(task_id, task_item)` - Execute a single task using agent

**Task Lifecycle:**
```
SUBMITTED → PLANNING → AWAITING_APPROVAL → EXECUTING → COMPLETED
                ↑            ↓                   ↓
             (reject)    (approve)           (pause)
                                                ↓
                                             PAUSED
                                                ↓
                                            (resume)
```

### 4. Backend - API Endpoints (`backend/a2a/router.py`)

**New Endpoints:**
- `POST /a2a/tasks/{task_id}/approve` - Approve a task's plan
- `POST /a2a/tasks/{task_id}/reject` - Reject a plan with feedback
- `POST /a2a/tasks/{task_id}/pause` - Pause execution
- `POST /a2a/tasks/{task_id}/resume` - Resume execution

**SSE Events:**
- `status` - Task state changes (planning, awaiting-approval, executing, etc.)
- `plan_update` - Plan progress updates (task/phase status changes)
- Existing: `message`, `tool_use`, `artifact`

### 5. Frontend - PlanDisplay Component (`frontend/src/components/PlanDisplay.tsx`)

**Features:**
- Displays execution plan in checklist format
- Status icons: ✓ (completed), ⏳ (in progress), ⏸️ (pending), ❌ (failed)
- Grouped by phases with expandable task lists
- Color-coded status indicators
- Built-in approval buttons (Approve/Reject)
- Feedback textarea for plan rejection
- Execution controls (Pause/Resume/Cancel)
- Real-time updates via props

**Component Props:**
```typescript
{
  plan: Plan;
  isExecuting?: boolean;
  onApprove?: () => void;
  onReject?: (feedback: string) => void;
  onPause?: () => void;
  onResume?: () => void;
  onCancel?: () => void;
  showApprovalButtons?: boolean;
  showExecutionControls?: boolean;
  isPaused?: boolean;
}
```

### 6. Frontend - API Client (`frontend/src/lib/api.ts`)

**New Functions:**
- `approvePlan(taskId)` - Call approve endpoint
- `rejectPlan(taskId, feedback)` - Call reject endpoint
- `pauseTask(taskId)` - Call pause endpoint
- `resumeTask(taskId)` - Call resume endpoint
- `cancelTask(taskId)` - Call cancel endpoint

**New TypeScript Interfaces:**
- `Plan`, `Phase`, `TaskItem` - Match backend models
- `Task` - Full task object with status and plan

## How the Planning Flow Works

### Step 1: User Sends Message
```
User: "Analyze all orders and show me top customers"
```

### Step 2: Backend Generates Plan
```json
{
  "description": "Analyze orders and identify top customers",
  "phases": [
    {
      "id": "phase_1",
      "name": "Data Collection",
      "tasks": [
        { "id": "task_1_1", "description": "Call get-all-orders tool" }
      ]
    },
    {
      "id": "phase_2",
      "name": "Analysis",
      "tasks": [
        { "id": "task_2_1", "description": "Calculate total spending per customer" },
        { "id": "task_2_2", "description": "Sort customers by spending" },
        { "id": "task_2_3", "description": "Identify top 5 customers" }
      ]
    },
    {
      "id": "phase_3",
      "name": "Presentation",
      "tasks": [
        { "id": "task_3_1", "description": "Format results as table" },
        { "id": "task_3_2", "description": "Present findings" }
      ]
    }
  ]
}
```

### Step 3: Frontend Shows Plan
- PlanDisplay component renders the plan
- All tasks show ⏸️ (pending) status
- Approve/Reject buttons are visible

### Step 4: User Reviews and Approves
- User clicks "Approve Plan"
- Frontend calls `approvePlan(taskId)`
- Backend transitions to EXECUTING state

### Step 5: Backend Executes Plan
For each phase:
  - Phase status → IN_PROGRESS
  - For each task in phase:
    - Task status → IN_PROGRESS (shows ⏳)
    - Execute task using agent
    - Task status → COMPLETED (shows ✓)
  - Phase status → COMPLETED

Progress updates sent via SSE `plan_update` events.

### Step 6: Frontend Shows Real-time Progress
- PlanDisplay updates automatically as events arrive
- User sees tasks changing from ⏸️ → ⏳ → ✓
- Execution can be paused/resumed/cancelled

## What Still Needs Integration

### Option 1: Modify Chat.tsx to Use A2A Tasks (Recommended)

The Chat component currently uses `/api/chat` which bypasses the TaskManager. To enable planning-first:

1. **Update Chat.tsx to use A2A tasks:**
   ```typescript
   // Instead of:
   streamChat(message, conversationId)

   // Use:
   // 1. Create task via A2A
   const task = await createTask(message);

   // 2. Stream task events
   streamTaskEvents(task.id);

   // 3. Show plan when state = awaiting-approval
   if (event.status.state === 'awaiting-approval') {
     showPlanWithButtons(event.plan);
   }

   // 4. Handle approval/rejection
   onApprove={() => approvePlan(task.id))
   onReject((feedback) => rejectPlan(task.id, feedback))
   ```

2. **Add these API functions to api.ts:**
   ```typescript
   async function createTask(message: string) {
     const response = await fetch(`${API_BASE}/a2a/tasks`, {
       method: "POST",
       body: JSON.stringify({
         message: {
           role: "user",
           parts: [{ type: "text", text: message }]
         }
       })
     });
     return response.json();
   }

   async function* streamTaskEvents(taskId: string) {
     const response = await fetch(`${API_BASE}/a2a/tasks/${taskId}/stream`);
     const reader = response.body.getReader();
     // Parse SSE events similar to streamChat
   }
   ```

### Option 2: Modify /api/chat Endpoint

Alternatively, update the `/api/chat` endpoint in `backend/main.py` to use TaskManager:

```python
@app.post("/api/chat")
async def chat(request: ChatRequest):
    # Create task using TaskManager
    task = await task_manager.create_task(
        message=Message(
            role="user",
            parts=[Part(type="text", text=request.message)]
        )
    )

    # Stream task events (includes plan approval flow)
    async def generate():
        async for event in task_manager.stream_task(task.id):
            yield f"event: {event['event']}\ndata: {event['data']}\n\n"

    return StreamingResponse(generate(), ...)
```

This way the frontend doesn't need to change, but the `/api/chat` endpoint will automatically provide planning-first behavior.

## Testing the Implementation

### Backend Tests

1. **Start the backend:**
   ```bash
   cd backend
   python main.py
   ```

2. **Test plan generation via A2A API:**
   ```bash
   # Create task
   curl -X POST http://localhost:8000/a2a/tasks \
     -H "Content-Type: application/json" \
     -d '{
       "message": {
         "role": "user",
         "parts": [{"type": "text", "text": "Show me all orders"}]
       }
     }'

   # Get task (should show plan in awaiting-approval state)
   curl http://localhost:8000/a2a/tasks/{task_id}

   # Approve plan
   curl -X POST http://localhost:8000/a2a/tasks/{task_id}/approve \
     -H "Content-Type: application/json" \
     -d '{"approved": true}'

   # Stream progress
   curl http://localhost:8000/a2a/tasks/{task_id}/stream
   ```

### Frontend Tests

Once integrated:
1. Send a message
2. Verify plan appears with approval buttons
3. Click "Reject Plan" and provide feedback
4. Verify new plan is generated with feedback incorporated
5. Click "Approve Plan"
6. Watch real-time progress as tasks execute
7. Test pause/resume during execution

## Architecture Decisions

### Why TaskManager for Planning?

The TaskManager already handles:
- Task lifecycle and state management
- SSE streaming to frontend
- Event queuing and async coordination

This made it the natural place to implement planning logic rather than duplicating this infrastructure.

### Why Separate Planning Client?

The `generate_plan()` method uses a separate Claude client instance because:
- Planning uses a different system prompt (PLANNING_PROMPT vs SYSTEM_PROMPT)
- We don't want planning interactions in conversation history
- Planning is a single-turn operation (no back-and-forth)

### Why Mixed Granularity?

The plan structure groups tasks into phases with mixed detail levels because:
- High-level phases (Data Collection, Analysis) give business context
- Detailed tasks (Call get-all-orders tool) show technical steps
- Users can understand both "what" and "how"
- Easy to scan at a glance while still seeing details

## Configuration

No configuration changes needed! The implementation uses existing:
- Claude API credentials (from environment)
- MCP server configurations (for tool access)
- Agent initialization (same OrdersAgent instance)

## Next Steps

1. **Choose Integration Approach:**
   - Option 1: Modify Chat.tsx to use A2A tasks (more work, cleaner architecture)
   - Option 2: Modify /api/chat to use TaskManager (less work, quicker deployment)

2. **Implement Integration:**
   - Follow one of the integration approaches above
   - Add task state tracking to Chat component
   - Wire up PlanDisplay component
   - Connect approval/rejection/pause/resume handlers

3. **Test End-to-End:**
   - Test simple queries (show all orders)
   - Test complex queries (analyze and create reports)
   - Test plan rejection and regeneration
   - Test pause/resume during execution
   - Test error handling

4. **Polish:**
   - Add loading states
   - Add error messages
   - Add success notifications
   - Improve plan formatting
   - Add keyboard shortcuts for approval

## Questions?

Feel free to ask about:
- How any component works
- Integration approaches
- Customizing the plan structure
- Adding new task states
- Extending the planning prompt
- Performance optimization
