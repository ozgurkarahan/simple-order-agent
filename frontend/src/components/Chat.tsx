"use client";

import { useState, useRef, useEffect } from "react";
import {
  Send,
  Loader2,
  User,
  Bot,
  Wrench,
  Sparkles,
  Package,
  Search,
  PlusCircle,
} from "lucide-react";
import { streamChat, type ChatMessage } from "@/lib/api";
import { cn, formatDate, generateId } from "@/lib/utils";

interface Message extends ChatMessage {
  id: string;
  isStreaming?: boolean;
}

const QUICK_ACTIONS = [
  { label: "Show all orders", icon: Package, query: "Show me all orders" },
  { label: "Search customer", icon: Search, query: "Show orders for customer 003KB000004r85iYAA" },
  { label: "Revenue summary", icon: Sparkles, query: "What's our total revenue?" },
  { label: "Create order", icon: PlusCircle, query: "Help me create a new order" },
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
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center mb-6 shadow-lg">
              <Sparkles className="w-10 h-10 text-primary" />
            </div>
            <h2 className="text-2xl font-bold mb-2">How can I help you today?</h2>
            <p className="text-muted-foreground max-w-md mb-8">
              I can help you analyze orders, look up customer data, track revenue, 
              and manage your order system using natural language.
            </p>
            
            {/* Quick Actions Grid */}
            <div className="grid grid-cols-2 gap-3 w-full max-w-md">
              {QUICK_ACTIONS.map((action) => (
                <button
                  key={action.label}
                  onClick={() => handleSubmit(action.query)}
                  className="flex items-center gap-3 p-4 text-left bg-card hover:bg-muted border border-border rounded-xl transition-all hover:scale-[1.02] hover:shadow-md"
                >
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                    <action.icon className="w-5 h-5 text-primary" />
                  </div>
                  <span className="text-sm font-medium">{action.label}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex gap-3 sm:gap-4 animate-fade-in",
                message.role === "user" ? "flex-row-reverse" : ""
              )}
            >
              <div
                className={cn(
                  "w-9 h-9 rounded-xl flex items-center justify-center shrink-0",
                  message.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-gradient-to-br from-muted to-muted/50 border border-border"
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
                  "max-w-[85%] sm:max-w-[75%] space-y-2",
                  message.role === "user" ? "items-end" : ""
                )}
              >
                {/* Tool use indicator */}
                {message.toolUse && (
                  <div className="inline-flex items-center gap-2 text-xs text-muted-foreground bg-muted/50 px-3 py-1.5 rounded-lg border border-border/50">
                    <Wrench className="w-3.5 h-3.5 animate-pulse" />
                    <span>Fetching data with <code className="font-mono text-primary">{message.toolUse.tool}</code></span>
                  </div>
                )}

                {/* Message content */}
                <div
                  className={cn(
                    "px-4 py-3 rounded-2xl",
                    message.role === "user"
                      ? "bg-primary text-primary-foreground rounded-br-md"
                      : "bg-card border border-border rounded-bl-md shadow-sm"
                  )}
                >
                  <div className="prose-agent whitespace-pre-wrap text-sm leading-relaxed">
                    {message.content}
                    {message.isStreaming && !message.content && (
                      <span className="inline-flex gap-1">
                        <span className="w-2 h-2 bg-current rounded-full typing-dot opacity-60" />
                        <span className="w-2 h-2 bg-current rounded-full typing-dot opacity-60" />
                        <span className="w-2 h-2 bg-current rounded-full typing-dot opacity-60" />
                      </span>
                    )}
                    {message.isStreaming && message.content && (
                      <span className="inline-block w-2 h-4 bg-current ml-0.5 animate-pulse" />
                    )}
                  </div>
                </div>

                {/* Timestamp */}
                <div
                  className={cn(
                    "text-[10px] text-muted-foreground/60 px-1",
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
      <div className="border-t border-border bg-card/50 backdrop-blur-sm p-4">
        <div className="max-w-3xl mx-auto">
          <div className="flex gap-3 items-end">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about orders, customers, revenue..."
                rows={1}
                className="w-full resize-none rounded-xl border border-input bg-background px-4 py-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent disabled:opacity-50 transition-all"
                disabled={isLoading}
              />
            </div>
            <button
              onClick={() => handleSubmit(input)}
              disabled={!input.trim() || isLoading}
              className="h-12 w-12 rounded-xl bg-primary text-primary-foreground flex items-center justify-center hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all hover:scale-105 active:scale-95 shadow-lg shadow-primary/20"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
          <p className="text-[10px] text-muted-foreground/50 text-center mt-2">
            Press Enter to send • Shift+Enter for new line
          </p>
        </div>
      </div>
    </div>
  );
}
