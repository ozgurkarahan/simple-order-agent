"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Shield, Zap, Tag, BookOpen, Globe, Key } from "lucide-react";
import type { AgentCard } from "@/lib/api";

interface AgentCardDisplayProps {
  agentCard: AgentCard;
}

export default function AgentCardDisplay({ agentCard }: AgentCardDisplayProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="mt-4 border border-border rounded-lg bg-gradient-to-br from-primary/5 to-transparent overflow-hidden transition-all duration-300">
      {/* Header - Always visible */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-primary/5 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            <Shield className="w-5 h-5 text-primary" />
          </div>
          <div className="text-left">
            <h3 className="font-semibold text-foreground">
              {agentCard.name} <span className="text-sm text-muted-foreground">v{agentCard.version}</span>
            </h3>
            <p className="text-sm text-muted-foreground line-clamp-1">{agentCard.description}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">{isExpanded ? "Hide Details" : "Show Details"}</span>
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-muted-foreground" />
          ) : (
            <ChevronDown className="w-5 h-5 text-muted-foreground" />
          )}
        </div>
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="px-4 pb-4 space-y-6 animate-in fade-in duration-300">
          {/* Capabilities */}
          <div>
            <h4 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
              <Zap className="w-4 h-4 text-orange-500" />
              Capabilities
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <div
                className={`px-3 py-2 rounded-lg border ${
                  agentCard.capabilities.streaming
                    ? "bg-green-500/10 border-green-500/20 text-green-700 dark:text-green-400"
                    : "bg-muted border-border text-muted-foreground"
                }`}
              >
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${agentCard.capabilities.streaming ? "bg-green-500" : "bg-muted-foreground"}`} />
                  <span className="text-xs font-medium">Streaming</span>
                </div>
              </div>
              <div
                className={`px-3 py-2 rounded-lg border ${
                  agentCard.capabilities.pushNotifications
                    ? "bg-blue-500/10 border-blue-500/20 text-blue-700 dark:text-blue-400"
                    : "bg-muted border-border text-muted-foreground"
                }`}
              >
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${agentCard.capabilities.pushNotifications ? "bg-blue-500" : "bg-muted-foreground"}`} />
                  <span className="text-xs font-medium">Push Notifications</span>
                </div>
              </div>
              <div
                className={`px-3 py-2 rounded-lg border ${
                  agentCard.capabilities.stateTransitionHistory
                    ? "bg-purple-500/10 border-purple-500/20 text-purple-700 dark:text-purple-400"
                    : "bg-muted border-border text-muted-foreground"
                }`}
              >
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${agentCard.capabilities.stateTransitionHistory ? "bg-purple-500" : "bg-muted-foreground"}`} />
                  <span className="text-xs font-medium">State History</span>
                </div>
              </div>
            </div>
          </div>

          {/* Skills */}
          <div>
            <h4 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
              <Tag className="w-4 h-4 text-blue-500" />
              Skills ({agentCard.skills.length})
            </h4>
            <div className="space-y-3">
              {agentCard.skills.map((skill) => (
                <div key={skill.id} className="bg-card border border-border rounded-lg p-3">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h5 className="font-medium text-sm text-foreground">{skill.name}</h5>
                    {skill.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {skill.tags.map((tag) => (
                          <span
                            key={tag}
                            className="px-2 py-0.5 text-xs bg-primary/10 text-primary rounded-full"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground mb-2">{skill.description}</p>
                  {skill.examples.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs font-medium text-muted-foreground mb-1">Example queries:</p>
                      <ul className="space-y-1">
                        {skill.examples.slice(0, 2).map((example, idx) => (
                          <li key={idx} className="text-xs text-muted-foreground pl-3 border-l-2 border-primary/30">
                            &quot;{example}&quot;
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Authentication */}
          {agentCard.authentication && (
            <div>
              <h4 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
                <Key className="w-4 h-4 text-yellow-500" />
                Authentication
              </h4>
              <div className="bg-card border border-border rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-foreground">Type: {agentCard.authentication.type}</p>
                    {agentCard.authentication.credentialsUrl && (
                      <a
                        href={agentCard.authentication.credentialsUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-primary hover:underline"
                      >
                        Get credentials →
                      </a>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Links */}
          <div>
            <h4 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
              <Globe className="w-4 h-4 text-green-500" />
              Links
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <a
                href={agentCard.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-3 py-2 bg-card border border-border rounded-lg hover:bg-primary/5 transition-colors text-sm"
              >
                <Globe className="w-4 h-4 text-primary" />
                <span className="text-foreground">Agent URL</span>
              </a>
              {agentCard.documentationUrl && (
                <a
                  href={agentCard.documentationUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 px-3 py-2 bg-card border border-border rounded-lg hover:bg-primary/5 transition-colors text-sm"
                >
                  <BookOpen className="w-4 h-4 text-blue-500" />
                  <span className="text-foreground">Documentation</span>
                </a>
              )}
            </div>
          </div>

          {/* Input/Output Modes */}
          {(agentCard.defaultInputModes || agentCard.defaultOutputModes) && (
            <div className="grid grid-cols-2 gap-4 text-xs">
              {agentCard.defaultInputModes && agentCard.defaultInputModes.length > 0 && (
                <div>
                  <p className="font-medium text-muted-foreground mb-1">Input Modes:</p>
                  <div className="flex flex-wrap gap-1">
                    {agentCard.defaultInputModes.map((mode) => (
                      <span key={mode} className="px-2 py-1 bg-secondary rounded text-secondary-foreground">
                        {mode}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {agentCard.defaultOutputModes && agentCard.defaultOutputModes.length > 0 && (
                <div>
                  <p className="font-medium text-muted-foreground mb-1">Output Modes:</p>
                  <div className="flex flex-wrap gap-1">
                    {agentCard.defaultOutputModes.map((mode) => (
                      <span key={mode} className="px-2 py-1 bg-secondary rounded text-secondary-foreground">
                        {mode}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
