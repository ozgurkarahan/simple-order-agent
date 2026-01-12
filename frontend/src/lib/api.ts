/**
 * API client for communicating with the Orders Agent backend.
 */

const API_BASE = "";

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

export interface AgentCard {
  name: string;
  description: string;
  version: string;
  url: string;
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

/**
 * Fetch the agent card for A2A discovery.
 */
export async function fetchAgentCard(): Promise<AgentCard> {
  const response = await fetch(`${API_BASE}/.well-known/agent.json`);
  if (!response.ok) {
    throw new Error("Failed to fetch agent card");
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
