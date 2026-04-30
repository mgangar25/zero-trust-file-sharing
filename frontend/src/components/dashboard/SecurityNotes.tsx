import Link from "next/link";
import {
  DatabaseZap,
  FileKey2,
  Fingerprint,
  KeyRound,
  ShieldCheck,
} from "lucide-react";

const notes = [
  {
    title: "AES-GCM before R2",
    body: "The backend encrypts file bytes before object storage receives them.",
    icon: ShieldCheck,
  },
  {
    title: "One key per file",
    body: "Every upload gets a fresh file key, limiting blast radius if metadata changes.",
    icon: FileKey2,
  },
  {
    title: "Wrapped file keys",
    body: "The master key protects each file key instead of encrypting every file directly.",
    icon: KeyRound,
  },
  {
    title: "Hashed share tokens",
    body: "The raw token is shown once, while the database keeps only the token hash.",
    icon: Fingerprint,
  },
  {
    title: "Hashed passwords",
    body: "Optional share passwords are stored as password hashes, not plaintext.",
    icon: DatabaseZap,
  },
];

export function SecurityNotes() {
  return (
    <section className="rounded-md border border-stone-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-stone-950">Security model</h2>
          <p className="mt-1 text-sm leading-6 text-stone-600">
            Audit logs record successful and blocked public access attempts,
            including status, reason, IP address, user agent, and time.
          </p>
        </div>
        <Link
          className="inline-flex h-10 items-center justify-center rounded-md border border-stone-200 px-3 text-sm font-semibold text-stone-700 hover:bg-stone-50"
          href="/security"
        >
          Full security page
        </Link>
      </div>
      <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        {notes.map((note) => {
          const Icon = note.icon;

          return (
            <div className="rounded-md border border-stone-200 p-4" key={note.title}>
              <Icon aria-hidden="true" className="h-5 w-5 text-emerald-800" />
              <h3 className="mt-3 text-sm font-semibold text-stone-950">
                {note.title}
              </h3>
              <p className="mt-2 text-sm leading-6 text-stone-600">{note.body}</p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
