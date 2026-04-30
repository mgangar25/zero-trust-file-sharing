"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { FileList } from "@/components/dashboard/FileList";
import { FileUploadCard } from "@/components/dashboard/FileUploadCard";
import { SecurityNotes } from "@/components/dashboard/SecurityNotes";
import { ShareLinksPanel } from "@/components/dashboard/ShareLinksPanel";
import { StatusMessage } from "@/components/ui/StatusMessage";
import { filesApi, shareApi } from "@/lib/api";
import { getAuthSession, type AuthSession } from "@/lib/auth";
import { saveBlobToDisk } from "@/lib/download";
import { getFriendlyErrorMessage } from "@/lib/errors";
import type { FileRecord, ShareLink } from "@/types/api";

export function DashboardClient() {
  const router = useRouter();
  const [session, setSession] = useState<AuthSession | null>(null);
  const [files, setFiles] = useState<FileRecord[]>([]);
  const [shareLinks, setShareLinks] = useState<ShareLink[]>([]);
  const [selectedShareFileId, setSelectedShareFileId] = useState("");
  const [busyFileId, setBusyFileId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);

  const loadDashboardData = useCallback(async (activeSession: AuthSession) => {
    setMessage(null);

    const [nextFiles, nextShareLinks] = await Promise.all([
      filesApi.list(activeSession.token),
      shareApi.list(activeSession.token),
    ]);

    setFiles(nextFiles);
    setShareLinks(nextShareLinks);
    setSelectedShareFileId((current) =>
      nextFiles.some((file) => file.id === current)
        ? current
        : nextFiles[0]?.id || "",
    );
  }, []);

  useEffect(() => {
    let isCancelled = false;

    async function bootstrapDashboard() {
      const storedSession = getAuthSession();

      if (!storedSession) {
        router.push("/login");
        return;
      }

      try {
        await loadDashboardData(storedSession);
        if (!isCancelled) {
          setSession(storedSession);
        }
      } catch (error) {
        if (!isCancelled) {
          setMessage(
            getFriendlyErrorMessage(
              error,
              "Dashboard data could not be loaded.",
            ),
          );
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    void bootstrapDashboard();

    return () => {
      isCancelled = true;
    };
  }, [loadDashboardData, router]);

  const refreshData = useCallback(async () => {
    const activeSession = getAuthSession();

    if (!activeSession) {
      router.push("/login");
      return;
    }

    await loadDashboardData(activeSession);
  }, [loadDashboardData, router]);

  const userLabel = session?.email || session?.userId || "authenticated user";

  async function handleDownload(file: FileRecord) {
    if (!session) {
      return;
    }

    setBusyFileId(file.id);
    setMessage(null);

    try {
      saveBlobToDisk(await filesApi.download(session.token, file));
    } catch (error) {
      setMessage(
        getFriendlyErrorMessage(error, "Download could not start."),
      );
    } finally {
      setBusyFileId(null);
    }
  }

  async function handleDelete(fileId: string) {
    if (!session) {
      return;
    }

    setBusyFileId(fileId);
    setMessage(null);

    try {
      await filesApi.delete(session.token, fileId);
      await refreshData();
    } catch (error) {
      setMessage(getFriendlyErrorMessage(error, "File was not deleted."));
    } finally {
      setBusyFileId(null);
    }
  }

  function handleCreateShare(fileId: string) {
    setSelectedShareFileId(fileId);
    document.getElementById("share-links")?.scrollIntoView({ behavior: "smooth" });
  }

  if (!session) {
    return null;
  }

  return (
    <AppShell
      description="Upload encrypted files, manage owner-only downloads, create revocable share links, and review the access trail."
      eyebrow="Dashboard"
      title="Secure file workspace"
      userLabel={userLabel}
    >
      <div className="grid gap-6 xl:grid-cols-[380px_1fr]">
        <div className="space-y-6">
          <FileUploadCard token={session.token} onUploaded={refreshData} />
          <div id="share-links">
            <ShareLinksPanel
              files={files}
              initialFileId={selectedShareFileId}
              key={selectedShareFileId || "share-panel"}
              links={shareLinks}
              onChanged={refreshData}
              token={session.token}
            />
          </div>
        </div>

        <div className="space-y-6">
          {message ? <StatusMessage tone="error">{message}</StatusMessage> : null}
          {isLoading ? (
            <div className="rounded-md border border-stone-200 bg-white p-6 text-sm text-stone-600 shadow-sm">
              Loading dashboard...
            </div>
          ) : (
            <FileList
              busyFileId={busyFileId}
              files={files}
              onCreateShare={handleCreateShare}
              onDelete={handleDelete}
              onDownload={handleDownload}
            />
          )}
          <SecurityNotes />
        </div>
      </div>
    </AppShell>
  );
}
