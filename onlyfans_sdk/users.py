"""
Users API
"""
from typing import Any, Dict, List, Literal, Optional, Union, Generator

from ._client import OFAuthClient
from .models import (
    V2AccessUsersBlockedGetResponse,
    V2AccessUsersListGetResponse,
    V2AccessUsersRestrictGetResponse,
    V2AccessUsersSearchGetResponse,
)

def get_users(
    client: OFAuthClient,
    user_id: str
) -> Dict[str, Any]:
    """
    Get user
    Get user

**Permission Required:** `profile:read`
    """
    path = f"/v2/access/users/{user_id}"
    return client.request(
        "GET",
        path,
    )

def create_restrict(
    client: OFAuthClient,
    user_id: str
) -> Dict[str, Any]:
    """
    Restrict user
    Restrict user

**Permission Required:** `users:write`
    """
    path = f"/v2/access/users/{user_id}/restrict"
    return client.request(
        "POST",
        path,
    )

def delete_restrict(
    client: OFAuthClient,
    user_id: str
) -> Dict[str, Any]:
    """
    Unrestrict user
    Unrestrict user

**Permission Required:** `users:write`
    """
    path = f"/v2/access/users/{user_id}/restrict"
    return client.request(
        "DELETE",
        path,
    )

def list_blockeds(
    client: OFAuthClient,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> V2AccessUsersBlockedGetResponse:
    """
    List blocked users
    List blocked users

**Permission Required:** `users:write`
    """
    path = f"/v2/access/users/blocked"
    query = {
        "limit": limit,
        "offset": offset,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def iter_blockeds(
    client: OFAuthClient,
    page_size: int = 20,
    max_items: Optional[int] = None
) -> Generator[Any, None, None]:
    """
    List blocked users
    
    Returns a generator that yields items one at a time, automatically
    handling pagination.
    
    Args:
        page_size: Number of items per page (default: 20)
        max_items: Maximum total items to yield (default: unlimited)
    
    Yields:
        Individual items from the list response
    
    Example:
        for item in iter_blockeds(client, connection_id="..."):
            print(item)
    """
    offset = 0
    fetched = 0
    
    while True:
        if max_items is not None and fetched >= max_items:
            return
        
        remaining = page_size if max_items is None else min(page_size, max_items - fetched)
        response = list_blockeds(
            client=client,
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

def list_lists(
    client: OFAuthClient,
    user_ids: Optional[Union[List[str], str]]
) -> V2AccessUsersListGetResponse:
    """
    List users by IDs
    Get user profiles for multiple users by their IDs. Provide `userIds` as an array of user IDs (strings or numbers) or as a comma-separated string (e.g., `userIds=123,456,789`). Maximum 10 user IDs per request. Returns an array of user profiles.

**Permission Required:** `profile:read`
    """
    path = f"/v2/access/users/list"
    query = {
        "userIds": user_ids,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def list_restricts(
    client: OFAuthClient,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> V2AccessUsersRestrictGetResponse:
    """
    List restricted users
    List restricted users

**Permission Required:** `users:write`
    """
    path = f"/v2/access/users/restrict"
    query = {
        "limit": limit,
        "offset": offset,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def iter_restricts(
    client: OFAuthClient,
    page_size: int = 20,
    max_items: Optional[int] = None
) -> Generator[Any, None, None]:
    """
    List restricted users
    
    Returns a generator that yields items one at a time, automatically
    handling pagination.
    
    Args:
        page_size: Number of items per page (default: 20)
        max_items: Maximum total items to yield (default: unlimited)
    
    Yields:
        Individual items from the list response
    
    Example:
        for item in iter_restricts(client, connection_id="..."):
            print(item)
    """
    offset = 0
    fetched = 0
    
    while True:
        if max_items is not None and fetched >= max_items:
            return
        
        remaining = page_size if max_items is None else min(page_size, max_items - fetched)
        response = list_restricts(
            client=client,
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

def list_searchs(
    client: OFAuthClient,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    query: Optional[str] = None
) -> V2AccessUsersSearchGetResponse:
    """
    Search performers
    Search for performers/users

**Permission Required:** `profile:read`
    """
    path = f"/v2/access/users/search"
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
