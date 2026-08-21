"""Authenticated API surface for QRU Factory package intake."""
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse

from auth import require_super_admin
from package_intake import MAX_ARCHIVE_BYTES, PackageIntakeError, ingest_factory_package, new_trace_id

router = APIRouter(prefix="/api/package-intake", tags=["package-intake"])


@router.post("/ingest")
async def ingest_package(file: UploadFile = File(...), user=Depends(require_super_admin)):
    """Validate and stage an approved Factory ZIP. Never publishes to a storefront."""
    trace_id = new_trace_id()
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
        return await ingest_factory_package(body, actor=user.get("name", "Founder"), trace_id=trace_id)
    except PackageIntakeError as exc:
        return JSONResponse(status_code=exc.http_status, content=exc.as_dict())
    finally:
        await file.close()
