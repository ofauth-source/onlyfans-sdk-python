"""
Account API
"""
from typing import Any, Dict, List, Literal, Optional, Union, Generator

from ._client import OFAuthClient
from .models import (
    V2AccountConnectionsGetResponse,
    V2AccountConnectionsImportPostRequest,
    V2AccountConnectionsImportPostResponse,
    V2AccountSettingsGetResponse,
    V2AccountSettingsPatchRequest,
    V2AccountSettingsPatchResponse,
    V2AccountWhoamiGetResponse,
)

def whoami(
    client: OFAuthClient
) -> V2AccountWhoamiGetResponse:
    """
    Whoami
    Returns general account information for the API key's organization.
    """
    path = f"/v2/account/whoami"
    return client.request(
        "GET",
        path,
    )

def delete_connections(
    client: OFAuthClient,
    connection_id: str
) -> Dict[str, Any]:
    """
    Disconnect connection
    Disconnects a connection, and logs out the user. Must be called to remove the connection from your account and stop billing.
    """
    path = f"/v2/account/connections/{connection_id}"
    return client.request(
        "DELETE",
        path,
    )

def invalidate_connections(
    client: OFAuthClient,
    connection_id: str
) -> Dict[str, Any]:
    """
    Invalidate connection
    Invalidates a connection by marking it as expired and logging out the user. The connection record is preserved, allowing the user to reconnect with updated permissions.
    """
    path = f"/v2/account/connections/{connection_id}/invalidate"
    return client.request(
        "POST",
        path,
    )

def list_connections(
    client: OFAuthClient,
    status: Optional[Literal["active", "expired", "awaiting_2fa"]] = None,
    imported: Optional[Literal["true", "false"]] = None,
    limit: Optional[float] = None,
    offset: Optional[float] = None
) -> V2AccountConnectionsGetResponse:
    """
    List connections
    List connections for your organization
    """
    path = f"/v2/account/connections"
    query = {
        "status": status,
        "imported": imported,
        "limit": limit,
        "offset": offset,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def iter_connections(
    client: OFAuthClient,
    status: Optional[Literal["active", "expired", "awaiting_2fa"]] = None,
    imported: Optional[Literal["true", "false"]] = None,
    page_size: int = 20,
    max_items: Optional[int] = None
) -> Generator[Any, None, None]:
    """
    List connections
    
    Returns a generator that yields items one at a time, automatically
    handling pagination.
    
    Args:
        page_size: Number of items per page (default: 20)
        max_items: Maximum total items to yield (default: unlimited)
    
    Yields:
        Individual items from the list response
    
    Example:
        for item in iter_connections(client, connection_id="..."):
            print(item)
    """
    offset = 0
    fetched = 0
    
    while True:
        if max_items is not None and fetched >= max_items:
            return
        
        remaining = page_size if max_items is None else min(page_size, max_items - fetched)
        response = list_connections(
            client=client,
            status=status,
            imported=imported,
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

def get_connection_settings(
    client: OFAuthClient,
    connection_id: str
) -> Dict[str, Any]:
    """
    Get connection settings
    Get settings for a specific connection including Vault+ state
    """
    path = f"/v2/account/connections/{connection_id}/settings"
    return client.request(
        "GET",
        path,
    )

def update_connection_settings(
    client: OFAuthClient,
    connection_id: str,
    body: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update connection settings
    Update settings for a specific connection. Set vaultPlus.enabled to toggle vault caching. Set vaultPlus.settings to override org defaults (null to reset to org defaults).
    """
    path = f"/v2/account/connections/{connection_id}/settings"
    return client.request(
        "PATCH",
        path,
        body=body,
    )

def create_connections_connections_import(
    client: OFAuthClient,
    body: V2AccountConnectionsImportPostRequest
) -> V2AccountConnectionsImportPostResponse:
    """
    Import connection
    Import an externally managed connection. Imported connections are not billed monthly and are not health-checked by the connection monitor. They can be used through the Access API immediately. The session is validated by making a request to OnlyFans, and user profile data is fetched automatically.
    """
    path = f"/v2/account/connections/import"
    return client.request(
        "POST",
        path,
        body=body,
    )

def update_connections_connections_import(
    client: OFAuthClient,
    connection_id: str,
    body: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update imported connection session
    Update the session data for an existing imported connection. The new session must belong to the same OnlyFans user (matched by user ID from the cookie). This allows refreshing expired or rotated sessions without deleting and re-importing the connection, preserving the connection ID.
    """
    path = f"/v2/account/connections/import/{connection_id}"
    return client.request(
        "PATCH",
        path,
        body=body,
    )

def get_org_settings(
    client: OFAuthClient
) -> V2AccountSettingsGetResponse:
    """
    Get organization settings
    Get settings for the organization including Vault+ configuration
    """
    path = f"/v2/account/settings"
    return client.request(
        "GET",
        path,
    )

def update_org_settings(
    client: OFAuthClient,
    body: V2AccountSettingsPatchRequest
) -> V2AccountSettingsPatchResponse:
    """
    Update organization settings
    Update settings for the organization. Use applyToExistingConnections to propagate Vault+ settings to all connections.
    """
    path = f"/v2/account/settings"
    return client.request(
        "PATCH",
        path,
        body=body,
    )
