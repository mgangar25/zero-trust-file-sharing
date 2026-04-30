import type {
  AuditLog,
  CreatedShareLink,
  CreateShareLinkInput,
  DownloadResult,
  FileRecord,
  ShareLink,
  TokenResponse,
  UserResponse,
} from "@/types/api";

const fallbackApiUrl = "http://localhost:8000";

// NEXT_PUBLIC_API_URL is intentionally public because browsers need to know
// which backend origin to call. It must never contain database keys, R2 keys, or
// any other secret value.
export const apiBaseUrl = (
  process.env.NEXT_PUBLIC_API_URL || fallbackApiUrl
).replace(/\/$/, "");

type ApiJsonOptions = {
  method?: "GET" | "POST" | "DELETE" | "PATCH" | "PUT";
  token?: string;
  body?: unknown;
  headers?: HeadersInit;
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function buildHeaders(options: ApiJsonOptions): HeadersInit {
  const headers = new Headers(options.headers);

  if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }

  if (options.token) {
    headers.set("Authorization", `Bearer ${options.token}`);
  }

  return headers;
}

async function getErrorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };

    if (typeof body.detail === "string") {
      return body.detail;
    }

    if (Array.isArray(body.detail)) {
      return body.detail
        .map((item) =>
          typeof item === "object" && item !== null && "msg" in item
            ? String(item.msg)
            : "Invalid request",
        )
        .join(", ");
    }
  } catch {
    // If the backend returned a non-JSON error, the HTTP status is still useful.
  }

  return `Request failed with status ${response.status}.`;
}

export async function apiJson<T>(
  path: string,
  options: ApiJsonOptions = {},
): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: options.method || "GET",
    headers: buildHeaders(options),
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  if (!response.ok) {
    throw new ApiError(await getErrorMessage(response), response.status);
  }

  return (await response.json()) as T;
}

function getFilenameFromHeader(
  contentDisposition: string | null,
  fallbackName: string,
) {
  if (!contentDisposition) {
    return fallbackName;
  }

  const encodedMatch = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (encodedMatch?.[1]) {
    return decodeURIComponent(encodedMatch[1]);
  }

  const plainMatch = contentDisposition.match(/filename="?([^"]+)"?/i);
  return plainMatch?.[1] || fallbackName;
}

async function apiDownload(
  path: string,
  fallbackName: string,
  options: ApiJsonOptions = {},
): Promise<DownloadResult> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: options.method || "GET",
    headers: buildHeaders(options),
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  if (!response.ok) {
    throw new ApiError(await getErrorMessage(response), response.status);
  }

  return {
    blob: await response.blob(),
    filename: getFilenameFromHeader(
      response.headers.get("Content-Disposition"),
      fallbackName,
    ),
  };
}

export const authApi = {
  register(email: string, password: string) {
    return apiJson<UserResponse>("/auth/register", {
      method: "POST",
      body: { email, password },
    });
  },
  login(email: string, password: string) {
    return apiJson<TokenResponse>("/auth/login", {
      method: "POST",
      body: { email, password },
    });
  },
};

export const filesApi = {
  list(token: string) {
    return apiJson<FileRecord[]>("/files", { token });
  },
  async upload(token: string, file: File) {
    const formData = new FormData();
    formData.append("uploaded_file", file);

    const response = await fetch(`${apiBaseUrl}/files/upload`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      throw new ApiError(await getErrorMessage(response), response.status);
    }

    return (await response.json()) as FileRecord;
  },
  download(token: string, file: FileRecord) {
    return apiDownload(`/files/${file.id}/download`, file.original_filename, {
      token,
    });
  },
  delete(token: string, fileId: string) {
    return apiJson<{ message: string; file_id: string }>(`/files/${fileId}`, {
      method: "DELETE",
      token,
    });
  },
};

export const shareApi = {
  list(token: string) {
    return apiJson<ShareLink[]>("/share", { token });
  },
  create(token: string, input: CreateShareLinkInput) {
    return apiJson<CreatedShareLink>(`/share/files/${input.file_id}`, {
      method: "POST",
      token,
      body: {
        expires_in_minutes: input.expires_in_minutes,
        max_downloads: input.max_downloads,
        password: input.password || undefined,
      },
    });
  },
  revoke(token: string, shareId: string) {
    return apiJson<{ message: string; share_id: string }>(`/share/${shareId}`, {
      method: "DELETE",
      token,
    });
  },
  downloadPublic(token: string, password?: string) {
    return apiDownload(`/share/${token}/download`, "shared-file", {
      method: "POST",
      body: { password: password || undefined },
    });
  },
};

export const auditApi = {
  list(token: string) {
    return apiJson<AuditLog[]>("/audit", { token });
  },
};
