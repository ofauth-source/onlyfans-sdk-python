"""
Vault+ Media API
"""
from typing import Any, Dict, List, Literal, Optional, Union, Generator

from ._client import OFAuthClient
from .models import (
    V2VaultPlusBatchPostRequest,
    V2VaultPlusBatchPostResponse,
    V2VaultPlusListGetResponse,
    V2VaultPlusPurgeDeleteResponse,
)

def get_v2_vault_plus(
    client: OFAuthClient,
    connection_id: str,
    media_id: str
) -> Dict[str, Any]:
    """
    Get media item with all quality variants
    Get a media item with all its quality variants and presigned URLs
    """
    path = f"/v2/vault-plus/{media_id}"
    return client.request(
        "GET",
        path,
        connection_id=connection_id,
    )

def delete_v2_vault_plus(
    client: OFAuthClient,
    connection_id: str,
    media_id: str
) -> Dict[str, Any]:
    """
    Delete a stored media item
    Remove a media item from cache
    """
    path = f"/v2/vault-plus/{media_id}"
    return client.request(
        "DELETE",
        path,
        connection_id=connection_id,
    )

def create_v2_vault_plus_batch(
    client: OFAuthClient,
    connection_id: str,
    body: V2VaultPlusBatchPostRequest
) -> V2VaultPlusBatchPostResponse:
    """
    Get multiple media items with all quality variants
    Get multiple media items with all their quality variants and presigned URLs
    """
    path = f"/v2/vault-plus/batch"
    return client.request(
        "POST",
        path,
        body=body,
        connection_id=connection_id,
    )

def list_v2_vault_plus_lists(
    client: OFAuthClient,
    connection_id: str,
    status: Optional[Literal["edge_only", "pending", "storing", "stored", "removed"]] = None,
    source: Optional[Literal["vault", "messages", "posts", "stories"]] = None,
    content_type: Optional[str] = None,
    limit: Optional[float] = None,
    cursor: Optional[str] = None
) -> V2VaultPlusListGetResponse:
    """
    List stored media for a connection
    List all stored media items for a connection with pagination
    """
    path = f"/v2/vault-plus/list"
    query = {
        "status": status,
        "source": source,
        "contentType": content_type,
        "limit": limit,
        "cursor": cursor,
    }
    return client.request(
        "GET",
        path,
        query=query,
        connection_id=connection_id,
    )

def delete_v2_vault_plus_purge(
    client: OFAuthClient,
    connection_id: str
) -> V2VaultPlusPurgeDeleteResponse:
    """
    Remove all stored media for a connection
    Remove all stored media items for a specific connection from Vault+
    """
    path = f"/v2/vault-plus/purge"
    return client.request(
        "DELETE",
        path,
        connection_id=connection_id,
    )
