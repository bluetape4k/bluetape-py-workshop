"""Optional two-instance Redis load-coordination workshop."""

from .codec import PRODUCT_METADATA, ProductSummaryCodec
from .observer import CoordinationEventRecorder
from .service import RedisCatalogInstance

__all__ = [
    "PRODUCT_METADATA",
    "CoordinationEventRecorder",
    "ProductSummaryCodec",
    "RedisCatalogInstance",
]
