"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

interface AgentStatusBarProps {
  status: string | null;
}

export function AgentStatusBar({ status }: AgentStatusBarProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (status) {
      setVisible(true);
    } else {
      const t = setTimeout(() => setVisible(false), 300);
      return () => clearTimeout(t);
    }
  }, [status]);

  if (!visible) return null;

  return (
    <div className="flex items-center gap-2 px-4 py-2 text-sm text-muted-foreground transition-opacity duration-300">
      <Loader2 className="h-4 w-4 animate-spin" />
      <span>{status ?? ""}</span>
    </div>
  );
}
