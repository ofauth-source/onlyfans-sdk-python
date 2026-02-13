"""
Upload API
"""
from typing import Any, Dict, List, Literal, Optional, Union, Generator

from ._client import OFAuthClient
from .models import (
    V2AccessUploadsCheckPostRequest,
    V2AccessUploadsCheckPostResponse,
    V2AccessUploadsCompletePostRequest,
    V2AccessUploadsCompletePostResponse,
    V2AccessUploadsInitPostRequest,
    V2AccessUploadsInitPostResponse,
)

def create_uploads_uploads_check(
    client: OFAuthClient,
    body: V2AccessUploadsCheckPostRequest
) -> V2AccessUploadsCheckPostResponse:
    """
    Check if media already exists in vault
    Check if media already exists in vault

**Permission Required:** `vault:write`
    """
    path = f"/v2/access/uploads/check"
    return client.request(
        "POST",
        path,
        body=body,
    )

def init_uploads(
    client: OFAuthClient,
    body: V2AccessUploadsInitPostRequest
) -> V2AccessUploadsInitPostResponse:
    """
    Initialize media upload
    Initialize media upload

**Permission Required:** `vault:write`
    """
    path = f"/v2/access/uploads/init"
    return client.request(
        "POST",
        path,
        body=body,
    )

def replace_uploads_uploads_parts(
    client: OFAuthClient,
    media_upload_id: str,
    part_number: int
) -> Dict[str, Any]:
    """
    Upload chunk to managed media upload
    Upload chunk to managed media upload

**Permission Required:** `vault:write`
    """
    path = f"/v2/access/uploads/{media_upload_id}/parts/{part_number}"
    return client.request(
        "PUT",
        path,
    )

def replace_uploads(
    client: OFAuthClient,
    media_upload_id: str
) -> Dict[str, Any]:
    """
    Upload single-part media and finalize (No need to call /complete after upload if using this endpoint)
    Upload single-part media and finalize (No need to call /complete after upload if using this endpoint)

**Permission Required:** `vault:write`
    """
    path = f"/v2/access/uploads/{media_upload_id}"
    return client.request(
        "PUT",
        path,
    )

def complete_uploads(
    client: OFAuthClient,
    body: V2AccessUploadsCompletePostRequest
) -> V2AccessUploadsCompletePostResponse:
    """
    Finalize media upload
    Finalize media upload

**Permission Required:** `vault:write`
    """
    path = f"/v2/access/uploads/complete"
    return client.request(
        "POST",
        path,
        body=body,
    )
