"""
Self API
"""
from typing import Any, Dict, List, Literal, Optional, Union, Generator

from ._client import OFAuthClient
from .models import (
    V2AccessSelfGetResponse,
    V2AccessSelfNotificationsGetResponse,
    V2AccessSelfPatchRequest,
    V2AccessSelfPatchResponse,
    V2AccessSelfReleaseFormsGetResponse,
    V2AccessSelfTaggedFriendUsersGetResponse,
)

def list_selfs(
    client: OFAuthClient
) -> V2AccessSelfGetResponse:
    """
    Get current user
    Get current user

**Permission Required:** `profile:read`
    """
    path = f"/v2/access/self"
    return client.request(
        "GET",
        path,
    )

def update_self(
    client: OFAuthClient,
    body: V2AccessSelfPatchRequest
) -> V2AccessSelfPatchResponse:
    """
    Update current user profile
    Update current user profile

**Permission Required:** `profile:write`
    """
    path = f"/v2/access/self"
    return client.request(
        "PATCH",
        path,
        body=body,
    )

def list_notifications(
    client: OFAuthClient,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    type: Optional[Literal["subscribed", "purchases", "tip", "post", "commented", "mentioned", "favorited", "message"]] = None,
    related_username: Optional[str] = None
) -> V2AccessSelfNotificationsGetResponse:
    """
    List notifications
    List notifications

**Permission Required:** `notifications:read`
    """
    path = f"/v2/access/self/notifications"
    query = {
        "limit": limit,
        "offset": offset,
        "type": type,
        "relatedUsername": related_username,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def iter_notifications(
    client: OFAuthClient,
    type: Optional[Literal["subscribed", "purchases", "tip", "post", "commented", "mentioned", "favorited", "message"]] = None,
    related_username: Optional[str] = None,
    page_size: int = 20,
    max_items: Optional[int] = None
) -> Generator[Any, None, None]:
    """
    List notifications
    
    Returns a generator that yields items one at a time, automatically
    handling pagination.
    
    Args:
        page_size: Number of items per page (default: 20)
        max_items: Maximum total items to yield (default: unlimited)
    
    Yields:
        Individual items from the list response
    
    Example:
        for item in iter_notifications(client, connection_id="..."):
            print(item)
    """
    offset = 0
    fetched = 0
    
    while True:
        if max_items is not None and fetched >= max_items:
            return
        
        remaining = page_size if max_items is None else min(page_size, max_items - fetched)
        response = list_notifications(
            client=client,
            type=type,
            related_username=related_username,
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

def list_release_forms(
    client: OFAuthClient,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    filter: Optional[Literal["all", "pending"]] = None,
    sort_by: Optional[Literal["date", "name"]] = None,
    sort_direction: Optional[Literal["asc", "desc"]] = None,
    search: Optional[str] = None
) -> V2AccessSelfReleaseFormsGetResponse:
    """
    List release forms
    List release forms

**Permission Required:** `profile:read`
    """
    path = f"/v2/access/self/release-forms"
    query = {
        "limit": limit,
        "offset": offset,
        "filter": filter,
        "sortBy": sort_by,
        "sortDirection": sort_direction,
        "search": search,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def iter_release_forms(
    client: OFAuthClient,
    filter: Optional[Literal["all", "pending"]] = None,
    sort_by: Optional[Literal["date", "name"]] = None,
    sort_direction: Optional[Literal["asc", "desc"]] = None,
    search: Optional[str] = None,
    page_size: int = 20,
    max_items: Optional[int] = None
) -> Generator[Any, None, None]:
    """
    List release forms
    
    Returns a generator that yields items one at a time, automatically
    handling pagination.
    
    Args:
        page_size: Number of items per page (default: 20)
        max_items: Maximum total items to yield (default: unlimited)
    
    Yields:
        Individual items from the list response
    
    Example:
        for item in iter_release_forms(client, connection_id="..."):
            print(item)
    """
    offset = 0
    fetched = 0
    
    while True:
        if max_items is not None and fetched >= max_items:
            return
        
        remaining = page_size if max_items is None else min(page_size, max_items - fetched)
        response = list_release_forms(
            client=client,
            filter=filter,
            sort_by=sort_by,
            sort_direction=sort_direction,
            search=search,
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

def list_tagged_friend_users(
    client: OFAuthClient,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    filter: Optional[Literal["all", "pending"]] = None,
    sort_by: Optional[Literal["date", "name"]] = None,
    sort_direction: Optional[Literal["asc", "desc"]] = None,
    search: Optional[str] = None
) -> V2AccessSelfTaggedFriendUsersGetResponse:
    """
    List tagged friend users
    List tagged friend users

**Permission Required:** `profile:read`
    """
    path = f"/v2/access/self/tagged-friend-users"
    query = {
        "limit": limit,
        "offset": offset,
        "filter": filter,
        "sortBy": sort_by,
        "sortDirection": sort_direction,
        "search": search,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def iter_tagged_friend_users(
    client: OFAuthClient,
    filter: Optional[Literal["all", "pending"]] = None,
    sort_by: Optional[Literal["date", "name"]] = None,
    sort_direction: Optional[Literal["asc", "desc"]] = None,
    search: Optional[str] = None,
    page_size: int = 20,
    max_items: Optional[int] = None
) -> Generator[Any, None, None]:
    """
    List tagged friend users
    
    Returns a generator that yields items one at a time, automatically
    handling pagination.
    
    Args:
        page_size: Number of items per page (default: 20)
        max_items: Maximum total items to yield (default: unlimited)
    
    Yields:
        Individual items from the list response
    
    Example:
        for item in iter_tagged_friend_users(client, connection_id="..."):
            print(item)
    """
    offset = 0
    fetched = 0
    
    while True:
        if max_items is not None and fetched >= max_items:
            return
        
        remaining = page_size if max_items is None else min(page_size, max_items - fetched)
        response = list_tagged_friend_users(
            client=client,
            filter=filter,
            sort_by=sort_by,
            sort_direction=sort_direction,
            search=search,
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
