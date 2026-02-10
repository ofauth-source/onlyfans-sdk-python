"""
OFAuth Python SDK v2

Includes Pydantic models for type-safe API responses.
"""
from ._client import OFAuthClient, OFAuthError, BASE_URL

# Import all API modules
from . import analytics
from . import messages
from . import earnings
from . import posts
from . import promotions
from . import self
from . import subscribers
from . import subscriptions
from . import upload
from . import users
from . import user_lists
from . import vault_lists
from . import vault
from . import account
from . import dynamic_rules
from . import link
from . import vault_media
from . import vault_store
from . import vault_stats

# Import generated Pydantic models for type safety
from . import models

# Import webhook utilities
from . import webhooks

__all__ = [
    "OFAuthClient",
    "OFAuthError",
    "BASE_URL",
    "models",
    "webhooks",
    "analytics",
    "messages",
    "earnings",
    "posts",
    "promotions",
    "self",
    "subscribers",
    "subscriptions",
    "upload",
    "users",
    "user_lists",
    "vault_lists",
    "vault",
    "account",
    "dynamic_rules",
    "link",
    "vault_media",
    "vault_store",
    "vault_stats",
]
