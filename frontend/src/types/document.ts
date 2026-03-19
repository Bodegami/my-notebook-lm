export type DocumentStatus =
  | "pending"
  | "extracting"
  | "chunking"
  | "embedding"
  | "indexed"
  | "error";

export interface Document {
  id: string;
  filename: string;
  file_format: string;
  upload_time: string;
  status: DocumentStatus;
  error_message: string | null;
  page_count: number | null;
  chunk_count: number | null;
}

export interface UploadResponse {
  document_id: string;
  filename: string;
  status: string;
}

export interface DocumentListResponse {
  documents: Document[];
}
