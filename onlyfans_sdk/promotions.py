"""
Promotions API
"""
from typing import Any, Dict, List, Literal, Optional, Union, Generator

from ._client import OFAuthClient
from .models import (
    V2AccessPromotionsBundlesGetResponse,
    V2AccessPromotionsBundlesPostRequest,
    V2AccessPromotionsBundlesPostResponse,
    V2AccessPromotionsGetResponse,
    V2AccessPromotionsPostRequest,
    V2AccessPromotionsPostResponse,
    V2AccessPromotionsTrackingLinksGetResponse,
    V2AccessPromotionsTrackingLinksPostRequest,
    V2AccessPromotionsTrackingLinksPostResponse,
    V2AccessPromotionsTrackingLinksShareAccessDeleteRequest,
    V2AccessPromotionsTrackingLinksShareAccessDeleteResponse,
    V2AccessPromotionsTrackingLinksShareAccessPostRequest,
    V2AccessPromotionsTrackingLinksShareAccessPostResponse,
    V2AccessPromotionsTrialLinksGetResponse,
    V2AccessPromotionsTrialLinksPostRequest,
    V2AccessPromotionsTrialLinksPostResponse,
    V2AccessPromotionsTrialLinksShareAccessDeleteRequest,
    V2AccessPromotionsTrialLinksShareAccessDeleteResponse,
    V2AccessPromotionsTrialLinksShareAccessPostRequest,
    V2AccessPromotionsTrialLinksShareAccessPostResponse,
)

