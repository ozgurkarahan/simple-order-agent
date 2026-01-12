"use client";

import { useQuery } from "@tanstack/react-query";
import {
  LayoutDashboard,
  MessageSquare,
  Package,
  Settings,
  Sparkles,
  ChevronRight,
} from "lucide-react";
import { fetchAgentCard } from "@/lib/api";
import { cn } from "@/lib/utils";

interface SidebarProps {
  activeView: "chat" | "dashboard" | "orders";
  onViewChange: (view: "chat" | "dashboard" | "orders") => void;
}

export function Sidebar({ activeView, onViewChange }: SidebarProps) {
  const { data: agentCard, isLoading } = useQuery({
    queryKey: ["agentCard"],
    queryFn: fetchAgentCard,
    retry: false,
  });

  const navItems = [
    { id: "chat" as const, label: "Chat", icon: MessageSquare },
    { id: "dashboard" as const, label: "Analytics", icon: LayoutDashboard },
    { id: "orders" as const, label: "Orders", icon: Package },
  ];

  return (
    <aside className="w-64 h-screen bg-card border-r border-border flex flex-col">
      {/* Logo */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h1 className="font-semibold text-sm">Orders Agent</h1>
            <p className="text-xs text-muted-foreground">Analytics Dashboard</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3">
        <ul className="space-y-1">
          {navItems.map((item) => (
            <li key={item.id}>
              <button
                onClick={() => onViewChange(item.id)}
                className={cn(
                  "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                  activeView === item.id
                    ? "bg-primary/10 text-primary font-medium"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <item.icon className="w-4 h-4" />
                {item.label}
                {activeView === item.id && (
                  <ChevronRight className="w-4 h-4 ml-auto" />
                )}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      {/* Agent Card Info */}
      <div className="p-3 border-t border-border">
        <div className="bg-muted rounded-lg p-3">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-xs font-medium">A2A Agent</span>
          </div>
          {isLoading ? (
            <div className="text-xs text-muted-foreground">Loading...</div>
          ) : agentCard ? (
            <div className="space-y-1">
              <p className="text-xs font-medium">{agentCard.name}</p>
              <p className="text-xs text-muted-foreground">v{agentCard.version}</p>
              <div className="flex flex-wrap gap-1 mt-2">
                {agentCard.capabilities.streaming && (
                  <span className="text-[10px] px-1.5 py-0.5 bg-primary/10 text-primary rounded">
                    Streaming
                  </span>
                )}
              </div>
            </div>
          ) : (
            <div className="text-xs text-destructive">Agent unavailable</div>
          )}
        </div>
      </div>

      {/* Settings */}
      <div className="p-3 border-t border-border">
        <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-muted-foreground hover:bg-muted hover:text-foreground transition-colors">
          <Settings className="w-4 h-4" />
          Settings
        </button>
      </div>
    </aside>
  );
}
