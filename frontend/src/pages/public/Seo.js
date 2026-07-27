import { useEffect } from "react";

const DEFAULT_DESC =
  "QRU Press™ is a premium educational publishing house. Every title is carefully researched, thoughtfully written, and verified to the Treasure Standard™.";

function setMeta(key, content, attr = "name") {
  if (content == null) return;
  let el = document.head.querySelector(`meta[${attr}="${key}"]`);
  if (!el) {
    el = document.createElement("meta");
    el.setAttribute(attr, key);
    document.head.appendChild(el);
  }
  el.setAttribute("content", content);
}

function setCanonical(url) {
  if (!url) return;
  let el = document.head.querySelector('link[rel="canonical"]');
  if (!el) {
    el = document.createElement("link");
    el.setAttribute("rel", "canonical");
    document.head.appendChild(el);
  }
  el.setAttribute("href", url);
}

// Lightweight, dependency-free SEO/meta manager for the public storefront.
export default function Seo({ title, description, image, path }) {
  const desc = description || DEFAULT_DESC;
  const url = typeof window !== "undefined"
    ? `${window.location.origin}${path ?? window.location.pathname}`
    : undefined;
  useEffect(() => {
    if (title) document.title = title;
    setMeta("description", desc);
    setMeta("og:title", title, "property");
    setMeta("og:description", desc, "property");
    setMeta("og:type", "website", "property");
    setMeta("og:site_name", "QRU Press™", "property");
    if (url) setMeta("og:url", url, "property");
    if (image) setMeta("og:image", image, "property");
    setMeta("twitter:card", image ? "summary_large_image" : "summary");
    setMeta("twitter:title", title);
    setMeta("twitter:description", desc);
    if (image) setMeta("twitter:image", image);
    setCanonical(url);
  }, [title, desc, image, url]);
  return null;
}
