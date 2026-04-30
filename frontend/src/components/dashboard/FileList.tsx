"use client";

import { Download, FileUp, Link2, Trash2 } from "lucide-react";

import type { FileRecord } from "@/types/api";
import { formatBytes, formatDateTime } from "@/lib/format";

type FileListProps = {
  files: FileRecord[];
  busyFileId: string | null;
  onCreateShare: (fileId: string) => void;
  onDelete: (fileId: string) => Promise<void>;
  onDownload: (file: FileRecord) => Promise<void>;
};

export function FileList({
  files,
  busyFileId,
  onCreateShare,
  onDelete,
  onDownload,
}: FileListProps) {
  return (
    <section className="rounded-md border border-stone-200 bg-white shadow-sm">
      <div className="border-b border-stone-200 px-5 py-4">
        <h2 className="text-lg font-semibold text-stone-950">Files</h2>
        <p className="mt-1 text-sm text-stone-600">
          Owner-only metadata returned by <span className="font-mono">GET /files</span>.
        </p>
      </div>

      {files.length === 0 ? (
        <div className="px-5 py-12 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-md bg-emerald-50 text-emerald-800">
            <FileUp aria-hidden="true" className="h-6 w-6" />
          </div>
          <h3 className="mt-4 text-base font-semibold text-stone-950">
            No encrypted files yet
          </h3>
          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-stone-600">
            Upload a file to see owner-scoped metadata, download controls, and
            share-link actions appear here.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-stone-200 bg-stone-50 text-xs uppercase tracking-[0.14em] text-stone-500">
                <th className="px-5 py-3 font-semibold">Filename</th>
                <th className="px-5 py-3 font-semibold">Size</th>
                <th className="px-5 py-3 font-semibold">MIME type</th>
                <th className="px-5 py-3 font-semibold">Created</th>
                <th className="px-5 py-3 text-right font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {files.map((file) => (
                <tr
                  className="border-b border-stone-100 last:border-b-0"
                  key={file.id}
                >
                  <td className="px-5 py-4 font-medium text-stone-950">
                    {file.original_filename}
                  </td>
                  <td className="px-5 py-4 text-stone-600">
                    {formatBytes(file.file_size)}
                  </td>
                  <td className="px-5 py-4 text-stone-600">
                    {file.mime_type || "application/octet-stream"}
                  </td>
                  <td className="px-5 py-4 text-stone-600">
                    {formatDateTime(file.created_at)}
                  </td>
                  <td className="px-5 py-4">
                    <div className="flex justify-end gap-2">
                      <button
                        aria-label={`Download ${file.original_filename}`}
                        className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-stone-200 text-stone-700 hover:bg-stone-50 disabled:cursor-not-allowed disabled:opacity-60"
                        disabled={busyFileId === file.id}
                        onClick={() => onDownload(file)}
                        title="Download"
                        type="button"
                      >
                        <Download aria-hidden="true" className="h-4 w-4" />
                      </button>
                      <button
                        aria-label={`Create share link for ${file.original_filename}`}
                        className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-stone-200 text-emerald-800 hover:bg-emerald-50 disabled:cursor-not-allowed disabled:opacity-60"
                        disabled={busyFileId === file.id}
                        onClick={() => onCreateShare(file.id)}
                        title="Create share link"
                        type="button"
                      >
                        <Link2 aria-hidden="true" className="h-4 w-4" />
                      </button>
                      <button
                        aria-label={`Delete ${file.original_filename}`}
                        className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-rose-200 text-rose-700 hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-60"
                        disabled={busyFileId === file.id}
                        onClick={() => onDelete(file.id)}
                        title="Delete"
                        type="button"
                      >
                        <Trash2 aria-hidden="true" className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
