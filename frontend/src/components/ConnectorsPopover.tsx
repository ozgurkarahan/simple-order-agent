"use client";

import { useState, useRef, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, Server, Settings } from "lucide-react";
import Link from "next/link";
import { fetchConfig, type AppConfig } from "@/lib/api";
import { cn } from "@/lib/utils";

interface ConnectorsPopoverProps {
  className?: string;
}

export function ConnectorsPopover({ className }: ConnectorsPopoverProps) {
  const [isOpen, setIsOpen] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);

  const { data: config } = useQuery<AppConfig>({
    queryKey: ["config"],
    queryFn: fetchConfig,
    retry: false,
    staleTime: 30000,
  });

  // Close popover when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (popoverRef.current && !popoverRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const mcpServers = config?.mcp_servers || [];
  const activeCount = mcpServers.filter(s => s.is_active).length;
  const totalCount = mcpServers.length;

  return (
    <div ref={popoverRef} className={cn("relative", className)}>
      {/* Trigger button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors",
          "hover:bg-muted border border-transparent",
          isOpen && "bg-muted border-border"
        )}
      >
        <span className="flex items-center justify-center w-5 h-5 rounded bg-primary/10 text-primary text-xs font-semibold">
          M
        </span>
        <span className="hidden sm:inline text-muted-foreground">
          {activeCount} / {totalCount} MCP
        </span>
        <ChevronDown
          className={cn(
            "w-3.5 h-3.5 text-muted-foreground transition-transform",
            isOpen && "rotate-180"
          )}
        />
      </button>

      {/* Popover content */}
      {isOpen && (
        <div className="absolute bottom-full left-0 mb-2 w-72 bg-card rounded-xl border border-border shadow-lg animate-fade-in z-50">
          {/* Header */}
          <div className="px-4 py-3 border-b border-border">
            <h3 className="font-medium text-sm">MCP Connectors</h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              {activeCount} of {totalCount} servers active
            </p>
          </div>

          {/* MCP Servers List */}
          <div className="p-2 max-h-80 overflow-y-auto">
            {mcpServers.length > 0 ? (
              mcpServers.map((server) => (
                <div
                  key={server.id}
                  className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50 transition-colors"
                >
                  {/* Icon */}
                  <div className="w-8 h-8 rounded-lg bg-orange-500/10 flex items-center justify-center">
                    <Server className="w-4 h-4 text-orange-500" />
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{server.name}</p>
                    <p className="text-xs text-muted-foreground truncate">
                      {server.url.replace(/^https?:\/\//, "").split("/")[0]}
                    </p>
                  </div>

                  {/* Status indicator */}
                  <div
                    className={cn(
                      "w-2 h-2 rounded-full",
                      server.is_active ? "bg-green-500" : "bg-muted-foreground"
                    )}
                    title={server.is_active ? "Active" : "Inactive"}
                  />
                </div>
              ))
            ) : (
              <div className="p-4 text-center">
                <p className="text-sm text-muted-foreground">No MCP servers configured</p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-4 py-3 border-t border-border">
            <Link
              href="/settings"
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <Settings className="w-4 h-4" />
              <span>Manage connectors</span>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
