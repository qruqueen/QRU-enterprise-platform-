"""QRU Universal Distribution Framework™ — Connector implementations + registry (MO-007).

Real connectors: QRU Store™ (native), YouTube (external, via Data API). Additional channels are
registered as honest NEEDS_SETUP stubs so the SDK/registry is fully extensible — each future
platform only implements the same Connector interface.
"""
import os
import httpx

from database import db
from models import now_iso
from oauth_framework import _enc, _dec
from .sdk import (Connector, ConnectorCapability, DistributionResult,
                  ConnectorKind, DistMode, DistStatus)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "rendered_assets", "uploads")


async def save_connector_credentials(connector_id, creds: dict, secret_fields=("app_password",)):
    """Persist per-connector credentials, encrypting secret fields at rest (Fernet)."""
    stored = {}
    for k, v in (creds or {}).items():
        stored[k + "_enc" if k in secret_fields else k] = _enc(v) if k in secret_fields else v
    stored["updated_at"] = now_iso()
    await db.connector_credentials.update_one({"connector_id": connector_id},
                                              {"$set": {**stored, "connector_id": connector_id}}, upsert=True)
    return True


async def get_connector_credentials(connector_id, secret_fields=("app_password",)):
    doc = await db.connector_credentials.find_one({"connector_id": connector_id})
    if not doc:
        return None
    out = {}
    for k, v in doc.items():
        if k in ("_id", "connector_id", "updated_at"):
            continue
        if k.endswith("_enc"):
            out[k[:-4]] = _dec(v)
        else:
            out[k] = v
    return out


# ------------------------------------------------------------------ QRU STORE
class QRUStoreConnector(Connector):
    capability = ConnectorCapability(
        id="qru_store", name="QRU Store™", kind=ConnectorKind.DELIVER.value, category="Store",
        native=True, modes=[DistMode.PUBLIC.value, DistMode.DRAFT.value],
        asset_types=["listing"], requires_file=False, analytics_supported=True)

    async def connection_status(self):
        return {"connected": True, "account": "QRU Store™ (native)", "can_distribute": True, "reason": None}

    async def distribute(self, product, meta, mode, options):
        pid = product["id"]
        status = "Published" if mode == DistMode.PUBLIC.value else "Draft"
        await db.products.update_one({"id": pid}, {"$set": {
            "status": status, "store_listed": status == "Published",
            "listed_at": now_iso(), "updated_at": now_iso()}})
        if status != "Published":
            return DistributionResult(ok=True, status=DistStatus.DRAFT.value, external_id=pid,
                                      detail="Saved as store draft (not yet purchasable).")
        return DistributionResult(ok=True, status=DistStatus.DELIVERED.value, external_id=pid,
                                  url=f"/store?product={pid}", verified=True,
                                  detail="Listed in QRU Store™ and purchasable via Stripe.")

    async def verify(self, external_id, options):
        p = await db.products.find_one({"id": external_id})
        live = bool(p and p.get("status") == "Published")
        return DistributionResult(ok=live, status=DistStatus.DELIVERED.value if live else DistStatus.FAILED.value,
                                  external_id=external_id, verified=live,
                                  url=f"/store?product={external_id}",
                                  detail="Live in QRU Store™." if live else "Not currently published in the store.")

    async def fetch_analytics(self, external_id, options):
        purchases = await db.purchases.count_documents({"product_id": external_id})
        txns = await db.payment_transactions.find({"metadata.product_id": external_id, "payment_status": "paid"}).to_list(500)
        revenue = sum((t.get("amount_total") or 0) / 100 for t in txns)
        return {"supported": True, "provenance": "LIVE" if purchases else "TEST",
                "metrics": {"purchases": purchases, "revenue_usd": round(revenue, 2)}}


