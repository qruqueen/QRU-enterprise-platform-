import api from "@/lib/api";

const BACKEND = process.env.REACT_APP_BACKEND_URL;

// Mint a signed, short-lived token scoped to the exact file + action, then return an absolute URL.
export async function mintFileToken(productId, format, action) {
  const { data } = await api.post(`/products/${productId}/file-token`, { format, action });
  return { ...data, absUrl: `${BACKEND}${data.url}` };
}

// Explicit DOWNLOAD (Content-Disposition: attachment). Separate from preview.
export async function downloadDeliverable(productId, format = "pdf") {
  const t = await mintFileToken(productId, format, "download");
  const a = document.createElement("a");
  a.href = t.absUrl;
  a.rel = "noreferrer";
  document.body.appendChild(a);
  a.click();
  a.remove();
  return t;
}

// Open a preview in a NEW TAB (inline). Never downloads.
export async function openPreviewNewTab(productId, format = "pdf") {
  const t = await mintFileToken(productId, format, "preview");
  window.open(t.absUrl, "_blank", "noopener,noreferrer");
  return t;
}

// For Factory tools that hold a RAW asset URL: if it targets a protected deliverable-* file,
// mint a scoped token (by file id) and return the tokenized absolute URL; otherwise return as-is.
export async function tokenizeIfProtected(rawUrl, action = "preview") {
  const abs = rawUrl?.startsWith("http") ? rawUrl : `${BACKEND}${rawUrl}`;
  if (!rawUrl || !rawUrl.includes("/api/rendering/asset/deliverable-")) return abs;
  const fid = rawUrl.split("/api/rendering/asset/")[1].split("?")[0];
  const { data } = await api.post(`/products/file-token-by-fid`, { fid, action });
  return `${BACKEND}${data.url}`;
}

export async function downloadByFid(rawUrl) {
  let url = await tokenizeIfProtected(rawUrl, "download");
  // Non-protected public files: keep explicit attachment behavior via ?download=1.
  if (!rawUrl?.includes("/api/rendering/asset/deliverable-") && !url.includes("download=1")) {
    url += (url.includes("?") ? "&" : "?") + "download=1";
  }
  const a = document.createElement("a");
  a.href = url; a.rel = "noreferrer";
  document.body.appendChild(a); a.click(); a.remove();
}
