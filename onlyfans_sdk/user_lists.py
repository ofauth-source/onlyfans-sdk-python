"""
User Lists API
"""
from typing import Any, Dict, List, Literal, Optional, Union, Generator

from ._client import OFAuthClient
from .models import (
    V2AccessUsersListsGetResponse,
    V2AccessUsersListsPostRequest,
    V2AccessUsersListsPostResponse,
)

def create_users_users_lists(
    client: OFAuthClient,
    user_id: str,
    body: V2AccessUsersListsPostRequest
) -> V2AccessUsersListsPostResponse:
    """
    Add user to multiple lists
    Add a single user to multiple lists in one call

**Permission Required:** `lists:write`
    """
    path = f"/v2/access/users/{user_id}/lists"
    return client.request(
        "POST",
        path,
        body=body,
    )

def list_users_users_lists(
    client: OFAuthClient,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    query: Optional[str] = None
) -> V2AccessUsersListsGetResponse:
    """
    List user lists
    List user lists

**Permission Required:** `lists:read`
    """
    path = f"/v2/access/users/lists"
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

def iter_users_users_lists(
    client: OFAuthClient,
    query: Optional[str] = None,
    page_size: int = 20,
    max_items: Optional[int] = None
) -> Generator[Any, None, None]:
    """
    List user lists
    
    Returns a generator that yields items one at a time, automatically
    handling pagination.
    
    Args:
        page_size: Number of items per page (default: 20)
        max_items: Maximum total items to yield (default: unlimited)
    
    Yields:
        Individual items from the list response
    
    Example:
        for item in iter_users_users_lists(client, connection_id="..."):
            print(item)
    """
    offset = 0
    fetched = 0
    
    while True:
        if max_items is not None and fetched >= max_items:
            return
        
        remaining = page_size if max_items is None else min(page_size, max_items - fetched)
        response = list_users_users_lists(
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

def create_users_users_lists_2(
    client: OFAuthClient,
    body: V2AccessUsersListsPostRequest
) -> V2AccessUsersListsPostResponse:
    """
    Create user list
    Create user list

**Permission Required:** `lists:write`
    """
    path = f"/v2/access/users/lists"
    return client.request(
        "POST",
        path,
        body=body,
    )

def get_users_users_lists(
    client: OFAuthClient,
    list_id: str
) -> V2AccessUsersListsGetResponse:
    """
    Get user list
    Get user list

**Permission Required:** `lists:read`
    """
    path = f"/v2/access/users/lists/{list_id}"
    return client.request(
        "GET",
        path,
    )

def update_users_users_lists(
    client: OFAuthClient,
    list_id: str,
    body: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update user list
    Update user list

**Permission Required:** `lists:write`
    """
    path = f"/v2/access/users/lists/{list_id}"
    return client.request(
        "PATCH",
        path,
        body=body,
    )

def delete_users_users_lists(
    client: OFAuthClient,
    list_id: str
) -> Dict[str, Any]:
    """
    Delete user list
    Delete user list

**Permission Required:** `lists:write`
    """
    path = f"/v2/access/users/lists/{list_id}"
    return client.request(
        "DELETE",
        path,
    )

def list_users_lists_users(
    client: OFAuthClient,
    list_id: str,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> Dict[str, Any]:
    """
    List users in user list
    List users in user list

**Permission Required:** `lists:read`
    """
    path = f"/v2/access/users/lists/{list_id}/users"
    query = {
        "limit": limit,
        "offset": offset,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def iter_users_lists_users(
    client: OFAuthClient,
    list_id: str,
    page_size: int = 20,
    max_items: Optional[int] = None
) -> Generator[Any, None, None]:
    """
    List users in user list
    
    Returns a generator that yields items one at a time, automatically
    handling pagination.
    
    Args:
        page_size: Number of items per page (default: 20)
        max_items: Maximum total items to yield (default: unlimited)
    
    Yields:
        Individual items from the list response
    
    Example:
        for item in iter_users_lists_users(client, connection_id="..."):
            print(item)
    """
    offset = 0
    fetched = 0
    
    while True:
        if max_items is not None and fetched >= max_items:
            return
        
        remaining = page_size if max_items is None else min(page_size, max_items - fetched)
        response = list_users_lists_users(
            client=client,
            list_id=list_id,
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

def create_users_lists_users(
    client: OFAuthClient,
    list_id: str,
    user_id: str
) -> Dict[str, Any]:
    """
    Add user to list
    Add a single user to a user list

**Permission Required:** `lists:write`
    """
    path = f"/v2/access/users/lists/{list_id}/users/{user_id}"
    return client.request(
        "POST",
        path,
    )

def delete_users_lists_users(
    client: OFAuthClient,
    list_id: str,
    user_id: str
) -> Dict[str, Any]:
    """
    Remove user from user list
    Remove user from user list

**Permission Required:** `lists:write`
    """
    path = f"/v2/access/users/lists/{list_id}/users/{user_id}"
    return client.request(
        "DELETE",
        path,
    )
