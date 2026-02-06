"""
Messages API
"""
from typing import Any, Dict, List, Literal, Optional, Union, Generator

from ._client import OFAuthClient
from .models import (
    V2AccessChatsGetResponse,
    V2AccessMassMessagesGetResponse,
    V2AccessMassMessagesPostRequest,
    V2AccessMassMessagesPostResponse,
)

def list_chats_chats_messages(
    client: OFAuthClient,
    user_id: str,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    query: Optional[str] = None
) -> Dict[str, Any]:
    """
    Chat messages
    Chat messages

**Permission Required:** `messages:read`
    """
    path = f"/v2/access/chats/{user_id}/messages"
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

def iter_chats_chats_messages(
    client: OFAuthClient,
    user_id: str,
    query: Optional[str] = None,
    page_size: int = 20,
    max_items: Optional[int] = None
) -> Generator[Any, None, None]:
    """
    Chat messages
    
    Returns a generator that yields items one at a time, automatically
    handling pagination.
    
    Args:
        page_size: Number of items per page (default: 20)
        max_items: Maximum total items to yield (default: unlimited)
    
    Yields:
        Individual items from the list response
    
    Example:
        for item in iter_chats_chats_messages(client, connection_id="..."):
            print(item)
    """
    offset = 0
    fetched = 0
    
    while True:
        if max_items is not None and fetched >= max_items:
            return
        
        remaining = page_size if max_items is None else min(page_size, max_items - fetched)
        response = list_chats_chats_messages(
            client=client,
            user_id=user_id,
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

def create_chats_chats_messages(
    client: OFAuthClient,
    user_id: str,
    body: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Send chat message
    Send chat message

**Permission Required:** `messages:write`
    """
    path = f"/v2/access/chats/{user_id}/messages"
    return client.request(
        "POST",
        path,
        body=body,
    )

def delete_chats_chats_messages(
    client: OFAuthClient,
    user_id: str,
    message_id: str,
    body: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Unsend chat message
    Unsend chat message

**Permission Required:** `messages:write`
    """
    path = f"/v2/access/chats/{user_id}/messages/{message_id}"
    return client.request(
        "DELETE",
        path,
        body=body,
    )

def list_mass_messages(
    client: OFAuthClient,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    type: Optional[Literal["sent", "unsent", "scheduled"]] = None
) -> V2AccessMassMessagesGetResponse:
    """
    List mass messages
    Get a list of all mass messages (queued, sent, scheduled)

**Permission Required:** `messages:read`
    """
    path = f"/v2/access/mass-messages"
    query = {
        "limit": limit,
        "offset": offset,
        "type": type,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def iter_mass_messages(
    client: OFAuthClient,
    type: Optional[Literal["sent", "unsent", "scheduled"]] = None,
    page_size: int = 20,
    max_items: Optional[int] = None
) -> Generator[Any, None, None]:
    """
    List mass messages
    
    Returns a generator that yields items one at a time, automatically
    handling pagination.
    
    Args:
        page_size: Number of items per page (default: 20)
        max_items: Maximum total items to yield (default: unlimited)
    
    Yields:
        Individual items from the list response
    
    Example:
        for item in iter_mass_messages(client, connection_id="..."):
            print(item)
    """
    offset = 0
    fetched = 0
    
    while True:
        if max_items is not None and fetched >= max_items:
            return
        
        remaining = page_size if max_items is None else min(page_size, max_items - fetched)
        response = list_mass_messages(
            client=client,
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

def create_mass_messages(
    client: OFAuthClient,
    body: V2AccessMassMessagesPostRequest
) -> V2AccessMassMessagesPostResponse:
    """
    Create mass message
    Create a mass message to send to multiple fans

**Permission Required:** `messages:write`
    """
    path = f"/v2/access/mass-messages"
    return client.request(
        "POST",
        path,
        body=body,
    )

def get_mass_messages(
    client: OFAuthClient,
    mass_message_id: str
) -> V2AccessMassMessagesGetResponse:
    """
    Get mass message
    Get details of a specific mass message

**Permission Required:** `messages:read`
    """
    path = f"/v2/access/mass-messages/{mass_message_id}"
    return client.request(
        "GET",
        path,
    )

def replace_mass_messages(
    client: OFAuthClient,
    mass_message_id: str,
    body: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update mass message
    Update an existing mass message

**Permission Required:** `messages:write`
    """
    path = f"/v2/access/mass-messages/{mass_message_id}"
    return client.request(
        "PUT",
        path,
        body=body,
    )

def delete_mass_messages(
    client: OFAuthClient,
    mass_message_id: str
) -> Dict[str, Any]:
    """
    Delete mass message
    Delete a mass message

**Permission Required:** `messages:write`
    """
    path = f"/v2/access/mass-messages/{mass_message_id}"
    return client.request(
        "DELETE",
        path,
    )

def list_chats(
    client: OFAuthClient,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    order: Optional[Literal["recent", "old"]] = None,
    filter: Optional[Literal["priority", "who_tipped", "unread"]] = None,
    query: Optional[str] = None,
    user_list_id: Optional[int] = None
) -> V2AccessChatsGetResponse:
    """
    Chats list
    Chats list

**Permission Required:** `messages:read`
    """
    path = f"/v2/access/chats"
    query = {
        "limit": limit,
        "offset": offset,
        "order": order,
        "filter": filter,
        "query": query,
        "userListId": user_list_id,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def iter_chats(
    client: OFAuthClient,
    order: Optional[Literal["recent", "old"]] = None,
    filter: Optional[Literal["priority", "who_tipped", "unread"]] = None,
    query: Optional[str] = None,
    user_list_id: Optional[int] = None,
    page_size: int = 20,
    max_items: Optional[int] = None
) -> Generator[Any, None, None]:
    """
    Chats list
    
    Returns a generator that yields items one at a time, automatically
    handling pagination.
    
    Args:
        page_size: Number of items per page (default: 20)
        max_items: Maximum total items to yield (default: unlimited)
    
    Yields:
        Individual items from the list response
    
    Example:
        for item in iter_chats(client, connection_id="..."):
            print(item)
    """
    offset = 0
    fetched = 0
    
    while True:
        if max_items is not None and fetched >= max_items:
            return
        
        remaining = page_size if max_items is None else min(page_size, max_items - fetched)
        response = list_chats(
            client=client,
            order=order,
            filter=filter,
            query=query,
            user_list_id=user_list_id,
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

def list_chats_chats_media(
    client: OFAuthClient,
    user_id: str,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    skip_users: Optional[str] = None,
    last_id: Optional[str] = None,
    opened: Optional[Literal["0", "1", "true", "false"]] = None,
    type: Optional[Literal["photos", "videos", "audios"]] = None
) -> Dict[str, Any]:
    """
    Get chat media
    Get media from a chat. Use the `type` query parameter to filter by media type: 'photos', 'videos', or 'audios'. Omit `type` to get all media.

**Permission Required:** `messages:read`
    """
    path = f"/v2/access/chats/{user_id}/media"
    query = {
        "limit": limit,
        "offset": offset,
        "skip_users": skip_users,
        "last_id": last_id,
        "opened": opened,
        "type": type,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def iter_chats_chats_media(
    client: OFAuthClient,
    user_id: str,
    skip_users: Optional[str] = None,
    last_id: Optional[str] = None,
    opened: Optional[Literal["0", "1", "true", "false"]] = None,
    type: Optional[Literal["photos", "videos", "audios"]] = None,
    page_size: int = 20,
    max_items: Optional[int] = None
) -> Generator[Any, None, None]:
    """
    Get chat media
    
    Returns a generator that yields items one at a time, automatically
    handling pagination.
    
    Args:
        page_size: Number of items per page (default: 20)
        max_items: Maximum total items to yield (default: unlimited)
    
    Yields:
        Individual items from the list response
    
    Example:
        for item in iter_chats_chats_media(client, connection_id="..."):
            print(item)
    """
    offset = 0
    fetched = 0
    
    while True:
        if max_items is not None and fetched >= max_items:
            return
        
        remaining = page_size if max_items is None else min(page_size, max_items - fetched)
        response = list_chats_chats_media(
            client=client,
            user_id=user_id,
            skip_users=skip_users,
            last_id=last_id,
            opened=opened,
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
