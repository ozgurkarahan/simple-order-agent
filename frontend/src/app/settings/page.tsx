"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Settings,
  Server,
  Globe,
  Plus,
  X,
  Check,
  AlertCircle,
  Loader2,
  RotateCcw,
  Save,
  Edit2,
  Trash2,
} from "lucide-react";
import {
  fetchConfig,
  updateA2AConfig,
  addMCPServer,
  updateMCPServer,
  deleteMCPServer,
  testA2AConnection,
  testMCPConnection,
  resetConfig,
  type AppConfig,
  type MCPServerConfig,
  type A2ATestResponse,
  type MCPTestResponse,
  type AgentCard,
} from "@/lib/api";
import AgentCardDisplay from "@/components/AgentCardDisplay";

interface HeaderEntry {
  key: string;
  value: string;
}

function HeadersEditor({
  headers,
  onChange,
  placeholder = "Add custom headers",
}: {
  headers: Record<string, string>;
  onChange: (headers: Record<string, string>) => void;
  placeholder?: string;
}) {
  const [entries, setEntries] = useState<HeaderEntry[]>([]);

  useEffect(() => {
    const headerEntries = Object.entries(headers).map(([key, value]) => ({
      key,
      value,
    }));
    setEntries(headerEntries.length > 0 ? headerEntries : []);
  }, [headers]);

  const updateHeaders = (newEntries: HeaderEntry[]) => {
    setEntries(newEntries);
    const newHeaders: Record<string, string> = {};
    newEntries.forEach(({ key, value }) => {
      if (key.trim()) {
        newHeaders[key.trim()] = value;
      }
    });
    onChange(newHeaders);
  };

  const addHeader = () => {
    updateHeaders([...entries, { key: "", value: "" }]);
  };

  const removeHeader = (index: number) => {
    const newEntries = entries.filter((_, i) => i !== index);
    updateHeaders(newEntries);
  };

  const updateEntry = (index: number, field: "key" | "value", val: string) => {
    const newEntries = [...entries];
    newEntries[index] = { ...newEntries[index], [field]: val };
    updateHeaders(newEntries);
  };

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-muted-foreground">
        Custom Headers (optional)
      </label>
      {entries.map((entry, index) => (
        <div key={index} className="flex gap-2">
          <input
            type="text"
            placeholder="Key"
            value={entry.key}
            onChange={(e) => updateEntry(index, "key", e.target.value)}
            className="flex-1 px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
          <input
            type="text"
            placeholder="Value"
            value={entry.value}
            onChange={(e) => updateEntry(index, "value", e.target.value)}
            className="flex-1 px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
          <button
            type="button"
            onClick={() => removeHeader(index)}
            aria-label="Remove header"
            className="p-2 text-muted-foreground hover:text-destructive transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={addHeader}
        className="flex items-center gap-2 text-sm text-primary hover:text-primary/80 transition-colors"
      >
        <Plus className="w-4 h-4" />
        Add Header
      </button>
    </div>
  );
}

interface MCPServerCardProps {
  server: MCPServerConfig;
  onTest: () => void;
  onUpdate: (updates: { name?: string; url?: string; headers?: Record<string, string>; is_active?: boolean }) => void;
  onDelete: () => void;
  testResult: MCPTestResponse | null;
  isTestPending: boolean;
}

function MCPServerCard({ server, onTest, onUpdate, onDelete, testResult, isTestPending }: MCPServerCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [name, setName] = useState(server.name);
  const [url, setUrl] = useState(server.url);
  const [headers, setHeaders] = useState(server.headers);

  const handleSave = () => {
    onUpdate({ name, url, headers });
    setIsEditing(false);
  };

  const handleCancel = () => {
    setName(server.name);
    setUrl(server.url);
    setHeaders(server.headers);
    setIsEditing(false);
  };

  return (
    <div className="bg-card rounded-xl border border-border p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
            <Server className="w-5 h-5 text-orange-500" />
          </div>
          {isEditing ? (
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="px-3 py-1 bg-background border border-border rounded-lg text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          ) : (
            <h3 className="font-semibold">{server.name}</h3>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onUpdate({ is_active: !server.is_active })}
            className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
              server.is_active
                ? "bg-green-500/10 text-green-500 hover:bg-green-500/20"
                : "bg-muted text-muted-foreground hover:bg-muted/80"
            }`}
          >
            {server.is_active ? "Active" : "Inactive"}
          </button>
          {!isEditing && (
            <>
              <button
                onClick={() => setIsEditing(true)}
                className="p-2 text-muted-foreground hover:text-foreground transition-colors"
                aria-label="Edit server"
              >
                <Edit2 className="w-4 h-4" />
              </button>
              <button
                onClick={onDelete}
                className="p-2 text-muted-foreground hover:text-destructive transition-colors"
                aria-label="Delete server"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </>
          )}
        </div>
      </div>

      {isEditing ? (
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-muted-foreground">Server URL</label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://..."
              className="mt-1 w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>
          <HeadersEditor headers={headers} onChange={setHeaders} />
          <div className="flex items-center gap-2 justify-end">
            <button
              onClick={handleCancel}
              className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
            >
              <Save className="w-4 h-4" />
              Save Changes
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground truncate">{server.url}</p>
          <div className="flex items-center gap-4">
            <button
              onClick={onTest}
              disabled={isTestPending}
              className="flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors disabled:opacity-50"
            >
              {isTestPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Server className="w-4 h-4" />
              )}
              Test Connection
            </button>
            {testResult && (
              <div className={`flex items-center gap-2 text-sm ${testResult.success ? "text-green-500" : "text-destructive"}`}>
                {testResult.success ? (
                  <>
                    <Check className="w-4 h-4" />
                    <span>{testResult.tools?.length || 0} tools available</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-4 h-4" />
                    <span>{testResult.error}</span>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function SettingsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  // Form state
  const [a2aUrl, setA2aUrl] = useState("http://localhost:8000");
  const [a2aHeaders, setA2aHeaders] = useState<Record<string, string>>({});
  
  // Add new server form
  const [showAddServer, setShowAddServer] = useState(false);
  const [newServerName, setNewServerName] = useState("");
  const [newServerUrl, setNewServerUrl] = useState("");
  const [newServerHeaders, setNewServerHeaders] = useState<Record<string, string>>({});

  // Test results
  const [a2aTestResult, setA2aTestResult] = useState<A2ATestResponse | null>(null);
  const [mcpTestResults, setMcpTestResults] = useState<Record<string, MCPTestResponse>>({});
  
  // Agent card state
  const [agentCard, setAgentCard] = useState<AgentCard | null>(null);

  // Fetch config
  const { data: config, isLoading, error } = useQuery({
    queryKey: ["config"],
    queryFn: fetchConfig,
    retry: false,
  });

  // Update form when config loads
  useEffect(() => {
    if (config) {
      setA2aUrl(config.a2a.url);
      setA2aHeaders(config.a2a.headers);
    }
  }, [config]);

  // Mutations
  const updateA2AMutation = useMutation({
    mutationFn: updateA2AConfig,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["config"] }),
  });

  const addServerMutation = useMutation({
    mutationFn: addMCPServer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["config"] });
      setShowAddServer(false);
      setNewServerName("");
      setNewServerUrl("");
      setNewServerHeaders({});
    },
  });

  const updateServerMutation = useMutation({
    mutationFn: ({ serverId, updates }: { serverId: string; updates: any }) =>
      updateMCPServer(serverId, updates),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["config"] }),
  });

  const deleteServerMutation = useMutation({
    mutationFn: deleteMCPServer,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["config"] }),
  });

  const testA2AMutation = useMutation({
    mutationFn: testA2AConnection,
    onSuccess: (data) => {
      setA2aTestResult(data);
      if (data.success && data.agent_card) {
        setAgentCard(data.agent_card);
      } else {
        setAgentCard(null);
      }
    },
  });

  const testMCPMutation = useMutation({
    mutationFn: ({ serverId, config }: { serverId: string; config: { url: string; headers: Record<string, string> } }) =>
      testMCPConnection(config),
    onSuccess: (data, variables) => {
      setMcpTestResults(prev => ({ ...prev, [variables.serverId]: data }));
    },
  });

  const resetMutation = useMutation({
    mutationFn: resetConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["config"] });
      setA2aTestResult(null);
      setMcpTestResults({});
      setAgentCard(null);
    },
  });

  const handleTestA2A = () => {
    setA2aTestResult(null);
    setAgentCard(null);
    testA2AMutation.mutate({ url: a2aUrl, headers: a2aHeaders });
  };

  const handleSaveA2A = async () => {
    await updateA2AMutation.mutateAsync({ url: a2aUrl, headers: a2aHeaders });
  };

  const handleAddServer = () => {
    addServerMutation.mutate({
      name: newServerName,
      url: newServerUrl,
      headers: newServerHeaders,
    });
  };

  const handleReset = () => {
    resetMutation.mutate();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span>Loading configuration...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex items-center gap-2 text-destructive">
          <AlertCircle className="w-5 h-5" />
          <span>Error loading configuration</span>
        </div>
      </div>
    );
  }

  const mcpServers = config?.mcp_servers || [];
  const activeCount = mcpServers.filter(s => s.is_active).length;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between">
          <button
            onClick={() => router.push("/")}
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Chat</span>
          </button>
          <div className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-primary" />
            <h1 className="font-semibold">Configuration</h1>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-3xl mx-auto px-4 py-8 space-y-8">
        {/* A2A Agent Connection */}
        <section className="bg-card rounded-xl border border-border p-6 space-y-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <Globe className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h2 className="font-semibold">A2A Agent Connection</h2>
              <p className="text-sm text-muted-foreground">
                Configure the A2A-compliant agent endpoint
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label htmlFor="a2a-url" className="text-sm font-medium text-muted-foreground">
                Agent URL
              </label>
              <input
                id="a2a-url"
                type="url"
                value={a2aUrl}
                onChange={(e) => setA2aUrl(e.target.value)}
                placeholder="http://localhost:8000"
                className="mt-1 w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>

            <HeadersEditor headers={a2aHeaders} onChange={setA2aHeaders} />

            <div className="flex items-center gap-4">
              <button
                onClick={handleTestA2A}
                disabled={testA2AMutation.isPending}
                className="flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors disabled:opacity-50"
              >
                {testA2AMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Server className="w-4 h-4" />
                )}
                Test Connection
              </button>

              <button
                onClick={handleSaveA2A}
                disabled={updateA2AMutation.isPending}
                className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                {updateA2AMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                Save
              </button>

              {a2aTestResult && (
                <div className={`flex items-center gap-2 text-sm ${a2aTestResult.success ? "text-green-500" : "text-destructive"}`}>
                  {a2aTestResult.success ? (
                    <>
                      <Check className="w-4 h-4" />
                      <span>
                        Connected: {a2aTestResult.agent_card?.name} v{a2aTestResult.agent_card?.version}
                      </span>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="w-4 h-4" />
                      <span>{a2aTestResult.error}</span>
                    </>
                  )}
                </div>
              )}
            </div>
            
            {/* Agent Card Display */}
            {agentCard && (
              <div className="animate-in fade-in duration-300">
                <AgentCardDisplay agentCard={agentCard} />
              </div>
            )}
          </div>
        </section>

        {/* MCP Servers Configuration */}
        <section className="bg-card rounded-xl border border-border p-6 space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
                <Server className="w-5 h-5 text-orange-500" />
              </div>
              <div>
                <h2 className="font-semibold">MCP Servers ({activeCount} active)</h2>
                <p className="text-sm text-muted-foreground">
                  Configure MCP servers for order data and tools
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            {mcpServers.map((server) => (
              <MCPServerCard
                key={server.id}
                server={server}
                onTest={() => testMCPMutation.mutate({ serverId: server.id, config: { url: server.url, headers: server.headers } })}
                onUpdate={(updates) => updateServerMutation.mutate({ serverId: server.id, updates })}
                onDelete={() => deleteServerMutation.mutate(server.id)}
                testResult={mcpTestResults[server.id] || null}
                isTestPending={testMCPMutation.isPending}
              />
            ))}

            {showAddServer ? (
              <div className="bg-muted/50 rounded-xl border border-border p-4 space-y-4">
                <h3 className="font-semibold">Add New MCP Server</h3>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Server Name</label>
                  <input
                    type="text"
                    value={newServerName}
                    onChange={(e) => setNewServerName(e.target.value)}
                    placeholder="inventory"
                    className="mt-1 w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-muted-foreground">Server URL</label>
                  <input
                    type="url"
                    value={newServerUrl}
                    onChange={(e) => setNewServerUrl(e.target.value)}
                    placeholder="https://..."
                    className="mt-1 w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>
                <HeadersEditor headers={newServerHeaders} onChange={setNewServerHeaders} />
                <div className="flex items-center gap-2 justify-end">
                  <button
                    onClick={() => setShowAddServer(false)}
                    className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleAddServer}
                    disabled={!newServerName || !newServerUrl || addServerMutation.isPending}
                    className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
                  >
                    {addServerMutation.isPending ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Plus className="w-4 h-4" />
                    )}
                    Add Server
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setShowAddServer(true)}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 border-2 border-dashed border-border rounded-xl text-muted-foreground hover:text-foreground hover:border-primary/50 transition-colors"
              >
                <Plus className="w-5 h-5" />
                <span>Add MCP Server</span>
              </button>
            )}
          </div>
        </section>

        {/* Action Buttons */}
        <div className="flex items-center justify-between">
          <button
            onClick={handleReset}
            disabled={resetMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
          >
            {resetMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <RotateCcw className="w-4 h-4" />
            )}
            Reset to Defaults
          </button>
        </div>
      </main>
    </div>
  );
}
