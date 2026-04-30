"use client";

import { ChangeEvent, FormEvent, useState } from "react";
import { UploadCloud } from "lucide-react";

import { filesApi } from "@/lib/api";
import { getFriendlyErrorMessage } from "@/lib/errors";
import { formatBytes } from "@/lib/format";
import { StatusMessage } from "@/components/ui/StatusMessage";

type FileUploadCardProps = {
  token: string;
  onUploaded: () => Promise<void>;
};

export function FileUploadCard({ token, onUploaded }: FileUploadCardProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [messageTone, setMessageTone] = useState<"success" | "error">(
    "success",
  );

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setSelectedFile(event.target.files?.[0] || null);
    setMessage(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!selectedFile) {
      setMessageTone("error");
      setMessage("Choose a file before uploading.");
      return;
    }

    setIsUploading(true);
    setMessage(null);

    try {
      await filesApi.upload(token, selectedFile);
      setSelectedFile(null);
      await onUploaded();
      setMessageTone("success");
      setMessage(
        "Upload complete. The backend encrypted the file before storing it in R2.",
      );
    } catch (error) {
      setMessageTone("error");
      setMessage(
        getFriendlyErrorMessage(error, "Upload failed. Please try again."),
      );
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <section className="rounded-md border border-stone-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-stone-950">Upload file</h2>
          <p className="mt-1 text-sm leading-6 text-stone-600">
            Choose any demo file. FastAPI reads the bytes, creates a fresh file
            key, encrypts with AES-GCM, and stores only ciphertext in R2.
          </p>
        </div>
        <span className="flex h-10 w-10 items-center justify-center rounded-md bg-emerald-50 text-emerald-800">
          <UploadCloud aria-hidden="true" className="h-5 w-5" />
        </span>
      </div>

      <form className="mt-5 space-y-4" onSubmit={handleSubmit}>
        <label className="block rounded-md border border-dashed border-stone-300 bg-stone-50 px-4 py-6 text-center hover:border-emerald-600 hover:bg-emerald-50/50">
          <span className="block text-sm font-medium text-stone-700">
            {selectedFile
              ? selectedFile.name
              : "Drop in a file for encrypted storage"}
          </span>
          {selectedFile ? (
            <span className="mt-1 block text-xs text-stone-500">
              {formatBytes(selectedFile.size)}
            </span>
          ) : (
            <span className="mt-1 block text-xs text-stone-500">
              The original file never gets written to local disk by the backend.
            </span>
          )}
          <input className="sr-only" onChange={handleFileChange} type="file" />
        </label>

        {message ? (
          <StatusMessage tone={messageTone}>{message}</StatusMessage>
        ) : null}

        <button
          className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-md bg-emerald-900 px-4 text-sm font-semibold text-white hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isUploading}
          type="submit"
        >
          <UploadCloud aria-hidden="true" className="h-4 w-4" />
          {isUploading ? "Uploading..." : "Upload encrypted file"}
        </button>
      </form>
    </section>
  );
}
