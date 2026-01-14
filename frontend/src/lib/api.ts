/**
 * API client for communicating with the Orders Agent backend.
 */

const API_BASE = "http://localhost:8000";

export interface ChatMessage {
  role: "user" | "agent";
  content: string;
  timestamp: Date;
  toolUse?: {
    tool: string;
    input: Record<string, unknown>;
  };
  toolResult?: string;
}

export interface AuthConfig {
  type: "none" | "bearer" | "apiKey" | "oauth2";
  credentialsUrl?: string;
}

export interface AgentCard {
  name: string;
  description: string;
  version: string;
  url: string;
  documentationUrl?: string;
  capabilities: {
    streaming: boolean;
    pushNotifications: boolean;
    stateTransitionHistory: boolean;
  };
  skills: Array<{
    id: string;
    name: string;
    description: string;
    tags: string[];
    examples: string[];
  }>;
  authentication?: AuthConfig;
  defaultInputModes?: string[];
  defaultOutputModes?: string[];
}

export interface StreamEvent {
  type: "message" | "tool_use" | "tool_result" | "error" | "done";
  data: {
    type?: string;
    content?: string;
    tool?: string;
    input?: Record<string, unknown>;
    result?: string;
    error?: string;
  };
}

// Configuration Types
export interface A2AConfig {
  url: string;
  headers: Record<string, string>;
  is_local: boolean;
}

export interface MCPServerConfig {
  id: string;
  name: string;
  url: string;
  headers: Record<string, string>;
  is_active: boolean;
}

export interface AppConfig {
  a2a: A2AConfig;
  mcp_servers: MCPServerConfig[];
  updated_at?: string;
}

export interface A2AConfigUpdate {
  url: string;
  headers: Record<string, string>;
}

export interface MCPConfigUpdate {
  name: string;
  url: string;
  headers: Record<string, string>;
}

export interface MCPServerAdd {
  name: string;
  url: string;
  headers: Record<string, string>;
}

export interface MCPServerUpdate {
  name?: string;
  url?: string;
  headers?: Record<string, string>;
  is_active?: boolean;
}

export interface ConnectionTestRequest {
  url: string;
  headers: Record<string, string>;
}

export interface A2ATestResponse {
  success: boolean;
  agent_card?: AgentCard;
  error?: string;
}

export interface MCPTestResponse {
  success: boolean;
  tools?: string[];
  error?: string;
}

export interface ConfigUpdateResponse {
  status: string;
  connection_test?: string;
  reload_required?: boolean;
  server_id?: string;
}

export interface ConfigResetResponse {
  status: string;
  message: string;
}

// Conversation Types
export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface CreateConversationRequest {
  title?: string;
}

export interface UpdateConversationRequest {
  title: string;
}

/**
 * Fetch the agent card for A2A discovery.
 */
export async function fetchAgentCard(): Promise<AgentCard> {
  const response = await fetch(`${API_BASE}/.well-known/agent.json`);
  if (!response.ok) {
    throw new Error(`Failed to fetch agent card: ${response.status}`);
  }
  return response.json();
}

/**
 * Send a chat message and receive streaming response.
 */
