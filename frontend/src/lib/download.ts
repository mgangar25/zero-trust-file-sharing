import type { DownloadResult } from "@/types/api";

export function saveBlobToDisk({ blob, filename }: DownloadResult) {
  const objectUrl = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");

  anchor.href = objectUrl;
  anchor.download = filename;
  anchor.click();

  window.URL.revokeObjectURL(objectUrl);
}
