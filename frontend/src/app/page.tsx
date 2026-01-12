"use client";

import { useQuery } from "@tanstack/react-query";
import { Sparkles, Zap, MessageSquare } from "lucide-react";
import { Chat } from "@/components/Chat";
import { fetchAgentCard } from "@/lib/api";

export default function Home() {
  const { data: agentCard } = useQuery({
    queryKey: ["agentCard"],
    queryFn: fetchAgentCard,
    retry: false,
  });

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center shadow-lg shadow-primary/20">
              <Sparkles className="w-5 h-5 text-primary-foreground" />
            </div>
            <div>
              <h1 className="font-semibold text-lg">Orders Analytics Agent</h1>
              <p className="text-xs text-muted-foreground">
                AI-powered order insights
              </p>
            </div>
          </div>

          {/* Agent Status */}
          <div className="flex items-center gap-4">
            {agentCard && (
              <>
                <div className="hidden sm:flex items-center gap-2 text-xs text-muted-foreground">
                  <MessageSquare className="w-3.5 h-3.5" />
                  <span>{agentCard.skills?.length || 0} skills</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                  <span className="text-xs font-medium text-green-500">Online</span>
                </div>
              </>
            )}
            {agentCard?.capabilities?.streaming && (
              <div className="hidden sm:flex items-center gap-1.5 px-2 py-1 bg-primary/10 rounded-full">
                <Zap className="w-3 h-3 text-primary" />
                <span className="text-xs font-medium text-primary">Streaming</span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Chat */}
      <main className="flex-1 overflow-hidden">
        <div className="max-w-4xl mx-auto h-full">
          <Chat />
        </div>
      </main>
    </div>
  );
}
