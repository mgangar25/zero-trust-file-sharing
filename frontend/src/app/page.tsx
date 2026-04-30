import Link from "next/link";
import {
  ArrowRight,
  Clock3,
  Download,
  FileKey2,
  Fingerprint,
  KeyRound,
  Link2,
  LockKeyhole,
  ScrollText,
  ShieldCheck,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

const featureCards: { icon: LucideIcon; title: string; body: string }[] = [
  {
    icon: ShieldCheck,
    title: "AES-GCM encrypted storage",
    body: "Files are encrypted by the backend before Cloudflare R2 receives the bytes.",
  },
  {
    icon: Fingerprint,
    title: "JWT authentication",
    body: "FastAPI issues bearer tokens and every owner route verifies the current user.",
  },
  {
    icon: Link2,
    title: "Revocable share links",
    body: "Owners can disable a link without deleting the file or losing audit history.",
  },
  {
    icon: LockKeyhole,
    title: "Password protection",
    body: "Optional share passwords are checked server-side and stored only as hashes.",
  },
  {
    icon: Download,
    title: "Download limits",
    body: "Temporary links can stop serving files after a configured download count.",
  },
  {
    icon: ScrollText,
    title: "Audit logs",
    body: "Successful and blocked public access attempts are recorded with reasons.",
  },
];

const demoStats = [
  ["19", "backend tests passing"],
  ["0", "plaintext files stored in R2"],
  ["1x", "raw share token reveal"],
];

export default function Home() {
  return (
    <main className="min-h-screen bg-[#f8faf9] text-stone-950">
      <section className="border-b border-stone-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-5 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
          <div className="flex items-center gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-md bg-emerald-950 text-white">
              <FileKey2 aria-hidden="true" className="h-5 w-5" />
            </span>
            <div>
              <p className="text-sm font-semibold">Zero-Trust File Sharing</p>
              <p className="text-xs text-stone-500">FastAPI + Next.js + R2</p>
            </div>
          </div>
          <nav className="flex flex-wrap gap-2 text-sm font-medium">
            <Link
              className="inline-flex h-10 items-center gap-2 rounded-md border border-stone-200 px-3 text-stone-700 hover:bg-stone-50"
              href="/security"
            >
              Security model
            </Link>
            <Link
              className="inline-flex h-10 items-center gap-2 rounded-md border border-stone-200 px-3 text-stone-700 hover:bg-stone-50"
              href="/login"
            >
              Login
            </Link>
            <Link
              className="inline-flex h-10 items-center gap-2 rounded-md bg-stone-950 px-3 text-white hover:bg-stone-800"
              href="/register"
            >
              Register
              <ArrowRight aria-hidden="true" className="h-4 w-4" />
            </Link>
          </nav>
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-10 px-4 py-12 sm:px-6 lg:grid-cols-[1.03fr_0.97fr] lg:items-center lg:px-8 lg:py-16">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-800">
            Secure Portfolio Demo
          </p>
          <h1 className="mt-4 max-w-4xl text-5xl font-semibold tracking-normal text-stone-950 sm:text-6xl">
            Zero-trust file sharing with encrypted storage and auditable access.
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-stone-600">
            A full-stack security project that combines JWT auth, per-file
            encryption keys, Cloudflare R2 ciphertext storage, hashed share
            tokens, revocation, download limits, and access logs.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              className="inline-flex h-12 items-center gap-2 rounded-md bg-emerald-900 px-5 text-sm font-semibold text-white hover:bg-emerald-800"
              href="/dashboard"
            >
              Open dashboard
              <ArrowRight aria-hidden="true" className="h-4 w-4" />
            </Link>
            <Link
              className="inline-flex h-12 items-center gap-2 rounded-md border border-stone-300 bg-white px-5 text-sm font-semibold text-stone-800 hover:bg-stone-50"
              href="/security"
            >
              Review security
              <LockKeyhole aria-hidden="true" className="h-4 w-4" />
            </Link>
          </div>

          <div className="mt-8 grid max-w-2xl gap-3 sm:grid-cols-3">
            {demoStats.map(([value, label]) => (
              <div
                className="rounded-md border border-stone-200 bg-white p-4"
                key={label}
              >
                <p className="text-2xl font-semibold text-stone-950">{value}</p>
                <p className="mt-1 text-xs font-medium uppercase tracking-[0.14em] text-stone-500">
                  {label}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-md border border-stone-200 bg-white p-5 shadow-sm">
          <div className="rounded-md bg-stone-950 p-5 text-white">
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div>
                <p className="text-sm font-semibold">Live security workflow</p>
                <p className="text-xs text-stone-300">
                  upload, share, download, audit
                </p>
              </div>
              <ShieldCheck
                aria-hidden="true"
                className="h-5 w-5 text-emerald-300"
              />
            </div>

            <div className="mt-5 space-y-3">
              {[
                ["Encrypt", "AES-GCM protects bytes before object storage."],
                ["Wrap", "A master key wraps each random file key."],
                ["Share", "Raw tokens are shown once, then hashed."],
                ["Audit", "Failures and successes keep clear reasons."],
              ].map(([title, body], index) => (
                <div className="flex gap-3" key={title}>
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-white/10 text-sm font-semibold text-emerald-200">
                    {index + 1}
                  </span>
                  <div>
                    <p className="text-sm font-semibold">{title}</p>
                    <p className="text-sm leading-6 text-stone-300">{body}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            {[
              { icon: KeyRound, label: "Wrapped keys", tone: "text-emerald-800" },
              { icon: Clock3, label: "Expiring links", tone: "text-amber-700" },
              { icon: ScrollText, label: "Audit trail", tone: "text-sky-700" },
            ].map(({ icon: Icon, label, tone }) => (
              <div
                className="rounded-md border border-stone-200 bg-stone-50 p-3 text-sm font-medium text-stone-700"
                key={label}
              >
                <Icon aria-hidden="true" className={`mb-2 h-4 w-4 ${tone}`} />
                {label}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-stone-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-800">
              Feature Set
            </p>
            <h2 className="mt-3 text-3xl font-semibold tracking-normal text-stone-950">
              Built to show practical secure-system thinking.
            </h2>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {featureCards.map((feature) => {
              const Icon = feature.icon;

              return (
                <article
                  className="rounded-md border border-stone-200 bg-[#f8faf9] p-5"
                  key={feature.title}
                >
                  <Icon aria-hidden="true" className="h-5 w-5 text-emerald-800" />
                  <h3 className="mt-4 text-base font-semibold text-stone-950">
                    {feature.title}
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-stone-600">
                    {feature.body}
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
