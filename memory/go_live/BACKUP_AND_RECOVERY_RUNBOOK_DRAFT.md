# QRU Online — Backup & Recovery Runbook (DRAFT — Founder review)

> Status: DRAFT ops runbook. Describes what to protect and how to recover. No live systems are
> changed by this document.

## 1. What must be protected (in priority order)
1. **MongoDB data** — the single source of truth: `knowledge_records`, `book_records`,
   `products`, and `book_purchases` (orders/fulfillment). Losing this loses knowledge + sales.
2. **Secrets** — `backend/.env` (Stripe keys, Mongo URL, webhook secret). Store a copy in a
   password manager / secure vault, NOT in git (now enforced via .gitignore).
3. **Canonical assets** — `/app/backend/rendered_assets/` (canonical covers + EPUBs). Under the
   Master Asset Principle™ these are masters; derivatives (thumbnails) can be regenerated.
4. **Code** — pushed to GitHub via Emergent "Save to GitHub".

## 2. Backup approach (recommended)
- **Database:** enable automated daily snapshots of MongoDB with point-in-time recovery.
  - If using MongoDB Atlas: turn on **Cloud Backups** (daily + PITR), retain [7–30] days.
  - If self-hosted: nightly `mongodump` to offsite storage (e.g. object storage bucket),
    retain [30] days. Command reference: `mongodump --uri "$MONGO_URL" --archive=qru-YYYYMMDD.gz --gzip`.
- **Assets:** back up `rendered_assets/` to durable object storage [weekly or on change].
- **Secrets:** store `.env` values in [1Password/Bitwarden/secrets manager]; document who has access.
- **Code:** push to GitHub after each meaningful change.

## 3. Recovery procedures
- **Restore database:**
  - Atlas: restore snapshot to a new cluster, update `MONGO_URL`, redeploy.
  - Self-hosted: `mongorestore --uri "$MONGO_URL" --archive=qru-YYYYMMDD.gz --gzip --drop`.
- **Restore assets:** copy the backed-up `rendered_assets/` back; regenerate thumbnails on demand
  (cover-thumb endpoint recreates them automatically).
- **Restore secrets:** recreate `backend/.env` from the vault; restart backend.
- **Rebuild app:** redeploy from GitHub; set env vars; verify `/api/public/home` and a test purchase.

## 4. Verification after recovery
- [ ] `/api/public/books` returns the expected authorized titles with covers
- [ ] A Stripe **test** purchase completes and delivers an EPUB
- [ ] Existing paid orders in `book_purchases` still resolve downloads (within their 72h window)

## 5. Cadence & ownership
- Backups: [daily DB / weekly assets], owned by [name].
- Restore drill: test a restore to a scratch environment [quarterly].
- Recovery objective targets: RPO [24h], RTO [4h]. [Founder to confirm.]

---
### Founder decisions required
- [ ] Choose DB host/backup mechanism (Atlas Cloud Backups vs mongodump) + retention
- [ ] Choose asset backup destination
- [ ] Assign an owner + set a restore-drill cadence
