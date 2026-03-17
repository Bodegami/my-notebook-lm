"use client";

import { useState } from "react";
import { Trash2, Plus, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog";
import { UploadZone } from "@/components/UploadZone";
import type { Document } from "@/types/document";

const FORMAT_ICONS: Record<string, string> = {
  pdf: "📄", epub: "📘", docx: "📝", doc: "📝", md: "📋", txt: "📃",
};

const STATUS_PROCESSING = new Set(["pending", "extracting", "chunking", "embedding"]);

interface DocumentSidebarProps {
  documents: Document[];
  isUploading: boolean;
  onUpload: (files: File[]) => Promise<void>;
  onDelete: (id: string) => void;
  onClearAll: () => void;
}

export function DocumentSidebar({
  documents, isUploading, onUpload, onDelete, onClearAll,
}: DocumentSidebarProps) {
  const [uploadOpen, setUploadOpen] = useState(false);

  const handleUpload = async (files: File[]) => {
    await onUpload(files);
    setUploadOpen(false);
  };

  return (
    <div className="h-full flex flex-col border-r bg-muted/30">
      <div className="p-4 border-b">
        <h2 className="font-semibold text-sm uppercase tracking-wide text-muted-foreground">
          Your Books
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {documents.length === 0 && (
          <p className="text-xs text-muted-foreground text-center py-4">
            No books uploaded yet
          </p>
        )}
        {documents.map((doc) => (
          <div key={doc.id} className="flex items-start gap-2 p-2 rounded-md hover:bg-muted group">
            <span className="text-lg">{FORMAT_ICONS[doc.file_format] ?? "📄"}</span>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate" title={doc.filename}>
                {doc.filename.length > 24
                  ? doc.filename.slice(0, 21) + "…"
                  : doc.filename}
              </p>
              <div className="flex items-center gap-1 mt-0.5">
                {STATUS_PROCESSING.has(doc.status) ? (
                  <Badge variant="warning" className="gap-1 text-xs py-0">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    {doc.status}
                  </Badge>
                ) : doc.status === "indexed" ? (
                  <Badge variant="success" className="text-xs py-0">indexed</Badge>
                ) : (
                  <Badge variant="destructive" className="text-xs py-0">error</Badge>
                )}
              </div>
              {doc.status === "error" && doc.error_message && (
                <p className="text-xs text-red-600 mt-1 truncate" title={doc.error_message}>
                  {doc.error_message}
                </p>
              )}
            </div>
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <button className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-opacity">
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Delete document?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This will permanently remove "{doc.filename}" and all its indexed vectors.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <div className="flex gap-3 justify-end">
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction onClick={() => onDelete(doc.id)} className="bg-destructive hover:bg-destructive/90">
                    Delete
                  </AlertDialogAction>
                </div>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        ))}
      </div>

      <div className="p-3 border-t space-y-2">
        <Dialog open={uploadOpen} onOpenChange={setUploadOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" size="sm" className="w-full gap-2">
              <Plus className="h-4 w-4" /> Upload Books
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Upload Books</DialogTitle>
            </DialogHeader>
            <UploadZone onUpload={handleUpload} isUploading={isUploading} />
          </DialogContent>
        </Dialog>

        {documents.length > 0 && (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="ghost" size="sm" className="w-full gap-2 text-destructive hover:text-destructive">
                <Trash2 className="h-4 w-4" /> Clear All
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Clear knowledge base?</AlertDialogTitle>
                <AlertDialogDescription>
                  This will delete all {documents.length} document(s) and their vectors. This action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <div className="flex gap-3 justify-end">
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={onClearAll} className="bg-destructive hover:bg-destructive/90">
                  Clear All
                </AlertDialogAction>
              </div>
            </AlertDialogContent>
          </AlertDialog>
        )}
      </div>
    </div>
  );
}
