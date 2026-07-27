"""Founder Production Operations™ — governed migration endpoints (Founder/Admin only).

DRY-RUN by default everywhere. Writes require an explicit apply flag AND run only against
whatever database this backend is connected to — i.e. PRODUCTION when triggered on the
deployed site. Reuses the exact idempotent logic in prod_migrations.py.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth import require_super_admin
import prod_migrations as pm

router = APIRouter(prefix="/api/admin/migrations", tags=["production-operations"])


class BookCutoverInput(BaseModel):
    stage: str = "all"   # "1" | "2" | "all"
    apply: bool = False


class ApplyInput(BaseModel):
    apply: bool = False


class ContainmentInput(BaseModel):
    apply_hold: bool = False
    apply: bool = False


@router.get("/summary")
async def summary(user=Depends(require_super_admin)):
    return await pm.summary()


# ----- Workstream A -----
@router.post("/book-cutover")
async def book_cutover(body: BookCutoverInput, user=Depends(require_super_admin)):
    return await pm.book_cutover(stage=body.stage, apply=body.apply)


@router.post("/book-cutover/rollback")
async def book_cutover_rollback(body: ApplyInput, user=Depends(require_super_admin)):
    return await pm.book_cutover_rollback(apply=body.apply)


@router.get("/book-cutover/inspect")
async def book_cutover_inspect(user=Depends(require_super_admin)):
    """Read-only comparison of incoming vs existing records for the Stage-1 book_codes."""
    return await pm.inspect_book_conflicts()


@router.post("/book-cutover/resolve-conflicts")
async def book_cutover_resolve_conflicts(body: ApplyInput, user=Depends(require_super_admin)):
    """Governed adopt-and-repoint for ID_MISMATCH_SAME_BOOK records (dry-run by default)."""
    return await pm.resolve_book_conflicts(apply=body.apply)


@router.post("/book-cutover/create-fresh-code")
async def book_cutover_create_fresh(body: ApplyInput, user=Depends(require_super_admin)):
    """Create DIFFERENT_WORK migration books under a fresh production book_code (dry-run default)."""
    return await pm.create_under_fresh_code(apply=body.apply)


@router.post("/book-cutover/create-fresh-code/rollback")
async def book_cutover_create_fresh_rollback(body: ApplyInput, user=Depends(require_super_admin)):
    return await pm.create_under_fresh_code_rollback(apply=body.apply)


# ----- Workstream C -----
@router.post("/learn-containment")
async def learn_containment(body: ContainmentInput, user=Depends(require_super_admin)):
    return await pm.learn_containment(apply_hold=body.apply_hold, apply=body.apply)


@router.post("/learn-containment/rollback")
async def learn_containment_rollback(body: ApplyInput, user=Depends(require_super_admin)):
    return await pm.learn_containment_rollback(apply=body.apply)


# ----- DQ-7C Standards Metadata (independent governed operation) -----
@router.get("/standards-metadata/preflight")
async def standards_metadata_preflight(user=Depends(require_super_admin)):
    return await pm.standards_metadata_preflight()


@router.post("/standards-metadata/apply")
async def standards_metadata_apply(body: ApplyInput, user=Depends(require_super_admin)):
    return await pm.standards_metadata_apply(apply=body.apply)


@router.post("/standards-metadata/rollback")
async def standards_metadata_rollback(body: ApplyInput, user=Depends(require_super_admin)):
    return await pm.standards_metadata_rollback(apply=body.apply)