export async function* streamChat(
  message: string,
  conversationId?: string
): AsyncGenerator<StreamEvent> {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
    }),
  });

  if (!response.ok) {
    throw new Error(`Chat request failed: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("No response body");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();

    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Parse SSE events
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    let currentEvent = "";
    let currentData = "";

    for (const line of lines) {
      if (line.startsWith("event: ")) {
        currentEvent = line.slice(7);
      } else if (line.startsWith("data: ")) {
        currentData = line.slice(6);

        if (currentEvent && currentData) {
          try {
            const data = JSON.parse(currentData);
            yield {
              type: currentEvent as StreamEvent["type"],
              data,
            };
          } catch {
            // Skip invalid JSON
          }
          currentEvent = "";
          currentData = "";
        }
      }
    }
  }
}

/**
 * Send a chat message and get synchronous response.
 */
export async function sendChatSync(
  message: string,
  conversationId?: string
): Promise<{ message: string; conversationId?: string }> {
  const response = await fetch(`${API_BASE}/api/chat/sync`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
    }),
  });

  if (!response.ok) {
    throw new Error(`Chat request failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Health check endpoint.
 */
export async function checkHealth(): Promise<{
  status: string;
  service: string;
  version: string;
}> {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) {
    throw new Error("Health check failed");
  }
  return response.json();
}

// Configuration API Functions

/**
 * Fetch current configuration.
 */
export async function fetchConfig(): Promise<AppConfig> {
  const response = await fetch(`${API_BASE}/api/config`);
  if (!response.ok) {
    throw new Error(`Failed to fetch configuration: ${response.status}`);
  }
  return response.json();
}

/**
 * Update A2A agent configuration.
 */
export async function updateA2AConfig(config: A2AConfigUpdate): Promise<ConfigUpdateResponse> {
  const response = await fetch(`${API_BASE}/api/config/a2a`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  if (!response.ok) {
    throw new Error("Failed to update A2A configuration");
  }
  return response.json();
}

/**
 * Update MCP server configuration.
 */
export async function updateMCPConfig(config: MCPConfigUpdate): Promise<ConfigUpdateResponse> {
  const response = await fetch(`${API_BASE}/api/config/mcp`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  if (!response.ok) {
    throw new Error("Failed to update MCP configuration");
  }
  return response.json();
}

/**
 * Test A2A agent connection.
 */
export async function testA2AConnection(config: ConnectionTestRequest): Promise<A2ATestResponse> {
  const response = await fetch(`${API_BASE}/api/config/a2a/test`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  if (!response.ok) {
    throw new Error("Failed to test A2A connection");
  }
  return response.json();
}

/**
 * Test MCP server connection.
 */
export async function testMCPConnection(config: ConnectionTestRequest): Promise<MCPTestResponse> {
  const response = await fetch(`${API_BASE}/api/config/mcp/test`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  if (!response.ok) {
    throw new Error("Failed to test MCP connection");
  }
  return response.json();
}

/**
 * Reset configuration to defaults.
 */
export async function resetConfig(): Promise<ConfigResetResponse> {
  const response = await fetch(`${API_BASE}/api/config/reset`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error("Failed to reset configuration");
  }
  return response.json();
}

/**
 * Add a new MCP server.
 */
export async function addMCPServer(
  server: MCPServerAdd
): Promise<ConfigUpdateResponse> {
  const response = await fetch(`${API_BASE}/api/config/mcp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(server),
  });
  if (!response.ok) {
    throw new Error("Failed to add MCP server");
  }
  return response.json();
}

/**
 * Update an existing MCP server.
 */
export async function updateMCPServer(
  serverId: string,
  updates: MCPServerUpdate
): Promise<ConfigUpdateResponse> {
  const response = await fetch(`${API_BASE}/api/config/mcp/${serverId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates),
  });
  if (!response.ok) {
    throw new Error("Failed to update MCP server");
  }
  return response.json();
}

/**
 * Delete an MCP server.
 */
export async function deleteMCPServer(
  serverId: string
): Promise<ConfigUpdateResponse> {
  const response = await fetch(`${API_BASE}/api/config/mcp/${serverId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error("Failed to delete MCP server");
  }
  return response.json();
}

// Conversation API Functions

/**
 * List all conversations.
 */
export async function listConversations(): Promise<Conversation[]> {
  const response = await fetch(`${API_BASE}/api/conversations`);
  if (!response.ok) {
    throw new Error(`Failed to list conversations: ${response.status}`);
  }
  return response.json();
}

/**
 * Create a new conversation.
 */
export async function createConversation(
  request?: CreateConversationRequest
): Promise<Conversation> {
  const response = await fetch(`${API_BASE}/api/conversations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request || {}),
  });
  if (!response.ok) {
    throw new Error(`Failed to create conversation: ${response.status}`);
  }
  return response.json();
}

/**
 * Get a specific conversation.
 */
export async function getConversation(conversationId: string): Promise<Conversation> {
  const response = await fetch(`${API_BASE}/api/conversations/${conversationId}`);
  if (!response.ok) {
    throw new Error(`Failed to get conversation: ${response.status}`);
  }
  return response.json();
}

/**
 * Update a conversation's title.
 */
export async function updateConversation(
  conversationId: string,
  request: UpdateConversationRequest
): Promise<Conversation> {
  const response = await fetch(`${API_BASE}/api/conversations/${conversationId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error(`Failed to update conversation: ${response.status}`);
  }
  return response.json();
}

/**
 * Delete a conversation.
 */
export async function deleteConversation(conversationId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/conversations/${conversationId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error(`Failed to delete conversation: ${response.status}`);
  }
}

// A2A Task API Functions (for planning-first flow)

export interface Plan {
  id: string;
  description: string;
  phases: Phase[];
  createdAt: string;
  approvedAt?: string;
}

export interface Phase {
  id: string;
  name: string;
  description?: string;
  tasks: TaskItem[];
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped';
}

export interface TaskItem {
  id: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped';
  error?: string;
}

export interface Task {
  id: string;
  status: {
    state: string;
    message?: string;
    timestamp: string;
  };
  plan?: Plan;
  artifacts?: unknown[];
  history?: unknown[];
  metadata?: Record<string, unknown>;
}

/**
 * Approve a task plan.
 */
export async function approvePlan(taskId: string): Promise<Task> {
  const response = await fetch(`${API_BASE}/a2a/tasks/${taskId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ approved: true }),
  });
  if (!response.ok) {
    throw new Error(`Failed to approve plan: ${response.status}`);
  }
  return response.json();
}

/**
 * Reject a task plan with feedback.
 */
export async function rejectPlan(taskId: string, feedback: string): Promise<Task> {
  const response = await fetch(`${API_BASE}/a2a/tasks/${taskId}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ feedback }),
  });
  if (!response.ok) {
    throw new Error(`Failed to reject plan: ${response.status}`);
  }
  return response.json();
}

/**
 * Pause a task.
 */
export async function pauseTask(taskId: string): Promise<Task> {
  const response = await fetch(`${API_BASE}/a2a/tasks/${taskId}/pause`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(`Failed to pause task: ${response.status}`);
  }
  return response.json();
}

/**
 * Resume a paused task.
 */
export async function resumeTask(taskId: string): Promise<Task> {
  const response = await fetch(`${API_BASE}/a2a/tasks/${taskId}/resume`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(`Failed to resume task: ${response.status}`);
  }
  return response.json();
}

/**
 * Cancel a task.
 */
export async function cancelTask(taskId: string): Promise<Task> {
  const response = await fetch(`${API_BASE}/a2a/tasks/${taskId}/cancel`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(`Failed to cancel task: ${response.status}`);
  }
  return response.json();
}
