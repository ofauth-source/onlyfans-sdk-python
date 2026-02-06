"""
Vault+ Stats API
"""
from typing import Any, Dict, List, Literal, Optional, Union, Generator

from ._client import OFAuthClient
from .models import (
    V2VaultPlusStoreStatsGetResponse,
    V2VaultPlusStoreStatusGetResponse,
)

def list_v2_vault_plus_store_status(
    client: OFAuthClient,
    connection_id: str
) -> V2VaultPlusStoreStatusGetResponse:
    """
    Get storage status for a connection
    Get the current storage status and statistics for a connection
    """
    path = f"/v2/vault-plus/store/status"
    return client.request(
        "GET",
        path,
        connection_id=connection_id,
    )

def list_v2_vault_plus_store_stats(
    client: OFAuthClient
) -> V2VaultPlusStoreStatsGetResponse:
    """
    Get organization vault stats
    Get aggregated vault statistics for the organization
    """
    path = f"/v2/vault-plus/store/stats"
    return client.request(
        "GET",
        path,
    )
