"""QRU Portability Center™ — documentation-only export/backup/redeploy reference.

Reports live facts (collections, config presence WITHOUT secret values, version) plus
static checklists and command templates. This page exists so QRU can always be recovered.
"""
import os

from fastapi import APIRouter, Depends

from auth import get_current_user
from database import db
from ai_service import MODEL

router = APIRouter(prefix="/api/portability", tags=["portability-center"])


def _backend_url():
    """The public backend URL lives in the frontend env; read it for documentation."""
    val = os.environ.get("REACT_APP_BACKEND_URL")
    if val:
        return val
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return "not set"

VERSION = {"app": "QRU Factory™ Enterprise OS", "release": "1.0", "stack": "React + FastAPI + MongoDB"}

ENV_VARS = [
    {"key": "MONGO_URL", "purpose": "MongoDB connection string", "location": "backend/.env", "secret": True},
    {"key": "DB_NAME", "purpose": "Database name", "location": "backend/.env", "secret": False},
    {"key": "EMERGENT_LLM_KEY", "purpose": "Universal LLM key (text/image/TTS) — Emergent-managed", "location": "backend/.env", "secret": True},
    {"key": "STRIPE_API_KEY", "purpose": "Stripe payments (server-side)", "location": "backend/.env", "secret": True},
    {"key": "REACT_APP_BACKEND_URL", "purpose": "Public backend base URL used by the frontend", "location": "frontend/.env", "secret": False},
]

THIRD_PARTY = [
    {"name": "MongoDB", "role": "Primary datastore", "portable": "Yes — mongodump/mongorestore. Use MongoDB Atlas off-platform."},
    {"name": "Emergent Universal LLM Key", "role": "OpenAI/Gemini text, image, TTS", "portable": "Replace with your own OpenAI/Gemini/Anthropic API keys when self-hosting."},
    {"name": "Stripe", "role": "Payments & checkout", "portable": "Yes — bring your own Stripe account keys."},
]

DEPLOYMENT_TARGETS = [
    {"target": "Emergent (current)", "notes": "Managed hosting — 50 credits/month per deployed app."},
    {"target": "Vercel + Railway", "notes": "Frontend on Vercel, FastAPI backend on Railway, MongoDB Atlas."},
    {"target": "AWS / DigitalOcean", "notes": "Containers or VMs for backend, static host/CDN for frontend, Atlas or self-managed Mongo."},
    {"target": "Any React + FastAPI host", "notes": "Standard stack — no proprietary runtime required."},
]

BACKUP_CHECKLIST = [
    "Run 'Save to GitHub' to push the latest source code (frontend + backend + prompts + assets).",
    "Export MongoDB with mongodump (full binary backup of all collections).",
    "Record all environment variables from backend/.env and frontend/.env (values stored securely).",
    "Note your custom domain / backend URL and DNS records.",
    "Confirm Stripe keys and webhook endpoints are documented in your Stripe dashboard.",
    "Store backups in at least two locations (e.g., GitHub + cloud object storage).",
]

DISASTER_RECOVERY_CHECKLIST = [
    "Clone the GitHub repository to a new environment.",
    "Recreate backend/.env and frontend/.env from your secure env-var record.",
    "Provision MongoDB (Atlas or self-hosted) and set MONGO_URL + DB_NAME.",
    "Restore data with mongorestore from your latest dump.",
    "Install deps (backend: pip install -r requirements.txt; frontend: yarn install).",
    "Start services (backend on :8001, frontend on :3000) and verify /api/health.",
    "Point REACT_APP_BACKEND_URL at the new backend and re-test login + a manufacturing run.",
]

RESTORE_PROCEDURE = [
    {"step": "1. Get the code", "cmd": "git clone <your-qru-repo-url> qru-factory && cd qru-factory"},
    {"step": "2. Backend env", "cmd": "cp backend/.env.example backend/.env   # then fill MONGO_URL, DB_NAME, EMERGENT_LLM_KEY, STRIPE_API_KEY"},
    {"step": "3. Install backend", "cmd": "cd backend && pip install -r requirements.txt"},
    {"step": "4. Restore database", "cmd": "mongorestore --uri=\"$MONGO_URL\" --db=\"$DB_NAME\" ./dump/$DB_NAME"},
    {"step": "5. Install frontend", "cmd": "cd frontend && yarn install && yarn build"},
    {"step": "6. Run", "cmd": "sudo supervisorctl restart backend frontend   # or your host's process manager"},
]

COMMAND_TEMPLATES = [
    {"label": "Backup: full database dump", "cmd": "mongodump --uri=\"$MONGO_URL\" --db=\"$DB_NAME\" --out=./qru-backup-$(date +%F)"},
    {"label": "Backup: single collection (JSON)", "cmd": "mongoexport --uri=\"$MONGO_URL\" --db=\"$DB_NAME\" --collection=products --out=products.json"},
    {"label": "Restore: full database", "cmd": "mongorestore --uri=\"$MONGO_URL\" --db=\"$DB_NAME\" ./qru-backup-<date>/$DB_NAME"},
    {"label": "Restore: single collection (JSON)", "cmd": "mongoimport --uri=\"$MONGO_URL\" --db=\"$DB_NAME\" --collection=products --file=products.json"},
]


@router.get("/overview")
async def overview(user=Depends(get_current_user)):
    # Live MongoDB collections + counts (no document contents exposed).
    names = sorted(await db.list_collection_names())
    collections = []
    for n in names:
        try:
            collections.append({"name": n, "documents": await db[n].estimated_document_count()})
        except Exception:
            collections.append({"name": n, "documents": None})

    # Env / API-key presence ONLY — never the values.
    env_status = []
    for e in ENV_VARS:
        present = bool(os.environ.get(e["key"]))
        if e["key"] == "REACT_APP_BACKEND_URL":
            present = _backend_url() != "not set"
        env_status.append({**e, "configured": present, "masked": "•••• set" if present else "not set"})

    return {
        "version": VERSION,
        "github": {
            "status": "Use the 'Save to GitHub' feature in the chat input to push the full codebase.",
            "includes": ["Frontend (React)", "Backend (FastAPI + all subsystems)", "Prompts (in code)", "Static assets", "Config files"],
            "last_export_date": "Tracked in your GitHub repository commit history.",
        },
        "mongo_collections": {"count": len(collections), "collections": collections,
                              "note": "Schema is defined in code (Pydantic models + routers) and travels with the source export."},
        "environment_variables": env_status,
        "api_keys_checklist": [{"key": e["key"], "configured": e["configured"], "purpose": e["purpose"]} for e in env_status if e["secret"]],
        "deployment_targets": DEPLOYMENT_TARGETS,
        "llm_provider": {
            "current_provider": MODEL[0], "current_model": MODEL[1],
            "note": "Runs on the Emergent Universal LLM Key. When self-hosting, replace with your own OpenAI/Gemini/Anthropic keys and update ai_service.py.",
            "capabilities": ["Text generation", "Image generation (Nano Banana / GPT Image)", "OpenAI TTS"],
        },
        "backup_checklist": BACKUP_CHECKLIST,
        "disaster_recovery_checklist": DISASTER_RECOVERY_CHECKLIST,
        "restore_procedure": RESTORE_PROCEDURE,
        "command_templates": COMMAND_TEMPLATES,
        "domain": {"backend_url": _backend_url(),
                   "note": "Set REACT_APP_BACKEND_URL to your new public backend URL after redeploying."},
        "third_party_services": THIRD_PARTY,
    }
