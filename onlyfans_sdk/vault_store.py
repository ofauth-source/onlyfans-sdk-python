"""
Vault+ Store API
"""
from typing import Any, Dict, List, Literal, Optional, Union, Generator

from ._client import OFAuthClient

def create_v2_vault_plus_store_list(
    client: OFAuthClient,
    connection_id: str,
    list_id: str
) -> Dict[str, Any]:
    """
    Store all media from a vault list
    Queue storage of all media items from a specific vault list
    """
    path = f"/v2/vault-plus/store/list/{list_id}"
    return client.request(
        "POST",
        path,
        connection_id=connection_id,
    )
