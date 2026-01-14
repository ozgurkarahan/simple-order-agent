"use client";

import { useState, useRef, useEffect } from "react";
import { Sparkles } from "lucide-react";
import { streamChat, approvePlan, rejectPlan, pauseTask, resumeTask, cancelTask, type ChatMessage } from "@/lib/api";
import { cn, formatDate, generateId } from "@/lib/utils";
import { InputToolbar, type InputToolbarRef } from "./InputToolbar";
import { ToolAccordion } from "./ToolAccordion";
import { saveMessages, loadMessages } from "@/lib/conversation-storage";
import { PlanDisplay, type Plan } from "./PlanDisplay";

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

interface ChatProps {
  conversationId: string | null;
  onFirstMessage?: (message: string) => void;
}

export function Chat({ conversationId, onFirstMessage }: ChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [currentPlan, setCurrentPlan] = useState<Plan | null>(null);
  const [taskState, setTaskState] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<InputToolbarRef>(null);
  const firstMessageSent = useRef(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load messages when conversation changes
  useEffect(() => {
    if (conversationId) {
      // Load messages from localStorage
      const stored = loadMessages(conversationId);
      const loadedMessages: Message[] = stored.map(msg => ({
        ...msg,
        timestamp: new Date(msg.timestamp),
        isStreaming: false
      }));
      setMessages(loadedMessages);
      firstMessageSent.current = loadedMessages.length > 0;
    } else {
      setMessages([]);
      firstMessageSent.current = false;
    }

    // Reset plan state when switching conversations
    setCurrentTaskId(null);
    setCurrentPlan(null);
    setTaskState('');
  }, [conversationId]);

  // Save messages to localStorage whenever they change
  useEffect(() => {
    if (conversationId && messages.length > 0) {
      const storedMessages = messages.map(msg => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp.toISOString(),
        toolUse: msg.toolUse,
        toolResult: msg.toolResult
      }));
      saveMessages(conversationId, storedMessages);
    }
  }, [messages, conversationId]);

  // Plan control handlers
  const handleApprovePlan = async () => {
    if (!currentTaskId) return;
    try {
      await approvePlan(currentTaskId);
      // The status will be updated via SSE events
    } catch (error) {
      console.error('Failed to approve plan:', error);
      // TODO: Show error to user
    }
  };

  const handleRejectPlan = async (feedback: string) => {
    if (!currentTaskId) return;
    try {
      await rejectPlan(currentTaskId, feedback);
      // The agent will generate a new plan, which will come via SSE events
    } catch (error) {
      console.error('Failed to reject plan:', error);
      // TODO: Show error to user
    }
  };

  const handlePausePlan = async () => {
    if (!currentTaskId) return;
    try {
      await pauseTask(currentTaskId);
    } catch (error) {
      console.error('Failed to pause task:', error);
    }
  };

  const handleResumePlan = async () => {
    if (!currentTaskId) return;
    try {
      await resumeTask(currentTaskId);
    } catch (error) {
      console.error('Failed to resume task:', error);
    }
  };

  const handleCancelPlan = async () => {
    if (!currentTaskId) return;
    try {
      await cancelTask(currentTaskId);
    } catch (error) {
      console.error('Failed to cancel task:', error);
    }
  };

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

    // Notify parent about first message for title generation
    if (!firstMessageSent.current && onFirstMessage) {
      onFirstMessage(text.trim());
      firstMessageSent.current = true;
    }

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
        if (event.type === "status") {
          // Handle task status updates and plan generation
          const statusData = event.data as any;

          // Extract taskId from status event
          if (statusData.taskId) {
            setCurrentTaskId(statusData.taskId);
          }

          // Extract task state
          if (statusData.status?.state) {
            const newState = statusData.status.state;
            setTaskState(newState);

            // Clear plan when task completes, fails, or is canceled
            if (newState === 'completed' || newState === 'failed' || newState === 'canceled') {
              setCurrentPlan(null);
              setCurrentTaskId(null);
            }
          }

          // Extract plan if present
          if (statusData.plan) {
            setCurrentPlan(statusData.plan);
          }
        } else if (event.type === "plan_update") {
          // Handle real-time plan progress updates
          const updateData = event.data as any;
          if (updateData.plan) {
            setCurrentPlan(updateData.plan);
          }
        } else if (event.type === "message" && event.data.content) {
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
                  {/* Plan display - show when plan exists and is the latest message */}
                  {currentPlan && message.id === messages[messages.length - 1]?.id && (
                    <PlanDisplay
                      plan={currentPlan}
                      isExecuting={taskState === 'executing'}
                      onApprove={handleApprovePlan}
                      onReject={handleRejectPlan}
                      onPause={handlePausePlan}
                      onResume={handleResumePlan}
                      onCancel={handleCancelPlan}
                      showApprovalButtons={taskState === 'awaiting-approval'}
                      showExecutionControls={taskState === 'executing' || taskState === 'paused'}
                      isPaused={taskState === 'paused'}
                    />
                  )}

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
                  {message.isStreaming && !message.content && !message.toolUse && !currentPlan && (
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
