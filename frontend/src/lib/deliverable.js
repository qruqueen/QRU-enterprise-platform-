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
