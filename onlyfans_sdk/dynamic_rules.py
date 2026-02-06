"""
Dynamic Rules API
"""
from typing import Any, Dict, List, Literal, Optional, Union, Generator

from ._client import OFAuthClient
from .models import (
    V2DynamicRulesGetResponse,
    V2DynamicRulesSignPostRequest,
    V2DynamicRulesSignPostResponse,
    V2DynamicRulesStatusGetResponse,
)

def list_v2_dynamic_rules(
    client: OFAuthClient
) -> V2DynamicRulesGetResponse:
    """
    Get dynamic rules
    
    """
    path = f"/v2/dynamic-rules"
    return client.request(
        "GET",
        path,
    )

def create_v2_dynamic_rules_sign(
    client: OFAuthClient,
    body: V2DynamicRulesSignPostRequest
) -> V2DynamicRulesSignPostResponse:
    """
    Generate sign headers for a request
    
    """
    path = f"/v2/dynamic-rules/sign"
    return client.request(
        "POST",
        path,
        body=body,
    )

def list_v2_dynamic_rules_status(
    client: OFAuthClient
) -> V2DynamicRulesStatusGetResponse:
    """
    Get dynamic rules status
    
    """
    path = f"/v2/dynamic-rules/status"
    return client.request(
        "GET",
        path,
    )
