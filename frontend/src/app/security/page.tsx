import Link from "next/link";
import {
  ArrowRight,
  Clock3,
  Database,
  FileKey2,
  Fingerprint,
  KeyRound,
  Link2,
  LockKeyhole,
  ScrollText,
  ShieldCheck,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

const securityPoints: { icon: LucideIcon; title: string; body: string }[] = [
  {
    icon: ShieldCheck,
    title: "Encrypted before object storage",
    body: "The backend encrypts uploaded file bytes with AES-GCM before sending anything to Cloudflare R2.",
  },
  {
    icon: Database,
    title: "R2 stores encrypted bytes only",
    body: "Cloudflare R2 receives ciphertext, while the original filename, MIME type, and size are stored separately as owner-scoped metadata.",
  },
  {
    icon: FileKey2,
    title: "Unique AES-256 key per file",
    body: "Each upload gets its own random file key, so one file's encryption material is isolated from another file's data.",
  },
  {
    icon: KeyRound,
    title: "File keys are wrapped",
    body: "The master encryption key wraps each per-file key before metadata is saved, avoiding direct storage of raw file keys.",
  },
  {
    icon: Fingerprint,
    title: "Share tokens are hashed",
    body: "A raw share token is shown only once. The database stores a token hash, so saved rows do not expose usable public URLs.",
  },
  {
    icon: LockKeyhole,
    title: "Optional passwords are hashed",
    body: "When a share password is set, the backend stores a password hash and verifies submitted passwords server-side.",
  },
  {
    icon: Link2,
    title: "Limited public access",
    body: "Share links support expiration, owner revocation, and optional download limits for controlled temporary access.",
  },
  {
    icon: ScrollText,
    title: "Auditable access attempts",
    body: "Successful and failed public downloads are logged with status, reason, IP address, user agent, and timestamp.",
  },
];

const accessRules = [
  "JWT-authenticated users can list, download, delete, and share only their own files.",
  "Public share tokens grant access to one linked file, not to a user account or file list.",
  "Revoked, expired, over-limit, missing-password, and invalid-password attempts are blocked and logged.",
];

export default function SecurityPage() {
  return (
    <main className="min-h-screen bg-[#f8faf9] text-stone-950">
      <section className="border-b border-stone-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-5 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
          <Link className="flex items-center gap-3" href="/">
            <span className="flex h-11 w-11 items-center justify-center rounded-md bg-emerald-950 text-white">
              <FileKey2 aria-hidden="true" className="h-5 w-5" />
            </span>
            <div>
              <p className="text-sm font-semibold">Zero-Trust File Sharing</p>
              <p className="text-xs text-stone-500">Security model</p>
            </div>
          </Link>
          <nav className="flex flex-wrap gap-2 text-sm font-medium">
            <Link
              className="inline-flex h-10 items-center rounded-md border border-stone-200 px-3 text-stone-700 hover:bg-stone-50"
              href="/dashboard"
            >
              Dashboard
            </Link>
            <Link
              className="inline-flex h-10 items-center rounded-md border border-stone-200 px-3 text-stone-700 hover:bg-stone-50"
              href="/audit"
            >
              Audit
            </Link>
          </nav>
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-8 px-4 py-12 sm:px-6 lg:grid-cols-[0.95fr_1.05fr] lg:px-8 lg:py-16">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-800">
            Architecture Security
          </p>
          <h1 className="mt-4 text-4xl font-semibold tracking-normal text-stone-950 sm:text-5xl">
            A zero-trust approach for a practical file-sharing workflow.
          </h1>
          <p className="mt-5 text-lg leading-8 text-stone-600">
            This project assumes storage should not need to be trusted with
            plaintext. The backend authenticates users, encrypts files before
            storage, limits public access through hashed-token share links, and
            records access attempts for review.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              className="inline-flex h-12 items-center gap-2 rounded-md bg-emerald-900 px-5 text-sm font-semibold text-white hover:bg-emerald-800"
              href="/dashboard"
            >
              Try the dashboard
              <ArrowRight aria-hidden="true" className="h-4 w-4" />
            </Link>
            <Link
              className="inline-flex h-12 items-center gap-2 rounded-md border border-stone-300 bg-white px-5 text-sm font-semibold text-stone-800 hover:bg-stone-50"
              href="/"
            >
              Back to overview
            </Link>
          </div>
        </div>

        <div className="rounded-md border border-stone-200 bg-white p-5 shadow-sm">
          <div className="rounded-md bg-stone-950 p-5 text-white">
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-md bg-emerald-400/15 text-emerald-200">
                <Clock3 aria-hidden="true" className="h-5 w-5" />
              </span>
              <div>
                <p className="text-sm font-semibold">Access lifecycle</p>
                <p className="text-xs text-stone-300">
                  authenticate, authorize, decrypt, audit
                </p>
              </div>
            </div>
            <div className="mt-5 space-y-3">
              {accessRules.map((rule) => (
                <div className="rounded-md bg-white/5 p-3 text-sm leading-6 text-stone-200" key={rule}>
                  {rule}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="border-t border-stone-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {securityPoints.map((point) => {
              const Icon = point.icon;

              return (
                <article
                  className="rounded-md border border-stone-200 bg-[#f8faf9] p-5"
                  key={point.title}
                >
                  <Icon aria-hidden="true" className="h-5 w-5 text-emerald-800" />
                  <h2 className="mt-4 text-base font-semibold text-stone-950">
                    {point.title}
                  </h2>
                  <p className="mt-2 text-sm leading-6 text-stone-600">
                    {point.body}
                  </p>
                </article>
              );
            })}
          </div>
        </div>
      </section>
    </main>
  );
}
