"use client";

import { forwardRef, useState, useRef, useImperativeHandle } from "react";
import { Send, Loader2, ChevronDown } from "lucide-react";
import { ConnectorsPopover } from "./ConnectorsPopover";
import { cn } from "@/lib/utils";

interface InputToolbarProps {
  onSubmit: (message: string) => void;
  isLoading: boolean;
  placeholder?: string;
}

export interface InputToolbarRef {
  focus: () => void;
}

export const InputToolbar = forwardRef<InputToolbarRef, InputToolbarProps>(
  function InputToolbar({ onSubmit, isLoading, placeholder = "How can I help you today?" }, ref) {
    const [input, setInput] = useState("");
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    useImperativeHandle(ref, () => ({
      focus: () => textareaRef.current?.focus(),
    }));

    const handleSubmit = () => {
      if (!input.trim() || isLoading) return;
      onSubmit(input.trim());
      setInput("");
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    };

    // Auto-resize textarea
    const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setInput(e.target.value);
      const textarea = e.target;
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    };

    return (
      <div className="w-full max-w-3xl mx-auto">
        {/* Input container with pill shape */}
        <div className="relative bg-card rounded-2xl border border-border shadow-sm">
          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            rows={1}
            disabled={isLoading}
            className={cn(
              "w-full resize-none bg-transparent px-4 py-4 pr-12",
              "text-sm placeholder:text-muted-foreground/60",
              "focus:outline-none disabled:opacity-50",
              "min-h-[56px] max-h-[200px]"
            )}
          />

          {/* Bottom toolbar */}
          <div className="flex items-center justify-between px-3 pb-3">
            {/* Left side - Actions */}
            <div className="flex items-center gap-1">
              {/* Connectors */}
              <ConnectorsPopover />

              {/* Model badge */}
              <div className="flex items-center gap-1.5 px-2 py-1 text-xs text-muted-foreground">
                <span>Claude Sonnet</span>
                <ChevronDown className="w-3 h-3" />
              </div>
            </div>

            {/* Right side - Send button */}
            <button
              onClick={handleSubmit}
              disabled={!input.trim() || isLoading}
              className={cn(
                "w-9 h-9 rounded-full flex items-center justify-center transition-all",
                "disabled:opacity-40 disabled:cursor-not-allowed",
                input.trim() && !isLoading
                  ? "bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm"
                  : "bg-muted text-muted-foreground"
              )}
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>

        {/* Helper text */}
        <p className="text-[10px] text-muted-foreground/50 text-center mt-2">
          Press Enter to send · Shift+Enter for new line
        </p>
      </div>
    );
  }
);
