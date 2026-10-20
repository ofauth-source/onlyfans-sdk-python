"""
Mass Messages API
"""
from typing import Any, Dict, List, Literal, Optional, Union, Generator

from ._client import OFAuthClient

def list_scheduleds(
    client: OFAuthClient,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> Dict[str, Any]:
    """
    List scheduled mass messages
    List mass messages that have not been sent yet.

**Permission Required:** `messages:read`
    """
    path = f"/v2/access/mass-messages/scheduled"
    query = {
        "limit": limit,
        "offset": offset,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )
