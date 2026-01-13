"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Settings, Zap } from "lucide-react";
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
        <Chat />
      </main>
    </div>
  );
}
