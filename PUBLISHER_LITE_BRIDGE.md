# QRU Publisher Lite Bridge

This is the portable, independently deployable bridge from an approved Publisher Lite record to the QRU Online catalog. It does not use the legacy Factory-v2 handoff or Emergent-only storage.

## Current contract

- `schema_version`: `1.0`
- required objects: `product`, `assets`, `distribution`, `approval`, `validation`
- distribution channel: `qru_online_v2`
- exactly-once key: `product_key:version:release_zip_sha256`

The test suite uses a synthetic non-production record. Production release locators, hashes, and metadata stay in the private release queue rather than this public repository.

## Runtime configuration

Required:

- `MONGO_URL`
- `DB_NAME`
- `PUBLISHER_BRIDGE_TOKEN`
- `S3_BUCKET`
- `S3_ACCESS_KEY_ID` and `S3_SECRET_ACCESS_KEY` (or AWS equivalents)

Optional:

- `S3_ENDPOINT_URL` for an S3-compatible provider
- `S3_REGION`
- `QRU_PUBLIC_SITE_URL` (defaults to `https://qru-online.com`)
- `CORS_ORIGINS`

Railway builds the lightweight service with `Dockerfile.publisher-bridge`; it does not boot the Emergent-era Factory application.

## Publish call

Send a multipart `POST /api/publisher-lite/publish` with:

- `record`: the Publisher Lite JSON record
- `package`: the unchanged approved ZIP
- `Authorization: Bearer <PUBLISHER_BRIDGE_TOKEN>`

On success the bridge returns and persists a receipt containing the live product URL, catalog ID, product version, release ZIP SHA-256, delivery attachment state, and publication timestamp. Exact retries return the same receipt. Validation and infrastructure failures remain visible in `/api/publisher-lite/queue` and can be retried safely.

The protected `/api/publisher-lite/products/{product_id}/download` endpoint is intended for the existing paid-order service after its already-proven payment check; the bridge does not duplicate checkout logic.