# ------------------------------------------------------------------ YOUTUBE
class YouTubeConnector(Connector):
    capability = ConnectorCapability(
        id="youtube", name="YouTube", kind=ConnectorKind.PUBLISH.value, category="Video",
        native=False, modes=[DistMode.PRIVATE.value, DistMode.UNLISTED.value, DistMode.PUBLIC.value],
        asset_types=["video"], requires_file=True, analytics_supported=True)

    async def connection_status(self):
        import youtube_publisher as yt
        state = await db.connectors.find_one({"platform_id": "youtube"}) or {}
        connected = bool(state.get("access_token_enc")) and state.get("connected")
        return {"connected": bool(connected), "account": state.get("account"),
                "can_distribute": bool(connected),
                "reason": None if connected else "Connect YouTube in Publishing Connectors™ first."}

    def map_metadata(self, product, overrides):
        meta = super().map_metadata(product, overrides)
        meta["tags"] = (meta.get("tags") or [])[:15]
        meta["description"] = (meta.get("description") or "") + "\n\n— Manufactured by QRU Factory™."
        return meta

    async def distribute(self, product, meta, mode, options):
        import youtube_publisher as yt
        upload_id = (options or {}).get("video_upload_id")
        if not upload_id:
            return DistributionResult(ok=False, status=DistStatus.NEEDS_SETUP.value,
                                      detail="YouTube requires a video file. Upload the MP4 in YouTube Publisher™, or attach a rendered video asset.")
        path = os.path.join(UPLOAD_DIR, os.path.basename(upload_id))
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return DistributionResult(ok=False, status=DistStatus.FAILED.value, detail="Uploaded video file not found.")
        thumb = (options or {}).get("thumbnail_upload_id")
        thumb_path = os.path.join(UPLOAD_DIR, os.path.basename(thumb)) if thumb else None
        try:
            pub = await yt.publish_video(
                file_path=path, title=meta["title"], description=meta.get("description", ""),
                tags=meta.get("tags", []), privacy=mode if mode in ("private", "unlisted", "public") else "private",
                thumbnail_path=thumb_path if thumb_path and os.path.exists(thumb_path) else None,
                playlist_id=(options or {}).get("playlist_id"), product_id=product["id"], actor=(options or {}).get("actor", "Founder"))
        except yt.YouTubeError as e:
            return DistributionResult(ok=False, status=DistStatus.FAILED.value, detail=str(e))
        finally:
            for p in (path, thumb_path):
                try:
                    if p and os.path.exists(p):
                        os.remove(p)
                except Exception:
                    pass
        st = DistStatus.PUBLISHED.value
        return DistributionResult(ok=True, status=st, external_id=pub["video_id"], url=pub["url"],
                                  verified=True, detail=f"Uploaded to YouTube ({pub['privacy']}).",
                                  extra={"studio_url": pub["studio_url"], "privacy": pub["privacy"]})

    async def verify(self, external_id, options):
        import youtube_publisher as yt
        try:
            v = await yt.verify_video(external_id)
        except yt.YouTubeError as e:
            return DistributionResult(ok=False, status=DistStatus.FAILED.value, external_id=external_id, detail=str(e))
        if not v.get("exists"):
            return DistributionResult(ok=False, status=DistStatus.FAILED.value, external_id=external_id,
                                      detail="Video not found on YouTube.")
        return DistributionResult(ok=True, status=DistStatus.PUBLISHED.value, external_id=external_id,
                                  url=v["url"], verified=True, detail=f"Confirmed live on YouTube ({v.get('privacy')}).")

    async def fetch_analytics(self, external_id, options):
        import youtube_publisher as yt
        try:
            s = await yt.video_stats(external_id)
            return {"supported": True, "provenance": "LIVE", "metrics": s}
        except yt.YouTubeError as e:
            return {"supported": True, "provenance": "NOT_TRACKED", "note": str(e)}


