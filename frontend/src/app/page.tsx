"use client";

import { ModelStatusIndicator } from "@/components/ModelStatusIndicator";
import { DocumentSidebar } from "@/components/DocumentSidebar";
import { ChatThread } from "@/components/ChatThread";
import { ChatInput } from "@/components/ChatInput";
import { useSession } from "@/hooks/useSession";
import { useDocuments } from "@/hooks/useDocuments";
import { useChat } from "@/hooks/useChat";
import { useEffect, useState } from "react";
import { getHealth } from "@/lib/api";
import type { HealthResponse } from "@/types/chat";

export default function Home() {
  const { sessionId } = useSession();
  const { documents, isUploading, error: docError, uploadFiles, deleteDocument, clearAll } = useDocuments();
  const { messages, isStreaming, agentStatus, error: chatError, sendMessage, stopStreaming } = useChat(sessionId);

  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    const check = async () => {
      try {
        const h = await getHealth();
        setHealth(h);
      } catch {
        setHealth(null);
      }
    };
    check();
    const interval = setInterval(check, 5000);
    return () => clearInterval(interval);
  }, []);

  const hasIndexedDocs = documents.some((d) => d.status === "indexed");
  const modelsReady =
    health?.ollama === "connected" && (health?.models_loaded?.length ?? 0) > 0;

  const chatDisabled = !hasIndexedDocs || !modelsReady;
  const chatDisabledReason = !modelsReady
    ? "Models are loading, please wait"
    : "Upload books to start chatting";

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 border-b bg-background shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-xl">📚</span>
          <h1 className="font-semibold text-lg">Local Book Library</h1>
        </div>
        <ModelStatusIndicator />
      </header>

      {/* Error banners */}
      {(docError || chatError) && (
        <div className="bg-red-50 border-b border-red-200 px-6 py-2 text-sm text-red-700">
          {docError || chatError}
        </div>
      )}

      {/* Main content: sidebar + chat */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left sidebar — fixed 280px */}
        <aside className="w-[280px] shrink-0">
          <DocumentSidebar
            documents={documents}
            isUploading={isUploading}
            onUpload={uploadFiles}
            onDelete={deleteDocument}
            onClearAll={clearAll}
          />
        </aside>

        {/* Right panel — chat */}
        <main className="flex-1 flex flex-col overflow-hidden">
          <ChatThread
            messages={messages}
            isStreaming={isStreaming}
            agentStatus={agentStatus}
            hasDocuments={hasIndexedDocs}
          />
          <ChatInput
            onSend={sendMessage}
            onStop={stopStreaming}
            isStreaming={isStreaming}
            disabled={chatDisabled}
            disabledReason={chatDisabledReason}
          />
        </main>
      </div>
    </div>
  );
}
