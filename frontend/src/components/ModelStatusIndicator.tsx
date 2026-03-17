"use client";

import { useEffect, useState } from "react";
import { getHealth } from "@/lib/api";
import type { HealthResponse } from "@/types/chat";

type ModelStatus = "loading" | "ready" | "unavailable";

export function ModelStatusIndicator() {
  const [status, setStatus] = useState<ModelStatus>("loading");
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    const check = async () => {
      try {
        const health: HealthResponse = await getHealth();
        if (health.ollama === "connected" && health.models_loaded.length > 0) {
          setStatus("ready");
          setShowBanner(false);
        } else if (health.ollama === "unreachable") {
          setStatus("unavailable");
          setShowBanner(true);
        } else {
          setStatus("loading");
        }
      } catch {
        setStatus("unavailable");
        setShowBanner(true);
      }
    };

    check();
    const interval = setInterval(check, 5000);
    return () => clearInterval(interval);
  }, []);

  const dot =
    status === "ready"
      ? "bg-green-500"
      : status === "loading"
      ? "bg-yellow-400 animate-pulse"
      : "bg-red-500";

  const label =
    status === "ready"
      ? "Models Ready"
      : status === "loading"
      ? "Models Loading"
      : "Unavailable";

  return (
    <div className="flex flex-col items-end gap-1">
      <div className="flex items-center gap-2 text-sm">
        <span className={`h-2 w-2 rounded-full ${dot}`} />
        <span className="text-muted-foreground">{label}</span>
      </div>
      {showBanner && (
        <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded px-2 py-1 max-w-xs">
          Ollama not responding. Ensure Docker containers are running.{" "}
          <button
            onClick={() => setShowBanner(false)}
            className="underline ml-1"
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
}
