"use client";

import { Clipboard, Link2, ShieldOff } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";

import { shareApi } from "@/lib/api";
import { getFriendlyErrorMessage } from "@/lib/errors";
import { formatDateTime } from "@/lib/format";
import type { CreatedShareLink, FileRecord, ShareLink } from "@/types/api";
import { StatusMessage } from "@/components/ui/StatusMessage";

type ShareLinksPanelProps = {
  files: FileRecord[];
  initialFileId: string;
  links: ShareLink[];
  token: string;
  onChanged: () => Promise<void>;
};

export function ShareLinksPanel({
  files,
  initialFileId,
  links,
  token,
  onChanged,
}: ShareLinksPanelProps) {
  const [fileId, setFileId] = useState(initialFileId);
  const [expiresInMinutes, setExpiresInMinutes] = useState(60);
  const [maxDownloads, setMaxDownloads] = useState("");
  const [password, setPassword] = useState("");
  const [createdLink, setCreatedLink] = useState<CreatedShareLink | null>(null);
  const [isWorking, setIsWorking] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const latestShareUrl = useMemo(() => {
    if (!createdLink) {
      return "";
    }

    /*
     * The backend returns a backend download path for API clients. The React
     * app presents a friendlier public route that calls that API route behind
     * the scenes, while still showing the raw token only in this create result.
     */
    if (typeof window === "undefined") {
      return `/share/${createdLink.raw_token}`;
    }

    return `${window.location.origin}/share/${createdLink.raw_token}`;
  }, [createdLink]);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    setCreatedLink(null);
    setIsWorking(true);

    try {
      const created = await shareApi.create(token, {
        file_id: fileId,
        expires_in_minutes: expiresInMinutes,
        max_downloads: maxDownloads ? Number(maxDownloads) : undefined,
        password: password || undefined,
      });

      setCreatedLink(created);
      setPassword("");
      setMessage(
        "Share link created. Copy the URL now because the raw token is shown only once.",
      );
      await onChanged();
    } catch (error) {
      setMessage(
        getFriendlyErrorMessage(error, "Share link could not be created."),
      );
    } finally {
      setIsWorking(false);
    }
  }

  async function handleCopy() {
    if (!latestShareUrl) {
      return;
    }

    await navigator.clipboard.writeText(latestShareUrl);
    setMessage("Share URL copied.");
  }

  async function handleRevoke(shareId: string) {
    setIsWorking(true);
    setMessage(null);

    try {
      await shareApi.revoke(token, shareId);
      await onChanged();
      setMessage("Share link revoked. Future downloads through it will be blocked.");
    } catch (error) {
      setMessage(
        getFriendlyErrorMessage(error, "Share link could not be revoked."),
      );
    } finally {
      setIsWorking(false);
    }
  }

  return (
    <section className="rounded-md border border-stone-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-stone-950">Share links</h2>
          <p className="mt-1 text-sm leading-6 text-stone-600">
            Pick a file, set an expiration window, optionally add a password,
            and cap downloads for a safer public handoff.
          </p>
        </div>
        <span className="flex h-10 w-10 items-center justify-center rounded-md bg-amber-50 text-amber-800">
          <Link2 aria-hidden="true" className="h-5 w-5" />
        </span>
      </div>

      <form className="mt-5 grid gap-3" onSubmit={handleCreate}>
        <label className="grid gap-2 text-sm font-medium text-stone-700">
          File
          <select
            className="h-11 rounded-md border border-stone-200 bg-stone-50 px-3 text-sm outline-none focus:border-emerald-700 focus:bg-white"
            disabled={files.length === 0}
            onChange={(event) => setFileId(event.target.value)}
            value={fileId}
          >
            {files.map((file) => (
              <option key={file.id} value={file.id}>
                {file.original_filename}
              </option>
            ))}
          </select>
        </label>

        <div className="grid gap-3 sm:grid-cols-2">
          <label className="grid gap-2 text-sm font-medium text-stone-700">
            Expires in minutes
            <input
              className="h-11 rounded-md border border-stone-200 bg-stone-50 px-3 text-sm outline-none focus:border-emerald-700 focus:bg-white"
              min={1}
              onChange={(event) => setExpiresInMinutes(Number(event.target.value))}
              required
              type="number"
              value={expiresInMinutes}
            />
          </label>
          <label className="grid gap-2 text-sm font-medium text-stone-700">
            Max downloads
            <input
              className="h-11 rounded-md border border-stone-200 bg-stone-50 px-3 text-sm outline-none focus:border-emerald-700 focus:bg-white"
              min={1}
              onChange={(event) => setMaxDownloads(event.target.value)}
              placeholder="Unlimited"
              type="number"
              value={maxDownloads}
            />
          </label>
        </div>

        <label className="grid gap-2 text-sm font-medium text-stone-700">
          Optional password
          <input
            className="h-11 rounded-md border border-stone-200 bg-stone-50 px-3 text-sm outline-none focus:border-emerald-700 focus:bg-white"
            minLength={8}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Minimum 8 characters"
            type="password"
            value={password}
          />
        </label>

        {message ? <StatusMessage tone="info">{message}</StatusMessage> : null}

        {createdLink ? (
          <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-950">
            <p className="font-semibold">New share URL</p>
            <p className="mt-2 break-all font-mono text-xs">{latestShareUrl}</p>
            <p className="mt-2 break-all font-mono text-xs">
              Token: {createdLink.raw_token}
            </p>
            <p className="mt-2 text-xs leading-5">
              Save this URL now. The backend stores only a hash of the token, so
              it cannot show this raw token again later.
            </p>
            <button
              className="mt-3 inline-flex h-9 items-center gap-2 rounded-md bg-emerald-900 px-3 text-xs font-semibold text-white hover:bg-emerald-800"
              onClick={handleCopy}
              type="button"
            >
              <Clipboard aria-hidden="true" className="h-4 w-4" />
              Copy URL
            </button>
          </div>
        ) : null}

        <button
          className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-stone-950 px-4 text-sm font-semibold text-white hover:bg-stone-800 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isWorking || files.length === 0}
          type="submit"
        >
          <Link2 aria-hidden="true" className="h-4 w-4" />
          {isWorking ? "Working..." : "Create share link"}
        </button>
      </form>

      <div className="mt-6 border-t border-stone-200 pt-5">
        <h3 className="text-sm font-semibold text-stone-950">Existing links</h3>
        <div className="mt-3 space-y-3">
          {links.length === 0 ? (
            <div className="rounded-md border border-dashed border-stone-300 bg-stone-50 p-4 text-sm leading-6 text-stone-600">
              No share links yet. Create one after uploading a file, then use
              the public URL to test expiration, passwords, download limits, and
              audit logging.
            </div>
          ) : (
            links.map((link) => (
              <div
                className="rounded-md border border-stone-200 bg-stone-50 p-3"
                key={link.id}
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm font-medium text-stone-950">
                      {link.is_revoked ? "Revoked" : "Active"} link
                    </p>
                    <p className="mt-1 text-xs text-stone-600">
                      Expires {formatDateTime(link.expires_at)} · Downloads{" "}
                      {link.download_count}
                      {link.max_downloads ? ` / ${link.max_downloads}` : ""}
                    </p>
                  </div>
                  <button
                    className="inline-flex h-9 items-center justify-center gap-2 rounded-md border border-rose-200 px-3 text-xs font-semibold text-rose-700 hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-50"
                    disabled={isWorking || link.is_revoked}
                    onClick={() => handleRevoke(link.id)}
                    type="button"
                  >
                    <ShieldOff aria-hidden="true" className="h-4 w-4" />
                    Revoke
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </section>
  );
}
