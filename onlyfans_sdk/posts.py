"""
Posts API
"""
from typing import Any, Dict, List, Literal, Optional, Union, Generator

from ._client import OFAuthClient
from .models import (
    V2AccessPostsGetResponse,
    V2AccessPostsPostRequest,
    V2AccessPostsPostResponse,
)

def list_posts(
    client: OFAuthClient,
    limit: Optional[int] = None,
    sort_by: Optional[Literal["publish_date", "tips", "favorites_count"]] = None,
    sort_direction: Optional[Literal["asc", "desc"]] = None,
    pinned: Optional[bool] = None,
    include_post_counts: Optional[bool] = None,
    before_publish_time: Optional[str] = None
) -> V2AccessPostsGetResponse:
    """
    List own posts
    Get a list of your own posts

**Permission Required:** `posts:read`
    """
    path = f"/v2/access/posts"
    query = {
        "limit": limit,
        "sortBy": sort_by,
        "sortDirection": sort_direction,
        "pinned": pinned,
        "includePostCounts": include_post_counts,
        "beforePublishTime": before_publish_time,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def create_posts(
    client: OFAuthClient,
    body: V2AccessPostsPostRequest
) -> V2AccessPostsPostResponse:
    """
    Create post
    Create post

**Permission Required:** `posts:write`
    """
    path = f"/v2/access/posts"
    return client.request(
        "POST",
        path,
        body=body,
    )

def get_posts(
    client: OFAuthClient,
    post_id: str
) -> V2AccessPostsGetResponse:
    """
    Get post
    Get post

**Permission Required:** `posts:read`
    """
    path = f"/v2/access/posts/{post_id}"
    return client.request(
        "GET",
        path,
    )

def replace_posts(
    client: OFAuthClient,
    post_id: str,
    body: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Edit post
    Edit post

**Permission Required:** `posts:write`
    """
    path = f"/v2/access/posts/{post_id}"
    return client.request(
        "PUT",
        path,
        body=body,
    )

def delete_posts(
    client: OFAuthClient,
    post_id: str
) -> Dict[str, Any]:
    """
    Delete post
    Delete post

**Permission Required:** `posts:write`
    """
    path = f"/v2/access/posts/{post_id}"
    return client.request(
        "DELETE",
        path,
    )

def list_users_users_posts(
    client: OFAuthClient,
    user_id: str,
    limit: Optional[int] = None,
    sort_by: Optional[Literal["publish_date", "tips", "favorites_count"]] = None,
    sort_direction: Optional[Literal["asc", "desc"]] = None,
    pinned: Optional[bool] = None,
    include_post_counts: Optional[bool] = None,
    before_publish_time: Optional[str] = None
) -> Dict[str, Any]:
    """
    List user posts
    List user posts

**Permission Required:** `posts:read`
    """
    path = f"/v2/access/users/{user_id}/posts"
    query = {
        "limit": limit,
        "sortBy": sort_by,
        "sortDirection": sort_direction,
        "pinned": pinned,
        "includePostCounts": include_post_counts,
        "beforePublishTime": before_publish_time,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )
