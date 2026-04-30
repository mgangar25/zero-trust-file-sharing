"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { LockKeyhole, Mail, ShieldCheck } from "lucide-react";
import { FormEvent, useState } from "react";

import { authApi } from "@/lib/api";
import { saveAuthSession } from "@/lib/auth";
import { getFriendlyErrorMessage } from "@/lib/errors";
import { StatusMessage } from "@/components/ui/StatusMessage";

type AuthFormProps = {
  mode: "login" | "register";
};

export function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter();
  const isRegister = mode === "register";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setMessage(null);

    try {
      let userId: string | undefined;

      if (isRegister) {
        /*
         * Register returns safe user data, not a JWT. Logging in immediately
         * after registration gives the dashboard one simple post-signup path
         * while the backend keeps registration and authentication separate.
         */
        const createdUser = await authApi.register(email, password);
        userId = createdUser.id;
      }

      const tokenResponse = await authApi.login(email, password);
      saveAuthSession(tokenResponse.access_token, email, userId);
      router.push("/dashboard");
    } catch (error) {
      setMessage(
        getFriendlyErrorMessage(
          error,
          "Something went wrong. Please try again.",
        ),
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#f7f4ee] px-4 py-10 text-stone-950">
      <div className="mx-auto grid max-w-6xl gap-8 lg:grid-cols-[1fr_440px] lg:items-center">
        <section>
          <Link className="inline-flex items-center gap-3" href="/">
            <span className="flex h-11 w-11 items-center justify-center rounded-md bg-emerald-950 text-white">
              <ShieldCheck aria-hidden="true" className="h-5 w-5" />
            </span>
            <span>
              <span className="block text-sm font-semibold">
                Zero-Trust File Sharing
              </span>
              <span className="block text-xs text-stone-500">
                Encrypted local-dev frontend
              </span>
            </span>
          </Link>

          <div className="mt-16 max-w-xl">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-800">
              {isRegister ? "Create Account" : "Welcome Back"}
            </p>
            <h1 className="mt-3 text-4xl font-semibold tracking-normal text-stone-950 sm:text-5xl">
              {isRegister ? "Start a secure workspace." : "Return to your vault."}
            </h1>
            <p className="mt-5 text-lg leading-8 text-stone-600">
              Files stay private by design: encrypted before storage, scoped to
              the signed-in owner, and shared only through revocable links.
            </p>
          </div>
        </section>

        <section className="rounded-md border border-stone-200 bg-white p-6 shadow-sm">
          <div>
            <h2 className="text-2xl font-semibold">
              {isRegister ? "Register" : "Login"}
            </h2>
            <p className="mt-2 text-sm leading-6 text-stone-600">
              {isRegister
                ? "Create a user in the FastAPI backend."
                : "Use the JWT returned by the FastAPI backend."}
            </p>
          </div>

          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
            <label className="block">
              <span className="text-sm font-medium text-stone-700">Email</span>
              <span className="mt-2 flex h-12 items-center gap-2 rounded-md border border-stone-200 bg-stone-50 px-3 focus-within:border-emerald-700 focus-within:bg-white">
                <Mail aria-hidden="true" className="h-4 w-4 text-stone-500" />
                <input
                  className="w-full bg-transparent text-sm outline-none"
                  onChange={(event) => setEmail(event.target.value)}
                  required
                  type="email"
                  value={email}
                />
              </span>
            </label>

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
                  minLength={8}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                  type="password"
                  value={password}
                />
              </span>
            </label>

            {message ? <StatusMessage tone="error">{message}</StatusMessage> : null}

            <button
              className="inline-flex h-12 w-full items-center justify-center rounded-md bg-stone-950 px-4 text-sm font-semibold text-white hover:bg-stone-800 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSubmitting}
              type="submit"
            >
              {isSubmitting
                ? "Working..."
                : isRegister
                  ? "Create account"
                  : "Login"}
            </button>
          </form>

          <p className="mt-5 text-sm text-stone-600">
            {isRegister ? "Already registered?" : "Need an account?"}{" "}
            <Link
              className="font-semibold text-emerald-800 hover:text-emerald-700"
              href={isRegister ? "/login" : "/register"}
            >
              {isRegister ? "Login" : "Register"}
            </Link>
          </p>
        </section>
      </div>
    </div>
  );
}
