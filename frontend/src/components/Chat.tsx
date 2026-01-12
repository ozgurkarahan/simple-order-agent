"use client";

import { useState, useRef, useEffect } from "react";
import {
  Send,
  Loader2,
  User,
  Bot,
  Wrench,
  Sparkles,
} from "lucide-react";
import { streamChat, type ChatMessage } from "@/lib/api";
import { cn, formatDate, generateId } from "@/lib/utils";

interface Message extends ChatMessage {
  id: string;
  isStreaming?: boolean;
}

const QUICK_ACTIONS = [
  "Show me all orders from last week",
  "What are our top-selling products?",
  "List pending orders",
  "What's today's revenue?",
];

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId] = useState(() => generateId());
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMessage: Message = {
      id: generateId(),
      role: "user",
      content: text.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    // Create placeholder for agent response
    const agentMessageId = generateId();
    const agentMessage: Message = {
      id: agentMessageId,
      role: "agent",
      content: "",
      timestamp: new Date(),
      isStreaming: true,
    };

    setMessages((prev) => [...prev, agentMessage]);

    try {
      for await (const event of streamChat(text, conversationId)) {
        if (event.type === "message" && event.data.content) {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === agentMessageId
                ? { ...m, content: m.content + event.data.content }
                : m
            )
          );
        } else if (event.type === "tool_use") {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === agentMessageId
                ? {
                    ...m,
                    toolUse: {
                      tool: event.data.tool || "",
                      input: event.data.input || {},
                    },
                  }
                : m
            )
          );
        } else if (event.type === "tool_result") {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === agentMessageId
                ? { ...m, toolResult: event.data.result }
                : m
            )
          );
        } else if (event.type === "error") {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === agentMessageId
                ? {
                    ...m,
                    content: `Error: ${event.data.error}`,
                    isStreaming: false,
                  }
                : m
            )
          );
          break;
        }
      }
    } catch (error) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === agentMessageId
            ? {
                ...m,
                content: `Error: ${error instanceof Error ? error.message : "Unknown error"}`,
                isStreaming: false,
              }
            : m
        )
      );
    } finally {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === agentMessageId ? { ...m, isStreaming: false } : m
        )
      );
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(input);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
              <Sparkles className="w-8 h-8 text-primary" />
            </div>
            <h2 className="text-xl font-semibold mb-2">Orders Analytics Agent</h2>
            <p className="text-muted-foreground max-w-md mb-6">
              Ask me anything about your orders. I can help you analyze data,
              look up specific orders, or create new ones.
            </p>
            <div className="flex flex-wrap gap-2 justify-center max-w-lg">
              {QUICK_ACTIONS.map((action) => (
                <button
                  key={action}
                  onClick={() => handleSubmit(action)}
                  className="px-3 py-1.5 text-sm bg-muted hover:bg-muted/80 rounded-full transition-colors"
                >
                  {action}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex gap-3 animate-fade-in",
                message.role === "user" ? "flex-row-reverse" : ""
              )}
            >
              <div
                className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
                  message.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted"
                )}
              >
                {message.role === "user" ? (
                  <User className="w-4 h-4" />
                ) : (
                  <Bot className="w-4 h-4" />
                )}
              </div>

              <div
                className={cn(
                  "max-w-[80%] space-y-2",
                  message.role === "user" ? "items-end" : ""
                )}
              >
                {/* Tool use indicator */}
                {message.toolUse && (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted/50 px-2 py-1 rounded">
                    <Wrench className="w-3 h-3" />
                    Using {message.toolUse.tool}
                  </div>
                )}

                {/* Message content */}
                <div
                  className={cn(
                    "px-4 py-2.5 rounded-2xl",
                    message.role === "user"
                      ? "bg-primary text-primary-foreground rounded-br-md"
                      : "bg-card border border-border rounded-bl-md"
                  )}
                >
                  <div className="prose-agent whitespace-pre-wrap">
                    {message.content}
                    {message.isStreaming && (
                      <span className="inline-flex gap-1 ml-1">
                        <span className="w-1.5 h-1.5 bg-current rounded-full typing-dot" />
                        <span className="w-1.5 h-1.5 bg-current rounded-full typing-dot" />
                        <span className="w-1.5 h-1.5 bg-current rounded-full typing-dot" />
                      </span>
                    )}
                  </div>
                </div>

                {/* Timestamp */}
                <div
                  className={cn(
                    "text-[10px] text-muted-foreground px-1",
                    message.role === "user" ? "text-right" : ""
                  )}
                >
                  {formatDate(message.timestamp)}
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-border p-4">
        <div className="flex gap-2 items-end">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about orders..."
              rows={1}
              className="w-full resize-none rounded-xl border border-input bg-background px-4 py-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
              disabled={isLoading}
            />
          </div>
          <button
            onClick={() => handleSubmit(input)}
            disabled={!input.trim() || isLoading}
            className="h-11 w-11 rounded-xl bg-primary text-primary-foreground flex items-center justify-center hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
