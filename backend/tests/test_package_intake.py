import hashlib
import io
import json
import zipfile

import pytest

from package_intake import PackageIntakeError, parse_factory_package


def _json_bytes(value):
    return json.dumps(value, sort_keys=True, indent=2).encode("utf-8")


def make_package(*, approved=True, locked=False, metadata_locked=False,
                 extra_file=None, tamper_declared=False, traversal=False):
    product_key = "qru-financial-health-test-product"
    version = "1.0.0"
    files = {
        f"{product_key}-v{version}.pdf": b"%PDF-1.7\nQRU synthetic fixture\n%%EOF\n",
        f"{product_key}-v{version}.docx": b"PK\x03\x04synthetic-docx-fixture",
        f"{product_key}-cover-v{version}.png": b"\x89PNG\r\n\x1a\nsynthetic-cover",
        f"{product_key}-metadata-v{version}.json": _json_bytes({
            "title": "Test Product",
            "subtitle": "Synthetic Factory contract fixture",
            "publisher": "QRU Press(TM)",
            "series": "QRU Financial Health(TM)",
            "product_key": product_key,
            "version": version,
            "category": "Financial Health > Test",
            "suggested_price_usd": 7.0,
            "status": "FOUNDER REVIEW",
            "publisher_handoff": (
                "LOCKED pending Founder approval" if metadata_locked
                else "READY FOR PUBLISHER"
            ),
            "tags": ["test", "factory package"],
        }),
        "evidence-note.txt": b"Synthetic evidence note used only by tests.\n",
        "approval-record.json": _json_bytes({
            "product_key": product_key,
            "version": version,
            "founder_approval": "APPROVED" if approved else "PENDING",
            "status": "FOUNDER APPROVED" if approved else "PENDING FOUNDER REVIEW",
            "publisher_handoff": "LOCKED" if locked else "READY FOR PUBLISHER",
        }),
    }
    manifest = {
        "product_key": product_key,
        "version": version,
        "files": [
            {"filename": name, "sha256": hashlib.sha256(data).hexdigest()}
            for name, data in files.items()
        ],
        "publisher_handoff": (
            "LOCKED pending Founder approval" if locked else "READY FOR PUBLISHER"
        ),
    }
    manifest_name = f"{product_key}-manifest-v{version}.json"

    if tamper_declared:
        pdf_name = next(name for name in files if name.endswith(".pdf"))
        files[pdf_name] += b"tampered-after-manifest"

    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in files.items():
            zf.writestr(name, data)
        zf.writestr(manifest_name, _json_bytes(manifest))
        if extra_file:
            zf.writestr(extra_file, b"undeclared")
        if traversal:
            zf.writestr("../escape.txt", b"unsafe")
    return out.getvalue(), product_key, version


def test_pending_factory_package_is_blocked():
    blob, _, _ = make_package(approved=False, locked=True)
    with pytest.raises(PackageIntakeError) as exc:
        parse_factory_package(blob, trace_id="t1")
    assert exc.value.code == "FOUNDER_APPROVAL_REQUIRED"
    assert exc.value.stage == "approval_gate"


def test_approved_factory_contract_passes_and_identity_is_stable():
    blob, key, version = make_package(approved=True, locked=False)
    parsed = parse_factory_package(blob, trace_id="t2")
    assert parsed.product_key == key
    assert parsed.version == version
    assert len(parsed.archive_sha256) == 64
    assert parsed.idempotency_key == f"{key}:{version}:{parsed.archive_sha256}"
    assert parsed.metadata["title"] == "Test Product"


def test_locked_handoff_blocks_even_when_approval_says_approved():
    blob, _, _ = make_package(approved=True, locked=True)
    with pytest.raises(PackageIntakeError) as exc:
        parse_factory_package(blob, trace_id="t3")
    assert exc.value.code == "PUBLISHER_HANDOFF_LOCKED"


def test_stale_metadata_lock_does_not_override_approved_control_records():
    blob, _, _ = make_package(approved=True, locked=False, metadata_locked=True)
    parsed = parse_factory_package(blob, trace_id="t-meta")
    assert parsed.approval["founder_approval"] == "APPROVED"
    assert parsed.manifest["publisher_handoff"] == "READY FOR PUBLISHER"


def test_checksum_tamper_is_rejected():
    blob, _, _ = make_package(approved=True, locked=False, tamper_declared=True)
    with pytest.raises(PackageIntakeError) as exc:
        parse_factory_package(blob, trace_id="t4")
    assert exc.value.code == "CHECKSUM_MISMATCH"


def test_path_traversal_is_rejected():
    blob, _, _ = make_package(approved=True, locked=False, traversal=True)
    with pytest.raises(PackageIntakeError) as exc:
        parse_factory_package(blob, trace_id="t5")
    assert exc.value.code == "UNSAFE_ARCHIVE_PATH"


def test_undeclared_file_is_rejected():
    blob, _, _ = make_package(approved=True, locked=False, extra_file="surprise.txt")
    with pytest.raises(PackageIntakeError) as exc:
        parse_factory_package(blob, trace_id="t6")
    assert exc.value.code == "UNDECLARED_ARCHIVE_FILE"


def test_invalid_zip_has_structured_error():
    with pytest.raises(PackageIntakeError) as exc:
        parse_factory_package(b"not a zip", trace_id="trace-xyz")
    assert exc.value.as_dict() == {
        "ok": False,
        "code": "INVALID_ZIP",
        "stage": "archive_open",
        "trace_id": "trace-xyz",
        "message": "Package is not a valid ZIP archive.",
    }
