import { ApiError } from "@/lib/api";

export function getFriendlyErrorMessage(error: unknown, fallback: string) {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return "Your session is invalid or expired. Please log in again.";
    }

    if (error.status === 403) {
      return "This action is not allowed for the current account or link state.";
    }

    if (error.status === 404) {
      return "The requested file or share link could not be found.";
    }

    return error.message || fallback;
  }

  if (error instanceof TypeError) {
    /*
     * Browser fetch usually throws TypeError when the API is unreachable, CORS
     * blocks the request, or the backend is not running. Showing that directly
     * is noisy, so the UI points the developer at the likely local-dev fix.
     */
    return "Could not reach the backend. Make sure FastAPI is running on http://localhost:8000.";
  }

  return error instanceof Error ? error.message : fallback;
}
