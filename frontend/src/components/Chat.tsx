"use client";

import { useState, useRef, useEffect } from "react";
import { Sparkles } from "lucide-react";
import { streamChat, type ChatMessage } from "@/lib/api";
import { cn, formatDate, generateId } from "@/lib/utils";
import { InputToolbar, type InputToolbarRef } from "./InputToolbar";
import { ToolAccordion } from "./ToolAccordion";

interface Message extends ChatMessage {
  id: string;
  isStreaming?: boolean;
}

const QUICK_ACTIONS = [
  { label: "Show all orders", query: "Show me all orders" },
  { label: "Search by customer", query: "Show orders for customer 003KB000004r85iYAA" },
  { label: "Revenue summary", query: "What's our total revenue?" },
  { label: "Create an order", query: "Help me create a new order" },
];

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId] = useState(() => generateId());
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<InputToolbarRef>(null);

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

  // Empty state - Claude desktop style
  if (messages.length === 0) {
    return (
      <div className="flex flex-col h-full">
        {/* Centered content */}
        <div className="flex-1 flex flex-col items-center justify-center px-4 pb-8">
          {/* Agent branding */}
          <div className="flex items-center gap-3 mb-8">
            <Sparkles className="w-8 h-8 text-primary" />
            <h1 className="text-3xl font-serif font-bold text-foreground">
              Oz's Order Management Agent
            </h1>
          </div>

          {/* Input */}
          <div className="w-full max-w-2xl">
            <InputToolbar
              ref={inputRef}
              onSubmit={handleSubmit}
              isLoading={isLoading}
              placeholder="How can I help you today?"
            />
          </div>

          {/* Quick actions as subtle links */}
          <div className="flex flex-wrap justify-center gap-x-6 gap-y-2 mt-8">
            {QUICK_ACTIONS.map((action) => (
              <button
                key={action.label}
                onClick={() => handleSubmit(action.query)}
                className="text-sm text-muted-foreground hover:text-foreground transition-colors underline-offset-4 hover:underline"
              >
                {action.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Conversation view
  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "animate-fade-in",
                message.role === "user" ? "flex justify-end" : ""
              )}
            >
              {message.role === "user" ? (
                // User message - right aligned, subtle background
                <div className="max-w-[80%]">
                  <div className="bg-muted rounded-2xl rounded-br-md px-4 py-3">
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  </div>
                  <div className="text-[10px] text-muted-foreground/50 mt-1 text-right px-1">
                    {formatDate(message.timestamp)}
                  </div>
                </div>
              ) : (
                // Agent message - left aligned, clean styling
                <div className="max-w-full space-y-3">
                  {/* Tool usage accordion */}
                  {message.toolUse && (
                    <ToolAccordion
                      toolName={message.toolUse.tool}
                      toolInput={message.toolUse.input}
                      toolResult={message.toolResult}
                      isLoading={message.isStreaming && !message.toolResult}
                    />
                  )}

                  {/* Message content */}
                  {message.content && (
                    <div className="prose-agent">
                      <p className="whitespace-pre-wrap">
                        {message.content}
                        {message.isStreaming && message.content && (
                          <span className="inline-block w-1.5 h-4 bg-primary ml-0.5 animate-pulse" />
                        )}
                      </p>
                    </div>
                  )}

                  {/* Loading indicator when no content yet */}
                  {message.isStreaming && !message.content && !message.toolUse && (
                    <div className="flex gap-1.5 py-2">
                      <span className="w-2 h-2 bg-muted-foreground/40 rounded-full typing-dot" />
                      <span className="w-2 h-2 bg-muted-foreground/40 rounded-full typing-dot" />
                      <span className="w-2 h-2 bg-muted-foreground/40 rounded-full typing-dot" />
                    </div>
                  )}

                  {/* Timestamp */}
                  {!message.isStreaming && message.content && (
                    <div className="text-[10px] text-muted-foreground/50 px-1">
                      {formatDate(message.timestamp)}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input area */}
      <div className="border-t border-border/50 bg-background/80 backdrop-blur-sm p-4">
        <InputToolbar
          ref={inputRef}
          onSubmit={handleSubmit}
          isLoading={isLoading}
          placeholder="Ask about orders, customers, revenue..."
        />
      </div>
    </div>
  );
}
