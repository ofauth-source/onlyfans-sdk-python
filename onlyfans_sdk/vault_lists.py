"""
Vault Lists API
"""
from typing import Any, Dict, List, Literal, Optional, Union, Generator

from ._client import OFAuthClient
from .models import (
    V2AccessVaultListsGetResponse,
    V2AccessVaultListsPostRequest,
    V2AccessVaultListsPostResponse,
)

def list_vault_vault_lists(
    client: OFAuthClient,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    query: Optional[str] = None
) -> V2AccessVaultListsGetResponse:
    """
    List vault folders
    List vault folders

**Permission Required:** `vault:read`
    """
    path = f"/v2/access/vault/lists"
    query = {
        "limit": limit,
        "offset": offset,
        "query": query,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def iter_vault_vault_lists(
    client: OFAuthClient,
    query: Optional[str] = None,
    page_size: int = 20,
    max_items: Optional[int] = None
) -> Generator[Any, None, None]:
    """
    List vault folders
    
    Returns a generator that yields items one at a time, automatically
    handling pagination.
    
    Args:
        page_size: Number of items per page (default: 20)
        max_items: Maximum total items to yield (default: unlimited)
    
    Yields:
        Individual items from the list response
    
    Example:
        for item in iter_vault_vault_lists(client, connection_id="..."):
            print(item)
    """
    offset = 0
    fetched = 0
    
    while True:
        if max_items is not None and fetched >= max_items:
            return
        
        remaining = page_size if max_items is None else min(page_size, max_items - fetched)
        response = list_vault_vault_lists(
            client=client,
            query=query,
            limit=remaining,
            offset=offset,
        )
        
        for item in response.get("list", []):
            if max_items is not None and fetched >= max_items:
                return
            yield item
            fetched += 1
        
        if not response.get("hasMore", False):
            return
        
        offset = response.get("nextOffset", offset + len(response.get("list", [])))

def create_vault_vault_lists(
    client: OFAuthClient,
    body: V2AccessVaultListsPostRequest
) -> V2AccessVaultListsPostResponse:
    """
    Create vault list
    Create vault list

**Permission Required:** `vault:write`
    """
    path = f"/v2/access/vault/lists"
    return client.request(
        "POST",
        path,
        body=body,
    )

def update_vault_vault_lists(
    client: OFAuthClient,
    list_id: float,
    body: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update vault list
    Update vault list

**Permission Required:** `vault:write`
    """
    path = f"/v2/access/vault/lists/{list_id}"
    return client.request(
        "PATCH",
        path,
        body=body,
    )

def delete_vault_vault_lists(
    client: OFAuthClient,
    list_id: float
) -> Dict[str, Any]:
    """
    Delete vault list
    Delete vault list

**Permission Required:** `vault:write`
    """
    path = f"/v2/access/vault/lists/{list_id}"
    return client.request(
        "DELETE",
        path,
    )

def list_vault_vault_lists_media(
    client: OFAuthClient,
    list_id: float,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    sort_by: Optional[Literal["recent", "most-liked", "highest-tips"]] = None,
    sort_direction: Optional[Literal["asc", "desc"]] = None,
    query: Optional[str] = None,
    media_type: Optional[Literal["photo", "video", "audio", "gif"]] = None
) -> Dict[str, Any]:
    """
    List media in vault list
    List media in vault list

**Permission Required:** `vault:read`
    """
    path = f"/v2/access/vault/lists/{list_id}/media"
    query = {
        "limit": limit,
        "offset": offset,
        "sortBy": sort_by,
        "sortDirection": sort_direction,
        "query": query,
        "mediaType": media_type,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def iter_vault_vault_lists_media(
    client: OFAuthClient,
    list_id: float,
    sort_by: Optional[Literal["recent", "most-liked", "highest-tips"]] = None,
    sort_direction: Optional[Literal["asc", "desc"]] = None,
    query: Optional[str] = None,
    media_type: Optional[Literal["photo", "video", "audio", "gif"]] = None,
    page_size: int = 20,
    max_items: Optional[int] = None
) -> Generator[Any, None, None]:
    """
    List media in vault list
    
    Returns a generator that yields items one at a time, automatically
    handling pagination.
    
    Args:
        page_size: Number of items per page (default: 20)
        max_items: Maximum total items to yield (default: unlimited)
    
    Yields:
        Individual items from the list response
    
    Example:
        for item in iter_vault_vault_lists_media(client, connection_id="..."):
            print(item)
    """
    offset = 0
    fetched = 0
    
    while True:
        if max_items is not None and fetched >= max_items:
            return
        
        remaining = page_size if max_items is None else min(page_size, max_items - fetched)
        response = list_vault_vault_lists_media(
            client=client,
            list_id=list_id,
            sort_by=sort_by,
            sort_direction=sort_direction,
            query=query,
            media_type=media_type,
            limit=remaining,
            offset=offset,
        )
        
        for item in response.get("list", []):
            if max_items is not None and fetched >= max_items:
                return
            yield item
            fetched += 1
        
        if not response.get("hasMore", False):
            return
        
        offset = response.get("nextOffset", offset + len(response.get("list", [])))

def create_vault_vault_lists_media(
    client: OFAuthClient,
    list_id: float,
    body: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Add media to vault list
    Add media to vault list

**Permission Required:** `vault:write`
    """
    path = f"/v2/access/vault/lists/{list_id}/media"
    return client.request(
        "POST",
        path,
        body=body,
    )
