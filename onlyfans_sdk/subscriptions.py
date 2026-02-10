"""
Subscriptions API
"""
from typing import Any, Dict, List, Literal, Optional, Union, Generator

from ._client import OFAuthClient
from .models import (
    V2AccessSubscriptionsCountGetResponse,
    V2AccessSubscriptionsGetResponse,
)

def list_subscriptions(
    client: OFAuthClient,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    query: Optional[str] = None,
    filter: Optional[Dict[str, Any]] = None,
    type: Optional[Literal["all", "active", "expired"]] = None
) -> V2AccessSubscriptionsGetResponse:
    """
    List subscriptions
    Get a paginated list of people you're subscribed to/following. Use the `type` query parameter to filter: 'all' (default), 'active', or 'expired'.

**Permission Required:** `subscriptions:read`
    """
    path = f"/v2/access/subscriptions"
    query = {
        "limit": limit,
        "offset": offset,
        "query": query,
        "filter": filter,
        "type": type,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def iter_subscriptions(
    client: OFAuthClient,
    query: Optional[str] = None,
    filter: Optional[Dict[str, Any]] = None,
    type: Optional[Literal["all", "active", "expired"]] = None,
    page_size: int = 20,
    max_items: Optional[int] = None
) -> Generator[Any, None, None]:
    """
    List subscriptions
    
    Returns a generator that yields items one at a time, automatically
    handling pagination.
    
    Args:
        page_size: Number of items per page (default: 20)
        max_items: Maximum total items to yield (default: unlimited)
    
    Yields:
        Individual items from the list response
    
    Example:
        for item in iter_subscriptions(client, connection_id="..."):
            print(item)
    """
    offset = 0
    fetched = 0
    
    while True:
        if max_items is not None and fetched >= max_items:
            return
        
        remaining = page_size if max_items is None else min(page_size, max_items - fetched)
        response = list_subscriptions(
            client=client,
            query=query,
            filter=filter,
            type=type,
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

def list_historys(
    client: OFAuthClient,
    subscription_id: str,
    all: Optional[Literal["0", "1", "true", "false"]] = None
) -> Dict[str, Any]:
    """
    Get subscription history
    Get subscription history for a specific subscription

**Permission Required:** `subscriptions:read`
    """
    path = f"/v2/access/subscriptions/{subscription_id}/history"
    query = {
        "all": all,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def list_counts(
    client: OFAuthClient
) -> V2AccessSubscriptionsCountGetResponse:
    """
    Get subscription counts
    Get counts of subscriptions and subscribers by status

**Permission Required:** `subscriptions:read`
    """
    path = f"/v2/access/subscriptions/count"
    return client.request(
        "GET",
        path,
    )
