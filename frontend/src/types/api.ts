export type UserResponse = {
  id: string;
  email: string;
  created_at: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: "bearer" | string;
};

export type FileRecord = {
  id: string;
  owner_id: string;
  original_filename: string;
  file_size: number;
  mime_type: string | null;
  created_at: string;
  deleted_at: string | null;
};

export type CreateShareLinkInput = {
  file_id: string;
  expires_in_minutes: number;
  max_downloads?: number;
  password?: string;
};

export type ShareLink = {
  id: string;
  file_id: string;
  owner_id: string;
  expires_at: string | null;
  max_downloads: number | null;
  download_count: number;
  is_revoked: boolean;
  created_at: string;
};

export type CreatedShareLink = ShareLink & {
  raw_token: string;
  share_url: string;
};

export type AuditLog = {
  id: string;
  share_link_id: string | null;
  file_id: string | null;
  event_type: string;
  status: "success" | "failure" | string;
  reason: string | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
};

export type DownloadResult = {
  blob: Blob;
  filename: string;
};
