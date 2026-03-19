"use client";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { Citation } from "@/types/chat";

interface CitationBadgeProps {
  citation: Citation;
}

export function CitationBadge({ citation }: CitationBadgeProps) {
  const location = citation.page_number
    ? `p. ${citation.page_number}`
    : citation.section_heading
    ? `§ ${citation.section_heading}`
    : "No location info";

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button className="inline-flex items-center justify-center h-5 min-w-5 px-1 text-xs font-bold bg-blue-100 text-blue-800 rounded hover:bg-blue-200 transition-colors align-middle mx-0.5 cursor-pointer">
          [{citation.id}]
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-80 p-0" align="start">
        <div className="p-3 border-b">
          <p className="font-semibold text-sm truncate" title={citation.source_filename}>
            {citation.source_filename}
          </p>
          <p className="text-xs text-muted-foreground mt-0.5">{location}</p>
        </div>
        {citation.excerpt && (
          <blockquote className="p-3 text-sm text-muted-foreground italic border-l-2 border-muted m-3 pl-3">
            "{citation.excerpt}"
          </blockquote>
        )}
      </PopoverContent>
    </Popover>
  );
}
