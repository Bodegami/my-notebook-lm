"use client";

import { useEffect, useRef } from "react";
import { MessageBubble } from "@/components/MessageBubble";
import { AgentStatusBar } from "@/components/AgentStatusBar";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { ChatMessage } from "@/types/chat";

interface ChatThreadProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  agentStatus: string | null;
  hasDocuments: boolean;
}

export function ChatThread({ messages, isStreaming, agentStatus, hasDocuments }: ChatThreadProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, agentStatus]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-center p-8">
        <div>
          <p className="text-4xl mb-4">📚</p>
          {hasDocuments ? (
            <>
              <p className="text-lg font-medium text-foreground">Ask anything about your books</p>
              <p className="text-sm text-muted-foreground mt-1">Your knowledge base is ready</p>
            </>
          ) : (
            <>
              <p className="text-lg font-medium text-foreground">Upload books to start chatting</p>
              <p className="text-sm text-muted-foreground mt-1">Add PDF, EPUB, DOCX, MD, or TXT files</p>
            </>
          )}
        </div>
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1">
      <div className="p-4 space-y-1">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {isStreaming && <AgentStatusBar status={agentStatus} />}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
