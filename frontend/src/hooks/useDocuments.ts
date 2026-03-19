"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import * as api from "@/lib/api";
import type { Document } from "@/types/document";

const TERMINAL_STATUSES = new Set(["indexed", "error"]);
const POLL_INTERVAL_MS = 2000;

export function useDocuments() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const loadDocuments = useCallback(async () => {
    try {
      const docs = await api.getDocuments();
      setDocuments(docs);
      return docs;
    } catch (e) {
      setError("Failed to load documents.");
      return [];
    }
  }, []);

  const startPolling = useCallback(() => {
    stopPolling();
    pollRef.current = setInterval(async () => {
      const docs = await loadDocuments();
      const allDone = docs.every((d) => TERMINAL_STATUSES.has(d.status));
      if (allDone) stopPolling();
    }, POLL_INTERVAL_MS);
  }, [loadDocuments, stopPolling]);

  useEffect(() => {
    loadDocuments().then((docs) => {
      if (docs.some((d) => !TERMINAL_STATUSES.has(d.status))) {
        startPolling();
      }
    });
    return stopPolling;
  }, [loadDocuments, startPolling, stopPolling]);

  const uploadFiles = useCallback(
    async (files: File[]) => {
      setIsUploading(true);
      setError(null);
      try {
        await api.uploadDocuments(files);
        await loadDocuments();
        startPolling();
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "Upload failed.";
        setError(msg);
        throw e;
      } finally {
        setIsUploading(false);
      }
    },
    [loadDocuments, startPolling]
  );

  const deleteDocument = useCallback(
    async (id: string) => {
      try {
        await api.deleteDocument(id);
        setDocuments((prev) => prev.filter((d) => d.id !== id));
      } catch {
        setError("Failed to delete document.");
      }
    },
    []
  );

  const clearAll = useCallback(async () => {
    try {
      await api.clearAllDocuments();
      setDocuments([]);
      stopPolling();
    } catch {
      setError("Failed to clear knowledge base.");
    }
  }, [stopPolling]);

  return {
    documents,
    isUploading,
    error,
    uploadFiles,
    deleteDocument,
    clearAll,
    loadDocuments,
  };
}
