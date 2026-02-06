"""
Vault API
"""
from typing import Any, Dict, List, Literal, Optional, Union, Generator

from ._client import OFAuthClient
from .models import (
    V2AccessVaultMediaGetResponse,
)

def list_media(
    client: OFAuthClient,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    sort_by: Optional[Literal["recent", "most-liked", "highest-tips"]] = None,
    sort_direction: Optional[Literal["asc", "desc"]] = None,
    list_id: Optional[int] = None,
    query: Optional[str] = None,
    media_type: Optional[Literal["photo", "video", "audio", "gif"]] = None
) -> V2AccessVaultMediaGetResponse:
    """
    List vault media
    List vault media

**Permission Required:** `vault:read`
    """
    path = f"/v2/access/vault/media"
    query = {
        "limit": limit,
        "offset": offset,
        "sortBy": sort_by,
        "sortDirection": sort_direction,
        "listId": list_id,
        "query": query,
        "mediaType": media_type,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def iter_media(
    client: OFAuthClient,
    sort_by: Optional[Literal["recent", "most-liked", "highest-tips"]] = None,
    sort_direction: Optional[Literal["asc", "desc"]] = None,
    list_id: Optional[int] = None,
    query: Optional[str] = None,
    media_type: Optional[Literal["photo", "video", "audio", "gif"]] = None,
    page_size: int = 20,
    max_items: Optional[int] = None
) -> Generator[Any, None, None]:
    """
    List vault media
    
    Returns a generator that yields items one at a time, automatically
    handling pagination.
    
    Args:
        page_size: Number of items per page (default: 20)
        max_items: Maximum total items to yield (default: unlimited)
    
    Yields:
        Individual items from the list response
    
    Example:
        for item in iter_media(client, connection_id="..."):
            print(item)
    """
    offset = 0
    fetched = 0
    
    while True:
        if max_items is not None and fetched >= max_items:
            return
        
        remaining = page_size if max_items is None else min(page_size, max_items - fetched)
        response = list_media(
            client=client,
            sort_by=sort_by,
            sort_direction=sort_direction,
            list_id=list_id,
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
