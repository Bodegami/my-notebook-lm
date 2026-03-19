"use client";

import { useCallback, useState } from "react";
import { Button } from "@/components/ui/button";
import { Upload, X } from "lucide-react";

const ALLOWED_EXTS = [".pdf", ".epub", ".docx", ".doc", ".md", ".txt"];
const MAX_MB = 200;

interface UploadZoneProps {
  onUpload: (files: File[]) => Promise<void>;
  isUploading: boolean;
}

export function UploadZone({ onUpload, isUploading }: UploadZoneProps) {
  const [dragging, setDragging] = useState(false);
  const [selected, setSelected] = useState<File[]>([]);
  const [validationError, setValidationError] = useState<string | null>(null);

  const validate = (files: File[]): File[] => {
    const valid: File[] = [];
    const errors: string[] = [];
    for (const f of files) {
      const ext = "." + f.name.split(".").pop()?.toLowerCase();
      if (!ALLOWED_EXTS.includes(ext)) {
        errors.push(`${f.name}: unsupported format`);
      } else if (f.size > MAX_MB * 1024 * 1024) {
        errors.push(`${f.name}: exceeds ${MAX_MB}MB`);
      } else {
        valid.push(f);
      }
    }
    if (errors.length) setValidationError(errors.join("; "));
    return valid;
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const files = Array.from(e.dataTransfer.files);
    const valid = validate(files);
    setSelected((prev) => [...prev, ...valid]);
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    const valid = validate(files);
    setSelected((prev) => [...prev, ...valid]);
    e.target.value = "";
  };

  const removeFile = (idx: number) => {
    setSelected((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleUpload = async () => {
    if (!selected.length) return;
    await onUpload(selected);
    setSelected([]);
    setValidationError(null);
  };

  return (
    <div className="space-y-3">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors cursor-pointer ${
          dragging ? "border-primary bg-primary/5" : "border-muted-foreground/30"
        }`}
        onClick={() => document.getElementById("file-input")?.click()}
      >
        <Upload className="mx-auto h-8 w-8 text-muted-foreground mb-2" />
        <p className="text-sm text-muted-foreground">
          Drag & drop books here or <span className="underline">click to browse</span>
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          PDF, EPUB, DOCX, DOC, MD, TXT — max {MAX_MB}MB each
        </p>
        <input
          id="file-input"
          type="file"
          multiple
          accept={ALLOWED_EXTS.join(",")}
          className="hidden"
          onChange={handleFileInput}
        />
      </div>

      {validationError && (
        <p className="text-xs text-red-600">{validationError}</p>
      )}

      {selected.length > 0 && (
        <div className="space-y-1">
          {selected.map((f, i) => (
            <div key={i} className="flex items-center justify-between text-sm bg-muted rounded px-3 py-1.5">
              <span className="truncate max-w-[200px]">{f.name}</span>
              <button onClick={() => removeFile(i)} className="ml-2 text-muted-foreground hover:text-foreground">
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
          <Button
            onClick={handleUpload}
            disabled={isUploading}
            className="w-full mt-2"
            size="sm"
          >
            {isUploading ? "Uploading..." : `Upload ${selected.length} file${selected.length > 1 ? "s" : ""}`}
          </Button>
        </div>
      )}
    </div>
  );
}
