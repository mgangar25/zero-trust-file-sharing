"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { Download, FileKey2, LockKeyhole } from "lucide-react";

import { shareApi } from "@/lib/api";
import { saveBlobToDisk } from "@/lib/download";
import { getFriendlyErrorMessage } from "@/lib/errors";
import { StatusMessage } from "@/components/ui/StatusMessage";

type PublicShareClientProps = {
  token: string;
};

export function PublicShareClient({ token }: PublicShareClientProps) {
  const [password, setPassword] = useState("");
  const [isDownloading, setIsDownloading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [messageTone, setMessageTone] = useState<"success" | "error">("success");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsDownloading(true);
    setMessage(null);

    try {
      saveBlobToDisk(await shareApi.downloadPublic(token, password));
      setMessageTone("success");
      setMessage("Download started.");
    } catch (error) {
      setMessageTone("error");
      setMessage(
        getFriendlyErrorMessage(
          error,
          "This share link could not be downloaded.",
        ),
      );
    } finally {
      setIsDownloading(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f7f4ee] px-4 py-10 text-stone-950">
      <div className="mx-auto max-w-xl">
        <Link className="inline-flex items-center gap-3" href="/">
          <span className="flex h-10 w-10 items-center justify-center rounded-md bg-emerald-950 text-white">
            <FileKey2 aria-hidden="true" className="h-5 w-5" />
          </span>
          <span className="text-sm font-semibold">Zero-Trust File Sharing</span>
        </Link>

        <section className="mt-12 rounded-md border border-stone-200 bg-white p-6 shadow-sm">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-800">
                Public Share
              </p>
              <h1 className="mt-3 text-3xl font-semibold tracking-normal">
                Download shared file
              </h1>
              <p className="mt-3 text-sm leading-6 text-stone-600">
                The backend validates this token, checks limits, records the
                attempt, decrypts the file, and streams the response.
              </p>
            </div>
            <span className="flex h-11 w-11 items-center justify-center rounded-md bg-amber-50 text-amber-800">
              <Download aria-hidden="true" className="h-5 w-5" />
            </span>
          </div>

          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
            <label className="block">
              <span className="text-sm font-medium text-stone-700">
                Password
              </span>
              <span className="mt-2 flex h-12 items-center gap-2 rounded-md border border-stone-200 bg-stone-50 px-3 focus-within:border-emerald-700 focus-within:bg-white">
                <LockKeyhole
                  aria-hidden="true"
                  className="h-4 w-4 text-stone-500"
                />
                <input
                  className="w-full bg-transparent text-sm outline-none"
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Leave blank if no password was set"
                  type="password"
                  value={password}
                />
              </span>
            </label>

            {message ? (
              <StatusMessage tone={messageTone}>{message}</StatusMessage>
            ) : null}

            <button
              className="inline-flex h-12 w-full items-center justify-center gap-2 rounded-md bg-stone-950 px-4 text-sm font-semibold text-white hover:bg-stone-800 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isDownloading}
              type="submit"
            >
              <Download aria-hidden="true" className="h-4 w-4" />
              {isDownloading ? "Starting download..." : "Download file"}
            </button>
          </form>
        </section>
      </div>
    </main>
  );
}
