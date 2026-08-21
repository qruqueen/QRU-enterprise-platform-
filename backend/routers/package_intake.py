"""Authenticated API surface for QRU Simple Publisher package intake."""
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse

from auth import require_super_admin
from package_intake import MAX_ARCHIVE_BYTES, PackageIntakeError, ingest_factory_package, new_trace_id
from product_publishing import publish_to_store

router = APIRouter(prefix="/api/package-intake", tags=["package-intake"])


@router.post("/ingest")
async def ingest_package(file: UploadFile = File(...), user=Depends(require_super_admin)):
    """Validate an approved QRU package, stage it idempotently, then publish it to the QRU Store."""
    trace_id = new_trace_id()
    actor = user.get("name", "Founder")
    try:
        body = await file.read(MAX_ARCHIVE_BYTES + 1)
        if len(body) > MAX_ARCHIVE_BYTES:
            raise PackageIntakeError(
                "PACKAGE_TOO_LARGE",
                "receive",
                "Package exceeds the 100 MB intake limit.",
                trace_id=trace_id,
                http_status=413,
            )

        result = await ingest_factory_package(body, actor=actor, trace_id=trace_id)
        publish_result = await publish_to_store(result["product_id"], actor=actor)

        if not publish_result or not publish_result.get("ok"):
            message = (publish_result or {}).get("message") or "Package was staged, but the QRU Store publish step did not complete."
            return JSONResponse(
                status_code=502,
                content={
                    "ok": False,
                    "code": "AUTO_PUBLISH_FAILED",
                    "stage": "store_publish",
                    "trace_id": trace_id,
                    "message": message,
                    "product_id": result.get("product_id"),
                    "product_key": result.get("product_key"),
                    "version": result.get("version"),
                    "archive_sha256": result.get("archive_sha256"),
                    "idempotent_replay": result.get("idempotent_replay", False),
                },
            )

        result.update(
            {
                "status": "Published",
                "published": True,
                "auto_published": True,
                "store_url": publish_result.get("store_url"),
            }
        )
        return result
    except PackageIntakeError as exc:
        return JSONResponse(status_code=exc.http_status, content=exc.as_dict())
    finally:
        await file.close()