def list_tracking_links(
    client: OFAuthClient,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    pagination: Optional[int] = None,
    with_deleted: Optional[int] = None,
    sorting_deleted: Optional[str] = None,
    stats: Optional[Literal["true", "false"]] = None
) -> V2AccessPromotionsTrackingLinksGetResponse:
    """
    List tracking links
    Get a list of all tracking links

**Permission Required:** `promotions:read`
    """
    path = f"/v2/access/promotions/tracking-links"
    query = {
        "limit": limit,
        "offset": offset,
        "pagination": pagination,
        "with_deleted": with_deleted,
        "sorting_deleted": sorting_deleted,
        "stats": stats,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def iter_tracking_links(
    client: OFAuthClient,
    pagination: Optional[int] = None,
    with_deleted: Optional[int] = None,
    sorting_deleted: Optional[str] = None,
    stats: Optional[Literal["true", "false"]] = None,
    page_size: int = 20,
    max_items: Optional[int] = None
) -> Generator[Any, None, None]:
    """
    List tracking links
    
    Returns a generator that yields items one at a time, automatically
    handling pagination.
    
    Args:
        page_size: Number of items per page (default: 20)
        max_items: Maximum total items to yield (default: unlimited)
    
    Yields:
        Individual items from the list response
    
    Example:
        for item in iter_tracking_links(client, connection_id="..."):
            print(item)
    """
    offset = 0
    fetched = 0
    
    while True:
        if max_items is not None and fetched >= max_items:
            return
        
        remaining = page_size if max_items is None else min(page_size, max_items - fetched)
        response = list_tracking_links(
            client=client,
            pagination=pagination,
            with_deleted=with_deleted,
            sorting_deleted=sorting_deleted,
            stats=stats,
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

def create_tracking_links(
    client: OFAuthClient,
    body: V2AccessPromotionsTrackingLinksPostRequest
) -> V2AccessPromotionsTrackingLinksPostResponse:
    """
    Create tracking link
    Create a new tracking link

**Permission Required:** `promotions:write`
    """
    path = f"/v2/access/promotions/tracking-links"
    return client.request(
        "POST",
        path,
        body=body,
    )

def create_tracking_links_share_access(
    client: OFAuthClient,
    body: V2AccessPromotionsTrackingLinksShareAccessPostRequest
) -> V2AccessPromotionsTrackingLinksShareAccessPostResponse:
    """
    Share tracking link access
    Share tracking link access with a user

**Permission Required:** `promotions:write`
    """
    path = f"/v2/access/promotions/tracking-links/share-access"
    return client.request(
        "POST",
        path,
        body=body,
    )

def delete_tracking_links_share_access(
    client: OFAuthClient,
    body: V2AccessPromotionsTrackingLinksShareAccessDeleteRequest
) -> V2AccessPromotionsTrackingLinksShareAccessDeleteResponse:
    """
    Revoke tracking link access
    Revoke tracking link access from a user

**Permission Required:** `promotions:write`
    """
    path = f"/v2/access/promotions/tracking-links/share-access"
    return client.request(
        "DELETE",
        path,
        body=body,
    )

def get_tracking_links(
    client: OFAuthClient,
    tracking_link_id: str
) -> V2AccessPromotionsTrackingLinksGetResponse:
    """
    Get tracking link
    Get details of a specific tracking link

**Permission Required:** `promotions:read`
    """
    path = f"/v2/access/promotions/tracking-links/{tracking_link_id}"
    return client.request(
        "GET",
        path,
    )

def replace_tracking_links(
    client: OFAuthClient,
    tracking_link_id: str,
    body: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update tracking link
    Update an existing tracking link

**Permission Required:** `promotions:write`
    """
    path = f"/v2/access/promotions/tracking-links/{tracking_link_id}"
    return client.request(
        "PUT",
        path,
        body=body,
    )

def delete_tracking_links(
    client: OFAuthClient,
    tracking_link_id: str
) -> Dict[str, Any]:
    """
    Delete tracking link
    Delete a tracking link

**Permission Required:** `promotions:write`
    """
    path = f"/v2/access/promotions/tracking-links/{tracking_link_id}"
    return client.request(
        "DELETE",
        path,
    )

def list_tracking_links_claimers(
    client: OFAuthClient,
    tracking_link_id: str
) -> Dict[str, Any]:
    """
    Get tracking link claimers
    Get list of users who claimed a tracking link

**Permission Required:** `promotions:read`
    """
    path = f"/v2/access/promotions/tracking-links/{tracking_link_id}/claimers"
    return client.request(
        "GET",
        path,
    )

def list_trial_links(
    client: OFAuthClient,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> V2AccessPromotionsTrialLinksGetResponse:
    """
    List trial links
    Get a list of all trial links

**Permission Required:** `promotions:read`
    """
    path = f"/v2/access/promotions/trial-links"
    query = {
        "limit": limit,
        "offset": offset,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def create_trial_links(
    client: OFAuthClient,
    body: V2AccessPromotionsTrialLinksPostRequest
) -> V2AccessPromotionsTrialLinksPostResponse:
    """
    Create trial link
    Create a new trial link

**Permission Required:** `promotions:write`
    """
    path = f"/v2/access/promotions/trial-links"
    return client.request(
        "POST",
        path,
        body=body,
    )

def create_trial_links_share_access(
    client: OFAuthClient,
    body: V2AccessPromotionsTrialLinksShareAccessPostRequest
) -> V2AccessPromotionsTrialLinksShareAccessPostResponse:
    """
    Share trial link access
    Share trial link access with a user

**Permission Required:** `promotions:write`
    """
    path = f"/v2/access/promotions/trial-links/share-access"
    return client.request(
        "POST",
        path,
        body=body,
    )

def delete_trial_links_share_access(
    client: OFAuthClient,
    body: V2AccessPromotionsTrialLinksShareAccessDeleteRequest
) -> V2AccessPromotionsTrialLinksShareAccessDeleteResponse:
    """
    Revoke trial link access
    Revoke trial link access from a user

**Permission Required:** `promotions:write`
    """
    path = f"/v2/access/promotions/trial-links/share-access"
    return client.request(
        "DELETE",
        path,
        body=body,
    )

def get_trial_links(
    client: OFAuthClient,
    trial_link_id: str
) -> V2AccessPromotionsTrialLinksGetResponse:
    """
    Get trial link
    Get details of a specific trial link

**Permission Required:** `promotions:read`
    """
    path = f"/v2/access/promotions/trial-links/{trial_link_id}"
    return client.request(
        "GET",
        path,
    )

def replace_trial_links(
    client: OFAuthClient,
    trial_link_id: str,
    body: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update trial link
    Update an existing trial link

**Permission Required:** `promotions:write`
    """
    path = f"/v2/access/promotions/trial-links/{trial_link_id}"
    return client.request(
        "PUT",
        path,
        body=body,
    )

def delete_trial_links(
    client: OFAuthClient,
    trial_link_id: str
) -> Dict[str, Any]:
    """
    Delete trial link
    Delete a trial link

**Permission Required:** `promotions:write`
    """
    path = f"/v2/access/promotions/trial-links/{trial_link_id}"
    return client.request(
        "DELETE",
        path,
    )

def list_bundles(
    client: OFAuthClient,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> V2AccessPromotionsBundlesGetResponse:
    """
    List bundles
    Get a list of all subscription bundles

**Permission Required:** `promotions:read`
    """
    path = f"/v2/access/promotions/bundles"
    query = {
        "limit": limit,
        "offset": offset,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def create_bundles(
    client: OFAuthClient,
    body: V2AccessPromotionsBundlesPostRequest
) -> V2AccessPromotionsBundlesPostResponse:
    """
    Create bundle
    Create a new subscription bundle

**Permission Required:** `promotions:write`
    """
    path = f"/v2/access/promotions/bundles"
    return client.request(
        "POST",
        path,
        body=body,
    )

def get_bundles(
    client: OFAuthClient,
    bundle_id: str
) -> V2AccessPromotionsBundlesGetResponse:
    """
    Get bundle
    Get details of a specific subscription bundle

**Permission Required:** `promotions:read`
    """
    path = f"/v2/access/promotions/bundles/{bundle_id}"
    return client.request(
        "GET",
        path,
    )

def replace_bundles(
    client: OFAuthClient,
    bundle_id: str,
    body: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update bundle
    Update an existing subscription bundle

**Permission Required:** `promotions:write`
    """
    path = f"/v2/access/promotions/bundles/{bundle_id}"
    return client.request(
        "PUT",
        path,
        body=body,
    )

def delete_bundles(
    client: OFAuthClient,
    bundle_id: str
) -> Dict[str, Any]:
    """
    Delete bundle
    Delete a subscription bundle

**Permission Required:** `promotions:write`
    """
    path = f"/v2/access/promotions/bundles/{bundle_id}"
    return client.request(
        "DELETE",
        path,
    )

def list_promotions(
    client: OFAuthClient,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> V2AccessPromotionsGetResponse:
    """
    List promotions
    Get a list of all promotions

**Permission Required:** `promotions:read`
    """
    path = f"/v2/access/promotions"
    query = {
        "limit": limit,
        "offset": offset,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def create_promotions(
    client: OFAuthClient,
    body: V2AccessPromotionsPostRequest
) -> V2AccessPromotionsPostResponse:
    """
    Create promotion
    Create a new promotion

**Permission Required:** `promotions:write`
    """
    path = f"/v2/access/promotions"
    return client.request(
        "POST",
        path,
        body=body,
    )

def replace_promotions(
    client: OFAuthClient,
    promotion_id: str,
    body: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update promotion
    Update an existing promotion

**Permission Required:** `promotions:write`
    """
    path = f"/v2/access/promotions/{promotion_id}"
    return client.request(
        "PUT",
        path,
        body=body,
    )

def delete_promotions(
    client: OFAuthClient,
    promotion_id: str
) -> Dict[str, Any]:
    """
    Delete promotion
    Delete a promotion

**Permission Required:** `promotions:write`
    """
    path = f"/v2/access/promotions/{promotion_id}"
    return client.request(
        "DELETE",
        path,
    )

def create_stop(
    client: OFAuthClient,
    promotion_id: str
) -> Dict[str, Any]:
    """
    Stop promotion
    Stop/end a promotion

**Permission Required:** `promotions:write`
    """
    path = f"/v2/access/promotions/{promotion_id}/stop"
    return client.request(
        "POST",
        path,
    )
