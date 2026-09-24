"""Authenticated Publisher Lite bridge and QRU asset endpoints."""
import json
import os
import secrets

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from fastapi.responses import JSONResponse, Response

from database import db
from publisher_lite import MAX_ARCHIVE_BYTES, PublisherLiteError, publish_release
import storage

router = APIRouter(prefix="/api/publisher-lite", tags=["publisher-lite"])


def require_bridge_token(authorization: str | None = Header(default=None)):
    expected = os.environ.get("PUBLISHER_BRIDGE_TOKEN")
    supplied = authorization.removeprefix("Bearer ").strip() if authorization else ""
    if not expected or not supplied or not secrets.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Publisher bridge authentication required.")


@router.post("/publish", dependencies=[Depends(require_bridge_token)])
async def publish(record: UploadFile = File(...), package: UploadFile = File(...)):
    try:
        raw_record = await record.read(2 * 1024 * 1024 + 1)
        if len(raw_record) > 2 * 1024 * 1024:
            raise PublisherLiteError("RECORD_TOO_LARGE", "receive", "Publisher Lite record exceeds 2 MB.", status=413)
        try:
            value = json.loads(raw_record.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PublisherLiteError("INVALID_RECORD_JSON", "receive", "Publisher Lite record is not valid JSON.") from exc
        package_bytes = await package.read(MAX_ARCHIVE_BYTES + 1)
        return await publish_release(value, package_bytes)
    except PublisherLiteError as exc:
        return JSONResponse(status_code=exc.status, content=exc.as_dict())
    finally:
        await record.close()
        await package.close()


@router.get("/receipts/{receipt_id}", dependencies=[Depends(require_bridge_token)])
async def receipt(receipt_id: str):
    value = await db.publisher_lite_receipts.find_one({"_id": receipt_id}, {"_id": 0})
    if not value:
        raise HTTPException(status_code=404, detail="Publish receipt not found.")
    return value


@router.get("/queue", dependencies=[Depends(require_bridge_token)])
async def queue():
    values = await db.publisher_lite_queue.find({}, {"_id": 0}).sort("updated_at", -1).to_list(200)
    return {"items": values, "count": len(values)}


async def _asset(product_id: str, role: str):
    product = await db.products.find_one({"id": product_id, "status": "Published"}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    if role == "cover":
        asset = product.get("cover_asset")
    else:
        files = (product.get("customer_deliverable") or {}).get("files") or []
        asset = files[0] if files else None
    if not asset or not asset.get("storage_path"):
        raise HTTPException(status_code=404, detail="Asset not found.")
    body = await storage.aget_object(asset["storage_path"])
    return Response(content=body, media_type=asset.get("media_type") or "application/octet-stream")


@router.get("/products/{product_id}/cover")
async def cover(product_id: str):
    return await _asset(product_id, "cover")


@router.get("/products/{product_id}/download", dependencies=[Depends(require_bridge_token)])
async def download(product_id: str):
    # The existing paid-order service calls this only after its proven payment check.
    return await _asset(product_id, "customer")
