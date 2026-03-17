import type {
  Document,
  DocumentListResponse,
  HealthResponse,
  SSEEvent,
  UploadResponse,
} from "@/types/chat";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, options);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export async function getDocuments(): Promise<Document[]> {
  const data = await request<DocumentListResponse>("/api/documents");
  return data.documents;
}

export async function uploadDocuments(
  files: File[]
): Promise<UploadResponse[]> {
  const formData = new FormData();
  files.forEach((f) => formData.append("files", f));
  const res = await fetch(`${BASE_URL}/api/documents/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Upload error ${res.status}: ${text}`);
  }
  return res.json();
}

export async function deleteDocument(id: string): Promise<void> {
  await request(`/api/documents/${id}`, { method: "DELETE" });
}

export async function clearAllDocuments(): Promise<void> {
  await request("/api/documents", { method: "DELETE" });
}

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/api/health");
}

export async function streamChat(
  sessionId: string,
  message: string,
  onEvent: (event: SSEEvent) => void,
  signal: AbortSignal
): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Session-ID": sessionId,
    },
    body: JSON.stringify({ session_id: sessionId, message }),
    signal,
  });

  if (!res.ok) {
    throw new Error(`Chat error ${res.status}`);
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const event: SSEEvent = JSON.parse(line.slice(6));
          onEvent(event);
        } catch {
          // skip malformed lines
        }
      }
    }
  }
}
