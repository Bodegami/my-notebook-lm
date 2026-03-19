"use client";

import { useCallback, useRef, useState } from "react";
import { v4 as uuidv4 } from "uuid";
import * as api from "@/lib/api";
import type { ChatMessage, Citation, SSEEvent } from "@/types/chat";

export function useChat(sessionId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [agentStatus, setAgentStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!sessionId || isStreaming) return;

      const userMsg: ChatMessage = {
        id: uuidv4(),
        role: "user",
        content: text,
        citations: [],
        timestamp: new Date(),
      };

      const assistantId = uuidv4();
      const assistantMsg: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        citations: [],
        timestamp: new Date(),
        isStreaming: true,
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsStreaming(true);
      setAgentStatus(null);
      setError(null);

      const controller = new AbortController();
      abortRef.current = controller;

      const updateAssistant = (updater: (msg: ChatMessage) => ChatMessage) => {
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantId ? updater(m) : m))
        );
      };

      try {
        await api.streamChat(
          sessionId,
          text,
          (event: SSEEvent) => {
            if (event.type === "status") {
              setAgentStatus(event.text ?? null);
            } else if (event.type === "token") {
              updateAssistant((m) => ({
                ...m,
                content: m.content + (event.text ?? ""),
              }));
            } else if (event.type === "citation") {
              const citation: Citation = {
                id: event.id ?? 0,
                source_filename: event.source_filename ?? "",
                page_number: event.page_number ?? null,
                section_heading: event.section_heading ?? null,
                excerpt: event.excerpt ?? "",
              };
              updateAssistant((m) => ({
                ...m,
                citations: [...m.citations, citation],
              }));
            } else if (event.type === "done") {
              updateAssistant((m) => ({ ...m, isStreaming: false }));
              setIsStreaming(false);
              setAgentStatus(null);
            } else if (event.type === "error") {
              setError(event.text ?? "An error occurred.");
              updateAssistant((m) => ({ ...m, isStreaming: false }));
              setIsStreaming(false);
              setAgentStatus(null);
            }
          },
          controller.signal
        );
      } catch (e: unknown) {
        if ((e as Error)?.name !== "AbortError") {
          setError("Connection error. Please try again.");
        }
        updateAssistant((m) => ({ ...m, isStreaming: false }));
        setIsStreaming(false);
        setAgentStatus(null);
      }
    },
    [sessionId, isStreaming]
  );

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
    setIsStreaming(false);
    setAgentStatus(null);
    setMessages((prev) =>
      prev.map((m) =>
        m.isStreaming ? { ...m, isStreaming: false } : m
      )
    );
  }, []);

  const clearHistory = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    isStreaming,
    agentStatus,
    error,
    sendMessage,
    stopStreaming,
    clearHistory,
  };
}
