/**
 * Conversation message storage using browser localStorage
 */

export interface StoredMessage {
  id: string;
  role: "user" | "agent";
  content: string;
  timestamp: string;
  toolUse?: { tool: string; input: Record<string, unknown> };
  toolResult?: string;
}

function getStorageKey(conversationId: string): string {
  return `conversation_messages_${conversationId}`;
}

/**
 * Save messages for a conversation to localStorage
 */
export function saveMessages(conversationId: string, messages: StoredMessage[]): void {
  try {
    localStorage.setItem(getStorageKey(conversationId), JSON.stringify(messages));
  } catch (error) {
    console.error("Failed to save messages to localStorage:", error);
  }
}

/**
 * Load messages for a conversation from localStorage
 */
export function loadMessages(conversationId: string): StoredMessage[] {
  try {
    const data = localStorage.getItem(getStorageKey(conversationId));
    return data ? JSON.parse(data) : [];
  } catch (error) {
    console.error("Failed to load messages from localStorage:", error);
    return [];
  }
}

/**
 * Delete messages for a specific conversation from localStorage
 */
export function deleteMessages(conversationId: string): void {
  try {
    localStorage.removeItem(getStorageKey(conversationId));
  } catch (error) {
    console.error("Failed to delete messages from localStorage:", error);
  }
}

/**
 * Clear all conversation messages from localStorage
 */
export function clearAllMessages(): void {
  try {
    Object.keys(localStorage)
      .filter(key => key.startsWith('conversation_messages_'))
      .forEach(key => localStorage.removeItem(key));
  } catch (error) {
    console.error("Failed to clear all messages from localStorage:", error);
  }
}
