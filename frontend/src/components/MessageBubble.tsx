"use client";

import ReactMarkdown from "react-markdown";
import { CitationBadge } from "@/components/CitationBadge";
import { SourcesPanel } from "@/components/SourcesPanel";
import type { ChatMessage } from "@/types/chat";

interface MessageBubbleProps {
  message: ChatMessage;
}

function renderContentWithCitations(content: string, message: ChatMessage) {
  // Replace [n] citation markers with CitationBadge components
  const parts = content.split(/(\[\d+\])/g);
  return parts.map((part, i) => {
    const match = part.match(/^\[(\d+)\]$/);
    if (match) {
      const id = parseInt(match[1]);
      const citation = message.citations.find((c) => c.id === id);
      if (citation) {
        return <CitationBadge key={i} citation={citation} />;
      }
    }
    return (
      <ReactMarkdown key={i} components={{ p: ({ children }) => <span>{children}</span> }}>
        {part}
      </ReactMarkdown>
    );
  });
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-3`}>
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-foreground"
        }`}
      >
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="text-sm prose prose-sm max-w-none">
            {message.citations.length > 0
              ? renderContentWithCitations(message.content, message)
              : <ReactMarkdown>{message.content}</ReactMarkdown>}
            {message.isStreaming && (
              <span className="inline-block w-1.5 h-4 bg-current ml-0.5 animate-blink align-middle" />
            )}
          </div>
        )}
        {!isUser && message.citations.length > 0 && (
          <SourcesPanel citations={message.citations} />
        )}
      </div>
    </div>
  );
}
