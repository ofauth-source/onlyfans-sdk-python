"""
Subscribers API
"""
from typing import Any, Dict, List, Literal, Optional, Union, Generator

from ._client import OFAuthClient
from .models import (
    V2AccessSubscribersGetResponse,
)

def list_subscribers(
    client: OFAuthClient,
    query: Optional[str] = None,
    filter: Optional[Dict[str, Any]] = None,
    type: Optional[Union[Literal["all", "active", "expired"], Literal["latest"]]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    latest_type: Optional[Literal["total", "new", "renewals"]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> V2AccessSubscribersGetResponse:
    """
    List subscribers
    Get a paginated list of subscribers. Use the `type` query parameter to filter: 'all' (default), 'active', 'expired', or 'latest'. For 'latest', you can also use `startDate`, `endDate`, and `latestType` ('new' or 'renewals') to filter by date range.

**Permission Required:** `subscribers:read`
    """
    path = f"/v2/access/subscribers"
    query = {
        "query": query,
        "filter": filter,
        "type": type,
        "startDate": start_date,
        "endDate": end_date,
        "latestType": latest_type,
        "limit": limit,
        "offset": offset,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def iter_subscribers(
    client: OFAuthClient,
    query: Optional[str] = None,
    filter: Optional[Dict[str, Any]] = None,
    type: Optional[Union[Literal["all", "active", "expired"], Literal["latest"]]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    latest_type: Optional[Literal["total", "new", "renewals"]] = None,
    page_size: int = 20,
    max_items: Optional[int] = None
) -> Generator[Any, None, None]:
    """
    List subscribers
    
    Returns a generator that yields items one at a time, automatically
    handling pagination.
    
    Args:
        page_size: Number of items per page (default: 20)
        max_items: Maximum total items to yield (default: unlimited)
    
    Yields:
        Individual items from the list response
    
    Example:
        for item in iter_subscribers(client, connection_id="..."):
            print(item)
    """
    offset = 0
    fetched = 0
    
    while True:
        if max_items is not None and fetched >= max_items:
            return
        
        remaining = page_size if max_items is None else min(page_size, max_items - fetched)
        response = list_subscribers(
            client=client,
            query=query,
            filter=filter,
            type=type,
            start_date=start_date,
            end_date=end_date,
            latest_type=latest_type,
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

def set_note(
    client: OFAuthClient,
    user_id: str,
    body: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update subscriber note
    Update the note/notice for a subscriber

**Permission Required:** `subscribers:write`
    """
    path = f"/v2/access/subscribers/{user_id}/note"
    return client.request(
        "PUT",
        path,
        body=body,
    )

def set_discount(
    client: OFAuthClient,
    user_id: str,
    body: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Apply discount to subscriber
    Apply a discount to a subscriber's subscription

**Permission Required:** `subscribers:write`
    """
    path = f"/v2/access/subscribers/{user_id}/discount"
    return client.request(
        "PUT",
        path,
        body=body,
    )

def set_custom_name(
    client: OFAuthClient,
    user_id: str,
    body: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Set custom name for subscriber
    Set a custom display name for a subscriber

**Permission Required:** `subscribers:write`
    """
    path = f"/v2/access/subscribers/{user_id}/custom-name"
    return client.request(
        "PUT",
        path,
        body=body,
    )
