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
} from "lucide-react";
import {
  fetchConfig,
  updateA2AConfig,
  updateMCPConfig,
  testA2AConnection,
  testMCPConnection,
  resetConfig,
  type AppConfig,
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

export default function SettingsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  // Form state
  const [a2aUrl, setA2aUrl] = useState("http://localhost:8000");
  const [a2aHeaders, setA2aHeaders] = useState<Record<string, string>>({});
  const [mcpName, setMcpName] = useState("orders");
  const [mcpUrl, setMcpUrl] = useState("");
  const [mcpHeaders, setMcpHeaders] = useState<Record<string, string>>({});

  // Test results
  const [a2aTestResult, setA2aTestResult] = useState<A2ATestResponse | null>(null);
  const [mcpTestResult, setMcpTestResult] = useState<MCPTestResponse | null>(null);
  
  // Agent card state
  const [agentCard, setAgentCard] = useState<AgentCard | null>(null);

  // Save status
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");

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
      setMcpName(config.mcp.name);
      setMcpUrl(config.mcp.url);
      setMcpHeaders(config.mcp.headers);
    }
  }, [config]);

  // Mutations
  const updateA2AMutation = useMutation({
    mutationFn: updateA2AConfig,
  });

  const updateMCPMutation = useMutation({
    mutationFn: updateMCPConfig,
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
    mutationFn: testMCPConnection,
    onSuccess: (data) => setMcpTestResult(data),
  });

  const resetMutation = useMutation({
    mutationFn: resetConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["config"] });
      setA2aTestResult(null);
      setMcpTestResult(null);
      setAgentCard(null);
    },
  });

  const handleTestA2A = () => {
    setA2aTestResult(null);
    setAgentCard(null);
    testA2AMutation.mutate({ url: a2aUrl, headers: a2aHeaders });
  };

  const handleTestMCP = () => {
    setMcpTestResult(null);
    testMCPMutation.mutate({ url: mcpUrl, headers: mcpHeaders });
  };

  const handleSave = async () => {
    setSaveStatus("saving");
    try {
      await updateA2AMutation.mutateAsync({ url: a2aUrl, headers: a2aHeaders });
      await updateMCPMutation.mutateAsync({ name: mcpName, url: mcpUrl, headers: mcpHeaders });
      setSaveStatus("saved");
      queryClient.invalidateQueries({ queryKey: ["config"] });
      setTimeout(() => setSaveStatus("idle"), 2000);
    } catch {
      setSaveStatus("error");
      setTimeout(() => setSaveStatus("idle"), 3000);
    }
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

        {/* MCP Server Configuration */}
        <section className="bg-card rounded-xl border border-border p-6 space-y-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
              <Server className="w-5 h-5 text-orange-500" />
            </div>
            <div>
              <h2 className="font-semibold">MCP Server Configuration</h2>
              <p className="text-sm text-muted-foreground">
                Configure the MCP server for order data
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label htmlFor="mcp-name" className="text-sm font-medium text-muted-foreground">
                Server Name
              </label>
              <input
                id="mcp-name"
                type="text"
                value={mcpName}
                onChange={(e) => setMcpName(e.target.value)}
                placeholder="orders"
                className="mt-1 w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>

            <div>
              <label htmlFor="mcp-url" className="text-sm font-medium text-muted-foreground">
                Server URL
              </label>
              <input
                id="mcp-url"
                type="url"
                value={mcpUrl}
                onChange={(e) => setMcpUrl(e.target.value)}
                placeholder="https://..."
                className="mt-1 w-full px-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>

            <HeadersEditor headers={mcpHeaders} onChange={setMcpHeaders} />

            <div className="flex items-center gap-4">
              <button
                onClick={handleTestMCP}
                disabled={testMCPMutation.isPending}
                className="flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors disabled:opacity-50"
              >
                {testMCPMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Server className="w-4 h-4" />
                )}
                Test Connection
              </button>

              {mcpTestResult && (
                <div className={`flex items-center gap-2 text-sm ${mcpTestResult.success ? "text-green-500" : "text-destructive"}`}>
                  {mcpTestResult.success ? (
                    <>
                      <Check className="w-4 h-4" />
                      <span>{mcpTestResult.tools?.length || 0} tools available</span>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="w-4 h-4" />
                      <span>{mcpTestResult.error}</span>
                    </>
                  )}
                </div>
              )}
            </div>
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

          <button
            onClick={handleSave}
            disabled={saveStatus === "saving"}
            className={`flex items-center gap-2 px-6 py-2 rounded-lg font-medium transition-colors ${
              saveStatus === "saved"
                ? "bg-green-500 text-white"
                : saveStatus === "error"
                ? "bg-destructive text-destructive-foreground"
                : "bg-primary text-primary-foreground hover:bg-primary/90"
            } disabled:opacity-50`}
          >
            {saveStatus === "saving" ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Saving...
              </>
            ) : saveStatus === "saved" ? (
              <>
                <Check className="w-4 h-4" />
                Saved!
              </>
            ) : saveStatus === "error" ? (
              <>
                <AlertCircle className="w-4 h-4" />
                Error
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                Save Configuration
              </>
            )}
          </button>
        </div>
      </main>
    </div>
  );
}
