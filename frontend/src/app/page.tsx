"use client";

import { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { Settings, Zap } from "lucide-react";
import { Chat } from "@/components/Chat";
import ConversationSidebar from "@/components/ConversationSidebar";
import {
  fetchAgentCard,
  listConversations,
  createConversation,
  updateConversation,
  deleteConversation,
  type Conversation,
} from "@/lib/api";
import { deleteMessages } from "@/lib/conversation-storage";

export default function Home() {
  const queryClient = useQueryClient();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const hasInitialized = useRef(false);

  const { data: agentCard } = useQuery({
    queryKey: ["agentCard"],
    queryFn: fetchAgentCard,
    retry: false,
  });

  const { data: conversations = [] } = useQuery({
    queryKey: ["conversations"],
    queryFn: listConversations,
  });

  const createConversationMutation = useMutation({
    mutationFn: () => createConversation(),
    onSuccess: (newConversation) => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      setActiveConversationId(newConversation.id);
    },
  });

  const updateConversationMutation = useMutation({
    mutationFn: ({ id, title }: { id: string; title: string }) =>
      updateConversation(id, { title }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });

  const deleteConversationMutation = useMutation({
    mutationFn: (id: string) => deleteConversation(id),
    onSuccess: async (_, deletedId) => {
      // Delete messages from localStorage
      deleteMessages(deletedId);
      
      // Invalidate and refetch conversations
      await queryClient.invalidateQueries({ queryKey: ["conversations"] });
      
      // If deleted conversation was active, switch to another or create new
      if (activeConversationId === deletedId) {
        // Get the updated list after deletion
        const updatedConversations = queryClient.getQueryData<Conversation[]>(["conversations"]) || [];
        const remaining = updatedConversations.filter((c) => c.id !== deletedId);
        
        if (remaining.length > 0) {
          setActiveConversationId(remaining[0].id);
        } else {
          // No conversations left, create a new one
          setActiveConversationId(null);
          handleNewConversation();
        }
      }
    },
  });

  // Create initial conversation on mount
  useEffect(() => {
    // Only run initialization once
    if (hasInitialized.current) return;
    
    // Don't create if already creating
    if (createConversationMutation.isPending) return;
    
    if (conversations.length === 0 && !activeConversationId) {
      hasInitialized.current = true;
      createConversationMutation.mutate();
    } else if (conversations.length > 0 && !activeConversationId) {
      hasInitialized.current = true;
      // Select most recent conversation
      setActiveConversationId(conversations[0].id);
    }
  }, [conversations, activeConversationId, createConversationMutation]);

  const handleNewConversation = () => {
    createConversationMutation.mutate();
  };

  const handleSelectConversation = (conversationId: string) => {
    setActiveConversationId(conversationId);
  };

  const handleRenameConversation = (conversationId: string, newTitle: string) => {
    updateConversationMutation.mutate({ id: conversationId, title: newTitle });
  };

  const handleDeleteConversation = (conversationId: string) => {
    deleteConversationMutation.mutate(conversationId);
  };

  const handleFirstMessage = (message: string) => {
    // The backend will auto-generate the title from the first message
    // Just refresh the conversation list after a short delay
    setTimeout(() => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    }, 1000);
  };

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Conversation Sidebar */}
      <ConversationSidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onRenameConversation={handleRenameConversation}
        onDeleteConversation={handleDeleteConversation}
      />

      {/* Main content */}
      <div
        className={`flex flex-col h-full transition-all duration-300 ${
          isSidebarOpen ? "lg:pl-[280px]" : ""
        }`}
      >
        {/* Minimal header */}
        <header className="flex items-center justify-end gap-3 px-4 py-3">
          {/* Status indicators */}
          {agentCard && (
            <div className="flex items-center gap-3">
              {agentCard.capabilities?.streaming && (
                <div className="flex items-center gap-1.5 px-2 py-1 bg-primary/10 rounded-full">
                  <Zap className="w-3 h-3 text-primary" />
                  <span className="text-xs font-medium text-primary">Streaming</span>
                </div>
              )}
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-green-500" />
                <span className="text-xs text-muted-foreground">Online</span>
              </div>
            </div>
          )}

          {/* Settings link */}
          <Link
            href="/settings"
            className="p-2 text-muted-foreground hover:text-foreground transition-colors rounded-lg hover:bg-muted"
            title="Settings"
          >
            <Settings className="w-5 h-5" />
          </Link>
        </header>

        {/* Chat - takes full remaining height */}
        <main className="flex-1 overflow-hidden">
          <Chat
            conversationId={activeConversationId}
            onFirstMessage={handleFirstMessage}
          />
        </main>
      </div>
    </div>
  );
}
