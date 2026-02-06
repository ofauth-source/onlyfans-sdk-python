"""
Link API
"""
from typing import Any, Dict, List, Literal, Optional, Union, Generator

from ._client import OFAuthClient
from .models import (
    V2LinkInitPostRequest,
    V2LinkInitPostResponse,
)

def init_v2_link(
    client: OFAuthClient,
    body: V2LinkInitPostRequest
) -> V2LinkInitPostResponse:
    """
    Initialize a Link session
    Initialize a hosted Link session for authentication.
    """
    path = f"/v2/link/init"
    return client.request(
        "POST",
        path,
        body=body,
    )

def get_v2_link(
    client: OFAuthClient,
    client_secret: str
) -> Dict[str, Any]:
    """
    Get login status
    Poll for login status
    """
    path = f"/v2/link/{client_secret}"
    return client.request(
        "GET",
        path,
    )

def delete_v2_link(
    client: OFAuthClient,
    client_secret: str
) -> Dict[str, Any]:
    """
    Delete login session
    Delete login session
    """
    path = f"/v2/link/{client_secret}"
    return client.request(
        "DELETE",
        path,
    )
