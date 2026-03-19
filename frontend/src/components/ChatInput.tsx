"use client";

import { useCallback, useRef } from "react";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { StopButton } from "@/components/StopButton";

interface ChatInputProps {
  onSend: (text: string) => void;
  onStop: () => void;
  isStreaming: boolean;
  disabled: boolean;
  disabledReason?: string;
}

export function ChatInput({ onSend, onStop, isStreaming, disabled, disabledReason }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = useCallback(() => {
    const value = textareaRef.current?.value.trim();
    if (!value || isStreaming || disabled) return;
    onSend(value);
    if (textareaRef.current) textareaRef.current.value = "";
    adjustHeight();
  }, [onSend, isStreaming, disabled]);

  const adjustHeight = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 144) + "px"; // max 6 rows ≈ 144px
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex items-end gap-2 p-4 border-t">
      <div className="flex-1 relative">
        <textarea
          ref={textareaRef}
          rows={1}
          placeholder={
            disabled
              ? disabledReason ?? "Chat unavailable"
              : "Ask about your books..."
          }
          disabled={disabled || isStreaming}
          onKeyDown={handleKeyDown}
          onInput={adjustHeight}
          className="w-full resize-none rounded-lg border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50 disabled:cursor-not-allowed overflow-hidden"
          style={{ minHeight: "40px", maxHeight: "144px" }}
        />
      </div>
      {isStreaming ? (
        <StopButton onClick={onStop} />
      ) : (
        <Button
          onClick={handleSend}
          disabled={disabled}
          size="icon"
          className="shrink-0"
        >
          <Send className="h-4 w-4" />
          <span className="sr-only">Send</span>
        </Button>
      )}
    </div>
  );
}
