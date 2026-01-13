"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface ToolAccordionProps {
  toolName: string;
  toolInput?: Record<string, unknown>;
  toolResult?: string;
  isLoading?: boolean;
}

export function ToolAccordion({
  toolName,
  toolInput,
  toolResult,
  isLoading = false,
}: ToolAccordionProps) {
  const [isOpen, setIsOpen] = useState(false);

  // Try to parse and format the result
  const formatResult = (result: string | undefined) => {
    if (!result) return null;

    try {
      const parsed = JSON.parse(result);

      // If it's an array of objects, try to render as table
      if (Array.isArray(parsed) && parsed.length > 0 && typeof parsed[0] === "object") {
        return renderTable(parsed);
      }

      // Otherwise render as formatted JSON
      return (
        <pre className="text-xs bg-muted/50 p-3 rounded-lg overflow-x-auto">
          <code>{JSON.stringify(parsed, null, 2)}</code>
        </pre>
      );
    } catch {
      // If not JSON, render as plain text
      return <p className="text-sm text-muted-foreground whitespace-pre-wrap">{result}</p>;
    }
  };

  const renderTable = (data: Record<string, unknown>[]) => {
    if (data.length === 0) return null;

    const columns = Object.keys(data[0]);

    return (
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr>
              {columns.map((col) => (
                <th
                  key={col}
                  className="text-left font-medium text-muted-foreground border-b border-border py-2 px-3 capitalize"
                >
                  {col.replace(/_/g, " ")}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.slice(0, 10).map((row, idx) => (
              <tr key={idx}>
                {columns.map((col) => (
                  <td key={col} className="border-b border-border/50 py-2 px-3">
                    {formatCellValue(row[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {data.length > 10 && (
          <p className="text-xs text-muted-foreground mt-2 px-3">
            Showing 10 of {data.length} rows
          </p>
        )}
      </div>
    );
  };

  const formatCellValue = (value: unknown): string => {
    if (value === null || value === undefined) return "-";
    if (typeof value === "number") {
      // Format currency-like values
      if (value >= 100) {
        return new Intl.NumberFormat("en-US", {
          style: "currency",
          currency: "EUR",
        }).format(value);
      }
      return value.toString();
    }
    if (typeof value === "object") {
      return JSON.stringify(value);
    }
    return String(value);
  };

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-muted/50 transition-colors"
      >
        {/* MCP badge */}
        <span className="flex items-center justify-center w-6 h-6 rounded bg-primary/10 text-primary text-xs font-semibold">
          M
        </span>

        {/* Tool name */}
        <span className="flex-1 text-left text-sm font-medium">
          {toolName}
        </span>

        {/* Loading indicator or chevron */}
        {isLoading ? (
          <div className="w-4 h-4 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
        ) : (
          <ChevronDown
            className={cn(
              "w-4 h-4 text-muted-foreground transition-transform duration-200",
              isOpen && "rotate-180"
            )}
          />
        )}
      </button>

      {/* Content */}
      {isOpen && (
        <div className="px-4 pb-4 border-t border-border/50">
          {/* Tool input if provided */}
          {toolInput && Object.keys(toolInput).length > 0 && (
            <div className="mt-3">
              <p className="text-xs text-muted-foreground mb-1">Input:</p>
              <pre className="text-xs bg-muted/50 p-2 rounded overflow-x-auto">
                <code>{JSON.stringify(toolInput, null, 2)}</code>
              </pre>
            </div>
          )}

          {/* Tool result */}
          <div className="mt-3">
            {toolResult ? (
              formatResult(toolResult)
            ) : isLoading ? (
              <p className="text-sm text-muted-foreground">Fetching data...</p>
            ) : (
              <p className="text-sm text-muted-foreground">No result</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
