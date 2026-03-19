"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import type { Citation } from "@/types/chat";

interface SourcesPanelProps {
  citations: Citation[];
}

export function SourcesPanel({ citations }: SourcesPanelProps) {
  const [open, setOpen] = useState(false);

  if (!citations.length) return null;

  return (
    <div className="mt-2 border rounded-md text-xs">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-3 py-2 text-muted-foreground hover:text-foreground transition-colors"
      >
        <span className="font-medium">Sources Consulted ({citations.length})</span>
        {open ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
      </button>
      {open && (
        <div className="border-t px-3 py-2 space-y-2">
          {citations.map((c, i) => {
            const location = c.page_number
              ? `p. ${c.page_number}`
              : c.section_heading
              ? `§ ${c.section_heading}`
              : "";
            const snippet = c.excerpt?.slice(0, 120) + (c.excerpt?.length > 120 ? "…" : "");
            return (
              <div key={i} className="text-muted-foreground">
                <span className="font-medium text-foreground">
                  [{c.id}] {c.source_filename}
                  {location && <span className="text-muted-foreground"> — {location}</span>}
                </span>
                {snippet && <p className="italic mt-0.5">"{snippet}"</p>}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
