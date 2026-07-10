"""QRU Universal Distribution Framework™ — Connector SDK™ (MO-007).

Every destination (public platform OR customer/school/storage) implements ONE interface so the
factory can add channels without redesigning the pipeline. This is the contract the Publishing,
Delivery, Verification, and Analytics engines orchestrate against.

Treasure Standard™: a connector may NEVER report success without a real external ID / confirmed
delivery. When a channel isn't wired, it must honestly return status NEEDS_SETUP.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional


class ConnectorKind(str, Enum):
    PUBLISH = "publish"   # public platforms (YouTube, blog, marketplaces, social)
    DELIVER = "deliver"   # customers, schools, storage (Store, Drive, Email)


class DistMode(str, Enum):
    DRAFT = "draft"
    PRIVATE = "private"
    UNLISTED = "unlisted"
    SCHEDULED = "scheduled"
    PUBLIC = "public"


class DistStatus(str, Enum):
    QUEUED = "queued"
    PUBLISHED = "published"
    DELIVERED = "delivered"
    SCHEDULED = "scheduled"
    FAILED = "failed"
    NEEDS_SETUP = "needs_setup"


@dataclass
class ConnectorCapability:
    id: str
    name: str
    kind: str                       # ConnectorKind
    category: str                   # Video | Marketplace | Blog | Storage | Email | Social | Store
    native: bool                    # native to QRU vs orchestrating an external service
    modes: List[str]                # supported DistMode values
    asset_types: List[str]          # required assets: 'video','pdf','listing','image','file'
    requires_file: bool = False
    analytics_supported: bool = False


@dataclass
class DistributionResult:
    ok: bool
    status: str = DistStatus.QUEUED.value
    external_id: Optional[str] = None      # Video ID / Product ID / Listing ID / Document ID
    url: Optional[str] = None
    detail: str = ""
    verified: bool = False
    extra: dict = field(default_factory=dict)

    def dict(self):
        return asdict(self)


class Connector(ABC):
    """Base class every distribution connector implements."""
    capability: ConnectorCapability

    @abstractmethod
    async def connection_status(self) -> dict:
        """Return {connected, account, can_distribute, reason}. Never raises."""

    def map_metadata(self, product: dict, overrides: dict) -> dict:
        """Platform-specific metadata mapping. Override per connector as needed."""
        content = product.get("content") or product.get("summary") or ""
        meta = {
            "title": product.get("title") or product.get("product_code") or "QRU Product",
            "description": (content[:4500]).strip(),
            "tags": [t for t in [product.get("category"), product.get("product_type")] if t],
        }
        meta.update({k: v for k, v in (overrides or {}).items() if v is not None})
        return meta

    @abstractmethod
    async def distribute(self, product: dict, meta: dict, mode: str, options: dict) -> DistributionResult:
        """Publish/deliver the product. Returns a DistributionResult with a real external_id on success."""

    async def verify(self, external_id: str, options: dict) -> DistributionResult:
        """Confirm the distribution is live and return the canonical external ID/URL."""
        return DistributionResult(ok=True, status=DistStatus.PUBLISHED.value, external_id=external_id, verified=True,
                                  detail="Verification not implemented for this connector.")

    async def fetch_analytics(self, external_id: str, options: dict) -> dict:
        """Return performance metrics, or a not-tracked marker."""
        return {"supported": False, "note": "Analytics not available for this connector yet."}
