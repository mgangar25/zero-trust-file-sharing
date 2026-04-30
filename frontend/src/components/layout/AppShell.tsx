"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FileKey2, LockKeyhole, LogOut, ScrollText, ShieldCheck } from "lucide-react";
import type { ReactNode } from "react";

import { clearAuthSession } from "@/lib/auth";

type AppShellProps = {
  children: ReactNode;
  eyebrow: string;
  title: string;
  description: string;
  userLabel?: string | null;
};

export function AppShell({
  children,
  eyebrow,
  title,
  description,
  userLabel,
}: AppShellProps) {
  const router = useRouter();

  function handleLogout() {
    clearAuthSession();
    router.push("/login");
  }

  return (
    <div className="min-h-screen bg-[#f7f4ee] text-stone-950">
      <header className="border-b border-stone-200 bg-white/85 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
          <Link className="flex items-center gap-3" href="/">
            <span className="flex h-10 w-10 items-center justify-center rounded-md bg-emerald-950 text-white">
              <FileKey2 aria-hidden="true" className="h-5 w-5" />
            </span>
            <span>
              <span className="block text-sm font-semibold">
                Zero-Trust File Sharing
              </span>
              <span className="block text-xs text-stone-500">
                Encrypted portfolio system
              </span>
            </span>
          </Link>

          <nav className="flex flex-wrap items-center gap-2 text-sm">
            <Link
              className="inline-flex h-10 items-center gap-2 rounded-md border border-stone-200 bg-white px-3 font-medium text-stone-700 hover:border-stone-300 hover:bg-stone-50"
              href="/dashboard"
            >
              <ShieldCheck aria-hidden="true" className="h-4 w-4" />
              Dashboard
            </Link>
            <Link
              className="inline-flex h-10 items-center gap-2 rounded-md border border-stone-200 bg-white px-3 font-medium text-stone-700 hover:border-stone-300 hover:bg-stone-50"
              href="/audit"
            >
              <ScrollText aria-hidden="true" className="h-4 w-4" />
              Audit
            </Link>
            <Link
              className="inline-flex h-10 items-center gap-2 rounded-md border border-stone-200 bg-white px-3 font-medium text-stone-700 hover:border-stone-300 hover:bg-stone-50"
              href="/security"
            >
              <LockKeyhole aria-hidden="true" className="h-4 w-4" />
              Security
            </Link>
            {userLabel ? (
              <button
                className="inline-flex h-10 items-center gap-2 rounded-md bg-stone-950 px-3 font-medium text-white hover:bg-stone-800"
                onClick={handleLogout}
                type="button"
              >
                <LogOut aria-hidden="true" className="h-4 w-4" />
                Logout
              </button>
            ) : null}
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-800">
              {eyebrow}
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-normal text-stone-950 sm:text-4xl">
              {title}
            </h1>
            <p className="mt-3 max-w-2xl text-base leading-7 text-stone-600">
              {description}
            </p>
          </div>

          {userLabel ? (
            <div className="rounded-md border border-stone-200 bg-white px-4 py-3 text-sm text-stone-600">
              Signed in as{" "}
              <span className="font-semibold text-stone-950">{userLabel}</span>
            </div>
          ) : null}
        </div>

        {children}
      </main>
    </div>
  );
}
