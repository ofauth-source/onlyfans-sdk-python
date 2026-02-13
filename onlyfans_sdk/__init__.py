"""
OFAuth Python SDK v2

Includes Pydantic models for type-safe API responses.
"""
from ._client import OFAuthClient, OFAuthError, BASE_URL

# Import all API modules
from . import account
from . import self
from . import earnings
from . import analytics
from . import posts
from . import messages
from . import subscribers
from . import subscriptions
from . import promotions
from . import users
from . import user_lists
from . import vault
from . import vault_lists
from . import upload
from . import link
from . import dynamic_rules
from . import vault_store
from . import vault_stats
from . import vault_media

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
    "account",
    "self",
    "earnings",
    "analytics",
    "posts",
    "messages",
    "subscribers",
    "subscriptions",
    "promotions",
    "users",
    "user_lists",
    "vault",
    "vault_lists",
    "upload",
    "link",
    "dynamic_rules",
    "vault_store",
    "vault_stats",
    "vault_media",
]