# ------------------------------------------------------------------ WORDPRESS (real)
class WordPressConnector(Connector):
    capability = ConnectorCapability(
        id="wordpress", name="WordPress / Blog", kind=ConnectorKind.PUBLISH.value, category="Blog",
        native=False, modes=[DistMode.DRAFT.value, DistMode.PUBLIC.value],
        asset_types=["article"], requires_file=False, analytics_supported=False)

    async def _creds(self):
        return await get_connector_credentials("wordpress")

    def _base(self, c):
        return c["site_url"].rstrip("/") + "/wp-json/wp/v2"

    def _auth(self, c):
        return httpx.BasicAuth(c["username"], c["app_password"])

    async def connection_status(self):
        c = await self._creds()
        if not c or not c.get("site_url"):
            return {"connected": False, "account": None, "can_distribute": False,
                    "reason": "Add your WordPress site URL, username and Application Password (Developer Setup)."}
        try:
            async with httpx.AsyncClient(auth=self._auth(c), timeout=20) as client:
                r = await client.get(f"{self._base(c)}/users/me", params={"context": "edit"})
            if r.status_code < 400:
                return {"connected": True, "account": f"{r.json().get('name')} · {c['site_url']}", "can_distribute": True, "reason": None}
            return {"connected": False, "account": c["site_url"], "can_distribute": False,
                    "reason": f"WordPress auth failed ({r.status_code}). Check the Application Password."}
        except Exception as e:
            return {"connected": False, "account": c.get("site_url"), "can_distribute": False, "reason": f"Could not reach the site: {str(e)[:80]}"}

    def map_metadata(self, product, overrides):
        meta = super().map_metadata(product, overrides)
        content = product.get("content") or product.get("summary") or ""
        # Preserve line breaks as HTML paragraphs.
        meta["content_html"] = "".join(f"<p>{p.strip()}</p>" for p in content.split("\n\n") if p.strip()) or f"<p>{content}</p>"
        return meta

    async def distribute(self, product, meta, mode, options):
        c = await self._creds()
        if not c:
            return DistributionResult(ok=False, status=DistStatus.NEEDS_SETUP.value, detail="WordPress is not configured yet.")
        status = "publish" if mode == DistMode.PUBLIC.value else "draft"
        payload = {"title": meta["title"], "content": meta.get("content_html") or meta.get("description", ""), "status": status}
        try:
            async with httpx.AsyncClient(auth=self._auth(c), timeout=45) as client:
                r = await client.post(f"{self._base(c)}/posts", json=payload)
        except Exception as e:
            return DistributionResult(ok=False, status=DistStatus.FAILED.value, detail=f"WordPress request failed: {str(e)[:120]}")
        if r.status_code >= 400:
            return DistributionResult(ok=False, status=DistStatus.FAILED.value, detail=f"WordPress rejected the post ({r.status_code}): {r.text[:150]}")
        post = r.json()
        st = DistStatus.PUBLISHED.value if status == "publish" else DistStatus.DRAFT.value
        return DistributionResult(ok=True, status=st, external_id=str(post["id"]), url=post.get("link"),
                                  verified=status == "publish", detail=f"WordPress post {post['id']} ({status}).")

    async def verify(self, external_id, options):
        c = await self._creds()
        if not c:
            return DistributionResult(ok=False, status=DistStatus.FAILED.value, external_id=external_id, detail="WordPress not configured.")
        try:
            async with httpx.AsyncClient(auth=self._auth(c), timeout=20) as client:
                r = await client.get(f"{self._base(c)}/posts/{external_id}")
            if r.status_code < 400:
                p = r.json()
                return DistributionResult(ok=True, status=DistStatus.PUBLISHED.value, external_id=external_id,
                                          url=p.get("link"), verified=p.get("status") == "publish",
                                          detail=f"Confirmed on WordPress (status: {p.get('status')}).")
        except Exception as e:
            return DistributionResult(ok=False, status=DistStatus.FAILED.value, external_id=external_id, detail=str(e)[:120])
        return DistributionResult(ok=False, status=DistStatus.FAILED.value, external_id=external_id, detail="Post not found on WordPress.")


# ------------------------------------------------------------------ HONEST STUBS
class _StubConnector(Connector):
    def __init__(self, cap, hint):
        self.capability = cap
        self._hint = hint

    async def connection_status(self):
        return {"connected": False, "account": None, "can_distribute": False,
                "reason": f"Developer setup required — {self.capability.name} connector is a planned QRU Distribution Framework™ channel."}

    async def distribute(self, product, meta, mode, options):
        return DistributionResult(ok=False, status=DistStatus.NEEDS_SETUP.value, detail=self._hint)


def _stub(id, name, kind, category, native, modes, asset_types, hint, requires_file=False):
    return _StubConnector(ConnectorCapability(id=id, name=name, kind=kind.value, category=category,
                          native=native, modes=[m.value for m in modes], asset_types=asset_types,
                          requires_file=requires_file), hint)


# ------------------------------------------------------------------ REGISTRY
def _build_registry():
    connectors = [
        QRUStoreConnector(),
        YouTubeConnector(),
        WordPressConnector(),
        _stub("google_drive", "Google Drive", ConnectorKind.DELIVER, "Storage", False,
              [DistMode.PRIVATE, DistMode.PUBLIC], ["file"],
              "Google Drive delivery (upload file, return Document ID) is a planned connector.", requires_file=True),
        _stub("email", "Email Delivery", ConnectorKind.DELIVER, "Email", False,
              [DistMode.PUBLIC], ["file"],
              "Email delivery (send download links via Resend/SendGrid) is a planned connector."),
        _stub("etsy", "Etsy", ConnectorKind.PUBLISH, "Marketplace", False,
              [DistMode.DRAFT, DistMode.PUBLIC], ["listing", "image"],
              "Etsy listing publishing (return Listing ID) is a planned connector."),
        _stub("amazon_kdp", "Amazon KDP", ConnectorKind.PUBLISH, "Marketplace", False,
              [DistMode.DRAFT, DistMode.PUBLIC], ["epub", "pdf", "image"],
              "Amazon KDP publishing (return ASIN) is a planned connector.", requires_file=True),
    ]
    return {c.capability.id: c for c in connectors}


REGISTRY = _build_registry()


def get_connector(connector_id):
    return REGISTRY.get(connector_id)
