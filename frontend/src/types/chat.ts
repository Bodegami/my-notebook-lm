export interface Citation {
  id: number;
  source_filename: string;
  page_number: number | null;
  section_heading: string | null;
  excerpt: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  timestamp: Date;
  isStreaming?: boolean;
}

export type SSEEventType = "status" | "token" | "citation" | "done" | "error";

export interface SSEEvent {
  type: SSEEventType;
  text?: string;
  citation?: Citation;
  sources?: Citation[];
  id?: number;
  source_filename?: string;
  page_number?: number | null;
  section_heading?: string | null;
  excerpt?: string;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  qdrant: "connected" | "unreachable";
  ollama: "connected" | "unreachable";
  models_loaded: string[];
}
