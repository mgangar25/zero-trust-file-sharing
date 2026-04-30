const tokenStorageKey = "ztfs_access_token";
const emailStorageKey = "ztfs_user_email";
const userIdStorageKey = "ztfs_user_id";

export type AuthSession = {
  token: string;
  email: string | null;
  userId: string | null;
};

type JwtPayload = {
  sub?: string;
  exp?: number;
};

function hasBrowserStorage() {
  return typeof window !== "undefined" && Boolean(window.localStorage);
}

function decodeJwtPayload(token: string): JwtPayload | null {
  try {
    const [, payload] = token.split(".");
    if (!payload) {
      return null;
    }

    const normalizedPayload = payload.replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(window.atob(normalizedPayload)) as JwtPayload;
  } catch {
    return null;
  }
}

export function saveAuthSession(token: string, email: string, userId?: string) {
  if (!hasBrowserStorage()) {
    return;
  }

  const tokenUserId = userId || decodeJwtPayload(token)?.sub || "";

  /*
   * Local storage is acceptable for this local portfolio/dev frontend because
   * it keeps the setup simple while the backend API is still evolving.
   *
   * Production should move JWT storage to secure, SameSite, httpOnly cookies
   * set by the backend. That prevents JavaScript from reading the token if a
   * future XSS bug ever appears in the browser app.
   */
  window.localStorage.setItem(tokenStorageKey, token);
  window.localStorage.setItem(emailStorageKey, email);

  if (tokenUserId) {
    window.localStorage.setItem(userIdStorageKey, tokenUserId);
  }
}

export function getAuthSession(): AuthSession | null {
  if (!hasBrowserStorage()) {
    return null;
  }

  const token = window.localStorage.getItem(tokenStorageKey);
  if (!token) {
    return null;
  }

  return {
    token,
    email: window.localStorage.getItem(emailStorageKey),
    userId:
      window.localStorage.getItem(userIdStorageKey) ||
      decodeJwtPayload(token)?.sub ||
      null,
  };
}

export function clearAuthSession() {
  if (!hasBrowserStorage()) {
    return;
  }

  window.localStorage.removeItem(tokenStorageKey);
  window.localStorage.removeItem(emailStorageKey);
  window.localStorage.removeItem(userIdStorageKey);
}
