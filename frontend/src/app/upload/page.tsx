"use client";

import React, { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useDropzone } from "react-dropzone";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api, type UploadResult } from "@/lib/api";
import { formatFileSize } from "@/lib/utils";
import {
  Upload,
  FileText,
  X,
  CheckCircle2,
  AlertCircle,
  Loader2,
  CloudUpload,
  File,
} from "lucide-react";

const ACCEPTED_TYPES = {
  "application/pdf": [".pdf"],
  "image/png": [".png"],
  "image/jpeg": [".jpg", ".jpeg"],
  "image/tiff": [".tiff"],
  "image/webp": [".webp"],
};

interface FileWithPreview extends File {
  preview?: string;
}

export default function UploadPage() {
  const router = useRouter();
  const [files, setFiles] = useState<FileWithPreview[]>([]);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<UploadResult[]>([]);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setError(null);
    setResults([]);
    const newFiles = acceptedFiles.map((file) =>
      Object.assign(file, {
        preview: file.type.startsWith("image/")
          ? URL.createObjectURL(file)
          : undefined,
      })
    );
    setFiles((prev) => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: 20 * 1024 * 1024, // 20MB
    onDropRejected: (rejections) => {
      const msgs = rejections.map((r) => {
        const errs = r.errors.map((e) => e.message).join(", ");
        return `${r.file.name}: ${errs}`;
      });
      setError(msgs.join("\n"));
    },
  });

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;

    setUploading(true);
    setError(null);

    try {
      const response = await api.uploadFiles(files);
      setResults(response.uploads);
      setFiles([]);

      // Redirect to records after a short delay if all successful
      if (response.failed === 0) {
        setTimeout(() => {
          router.push("/records");
        }, 2000);
      }
    } catch (err: any) {
      setError(err.message || "Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-zinc-100">Upload Documents</h1>
          <p className="text-zinc-400 mt-1">
            Drop your financial documents here and we&apos;ll automatically classify and extract them.
          </p>
        </div>

        {/* Drop Zone */}
        <Card className="mb-6 overflow-hidden">
          <div
            {...getRootProps()}
            className={`p-12 border-2 border-dashed rounded-xl transition-all duration-300 cursor-pointer text-center ${
              isDragActive
                ? "border-violet-500 bg-violet-500/5"
                : "border-zinc-700 hover:border-violet-500/50 hover:bg-zinc-800/30"
            }`}
          >
            <input {...getInputProps()} />
            <div className="flex flex-col items-center">
              <div
                className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-4 transition-all duration-300 ${
                  isDragActive
                    ? "bg-violet-500/20 scale-110"
                    : "bg-zinc-800"
                }`}
              >
                <CloudUpload
                  className={`w-8 h-8 transition-colors ${
                    isDragActive ? "text-violet-400" : "text-zinc-400"
                  }`}
                />
              </div>
              <p className="text-lg font-medium text-zinc-200 mb-1">
                {isDragActive ? "Drop your files here" : "Drag & drop documents here"}
              </p>
              <p className="text-sm text-zinc-500 mb-4">
                or click to browse files
              </p>
              <div className="flex gap-2 flex-wrap justify-center">
                {["PDF", "PNG", "JPG", "TIFF", "WEBP"].map((ext) => (
                  <span
                    key={ext}
                    className="px-2 py-1 text-xs font-mono text-zinc-400 bg-zinc-800 rounded-md border border-zinc-700"
                  >
                    .{ext.toLowerCase()}
                  </span>
                ))}
              </div>
              <p className="text-xs text-zinc-600 mt-3">Maximum file size: 20MB</p>
            </div>
          </div>
        </Card>

        {/* Error Message */}
        {error && (
          <Card className="mb-6 border-red-500/20 bg-red-500/5">
            <CardContent className="p-4 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
              <div className="text-sm text-red-300 whitespace-pre-line">{error}</div>
            </CardContent>
          </Card>
        )}

        {/* Selected Files */}
        {files.length > 0 && (
          <Card className="mb-6">
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <CardTitle className="text-base">
                Selected Files ({files.length})
              </CardTitle>
              <Button
                onClick={handleUpload}
                disabled={uploading}
                className="gap-2"
              >
                {uploading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    Upload & Extract
                  </>
                )}
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {files.map((file, index) => (
                  <div
                    key={`${file.name}-${index}`}
                    className="flex items-center justify-between p-3 rounded-lg bg-zinc-800/50 group"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-zinc-700 flex items-center justify-center">
                        <File className="w-5 h-5 text-zinc-300" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-zinc-200">
                          {file.name}
                        </p>
                        <p className="text-xs text-zinc-500">
                          {formatFileSize(file.size)}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => removeFile(index)}
                      className="p-1.5 rounded-md text-zinc-500 hover:text-red-400 hover:bg-red-500/10 opacity-0 group-hover:opacity-100 transition-all cursor-pointer"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Upload Results */}
        {results.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Upload Results</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {results.map((result) => (
                  <div
                    key={result.id}
                    className="flex items-center justify-between p-3 rounded-lg bg-zinc-800/50"
                  >
                    <div className="flex items-center gap-3">
                      {result.status === "processing" ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                      ) : (
                        <AlertCircle className="w-5 h-5 text-red-400" />
                      )}
                      <div>
                        <p className="text-sm font-medium text-zinc-200">
                          {result.filename}
                        </p>
                        <p className="text-xs text-zinc-500">{result.message}</p>
                      </div>
                    </div>
                    <Badge
                      variant={
                        result.status === "processing" ? "success" : "destructive"
                      }
                    >
                      {result.status}
                    </Badge>
                  </div>
                ))}
              </div>
              <div className="mt-4 flex justify-end">
                <Button
                  variant="outline"
                  onClick={() => router.push("/records")}
                  className="gap-2"
                >
                  <FileText className="w-4 h-4" />
                  View Records
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </AppShell>
  );
}
