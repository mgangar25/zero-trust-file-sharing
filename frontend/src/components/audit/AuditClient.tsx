"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { StatusMessage } from "@/components/ui/StatusMessage";
import { auditApi } from "@/lib/api";
import { getFriendlyErrorMessage } from "@/lib/errors";
import { formatDateTime, humanizeReason } from "@/lib/format";
import { getAuthSession, type AuthSession } from "@/lib/auth";
import type { AuditLog } from "@/types/api";

export function AuditClient() {
  const router = useRouter();
  const [session, setSession] = useState<AuthSession | null>(null);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    let isCancelled = false;

    async function bootstrapAudit() {
      const storedSession = getAuthSession();

      if (!storedSession) {
        router.push("/login");
        return;
      }

      try {
        const nextLogs = await auditApi.list(storedSession.token);

        if (!isCancelled) {
          setLogs(nextLogs);
          setSession(storedSession);
        }
      } catch (error) {
        if (!isCancelled) {
          setMessage(
            getFriendlyErrorMessage(error, "Audit logs could not be loaded."),
          );
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    void bootstrapAudit();

    return () => {
      isCancelled = true;
    };
  }, [router]);

  if (!session) {
    return null;
  }

  return (
    <AppShell
      description="Review successful and blocked public share-link download attempts for files you own."
      eyebrow="Audit Logs"
      title="Access history"
      userLabel={session.email || session.userId}
    >
      {message ? <StatusMessage tone="error">{message}</StatusMessage> : null}

      <section className="mt-6 rounded-md border border-stone-200 bg-white shadow-sm">
        <div className="border-b border-stone-200 px-5 py-4">
          <h2 className="text-lg font-semibold text-stone-950">Events</h2>
          <p className="mt-1 text-sm text-stone-600">
            Returned by <span className="font-mono">GET /audit</span> after
            owner scoping on the backend.
          </p>
        </div>

        {isLoading ? (
          <div className="px-5 py-10 text-sm text-stone-600">
            Loading audit events...
          </div>
        ) : logs.length === 0 ? (
          <div className="px-5 py-10 text-sm text-stone-600">
            No access attempts recorded yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[860px] border-collapse text-left text-sm">
              <thead>
                <tr className="border-b border-stone-200 bg-stone-50 text-xs uppercase tracking-[0.14em] text-stone-500">
                  <th className="px-5 py-3 font-semibold">Status</th>
                  <th className="px-5 py-3 font-semibold">Reason</th>
                  <th className="px-5 py-3 font-semibold">IP address</th>
                  <th className="px-5 py-3 font-semibold">User agent</th>
                  <th className="px-5 py-3 font-semibold">Time</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => {
                  const isSuccess = log.status === "success";

                  return (
                    <tr
                      className="border-b border-stone-100 last:border-b-0"
                      key={log.id}
                    >
                      <td className="px-5 py-4">
                        <span
                          className={`inline-flex rounded-md px-2 py-1 text-xs font-semibold ${
                            isSuccess
                              ? "bg-emerald-50 text-emerald-800"
                              : "bg-rose-50 text-rose-700"
                          }`}
                        >
                          {log.status}
                        </span>
                      </td>
                      <td className="px-5 py-4 capitalize text-stone-700">
                        {humanizeReason(log.reason)}
                      </td>
                      <td className="px-5 py-4 font-mono text-xs text-stone-600">
                        {log.ip_address || "not captured"}
                      </td>
                      <td className="max-w-[320px] truncate px-5 py-4 text-stone-600">
                        {log.user_agent || "not captured"}
                      </td>
                      <td className="px-5 py-4 text-stone-600">
                        {formatDateTime(log.created_at)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </AppShell>
  );
}
