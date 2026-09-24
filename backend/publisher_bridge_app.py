"""Small independently deployable Publisher Lite bridge."""
import os

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from routers.publisher_lite import router as publisher_lite_router

app = FastAPI(title="QRU Publisher Lite Bridge", version="1.0.0")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "qru-publisher-lite-bridge", "schema_version": "1.0"}


app.include_router(publisher_lite_router)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=False,
    allow_origins=[value for value in os.environ.get("CORS_ORIGINS", "https://qru-online.com").split(",") if value],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
