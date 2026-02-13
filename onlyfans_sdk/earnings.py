"""
Earnings API
"""
from typing import Any, Dict, List, Literal, Optional, Union, Generator

from ._client import OFAuthClient
from .models import (
    V2AccessEarningsChargebacksGetResponse,
    V2AccessEarningsChartGetResponse,
    V2AccessEarningsTransactionsGetResponse,
)

def list_charts(
    client: OFAuthClient,
    start_date: Optional[Union[str, Any]] = None,
    end_date: Optional[Union[str, Any]] = None,
    by: Optional[Literal["total", "messages", "tips", "stream", "post", "subscribes", "tips_profile", "tips_post", "tips_chat", "tips_stream", "tips_story", "ref"]] = None,
    with_total: Optional[bool] = None,
    monthly_total: Optional[bool] = None
) -> V2AccessEarningsChartGetResponse:
    """
    Get earnings chart
    Get time-series earnings data

**Permission Required:** `earnings:read`
    """
    path = f"/v2/access/earnings/chart"
    query = {
        "startDate": start_date,
        "endDate": end_date,
        "by": by,
        "withTotal": with_total,
        "monthlyTotal": monthly_total,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def list_transactions(
    client: OFAuthClient,
    start_date: Optional[str] = None,
    marker: Optional[str] = None,
    type: Optional[Literal["subscribes", "chat_messages", "post", "stream", "tips"]] = None,
    tips_source: Optional[Literal["chat", "post_all", "profile", "story", "stream"]] = None
) -> V2AccessEarningsTransactionsGetResponse:
    """
    List transactions
    Get a list of earnings transactions

**Permission Required:** `earnings:read`
    """
    path = f"/v2/access/earnings/transactions"
    query = {
        "startDate": start_date,
        "marker": marker,
        "type": type,
        "tipsSource": tips_source,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def iter_transactions(
    client: OFAuthClient,
    start_date: Optional[str] = None,
    type: Optional[Literal["subscribes", "chat_messages", "post", "stream", "tips"]] = None,
    tips_source: Optional[Literal["chat", "post_all", "profile", "story", "stream"]] = None,
    page_size: int = 20,
    max_items: Optional[int] = None
) -> Generator[Any, None, None]:
    """
    List transactions
    
    Returns a generator that yields items one at a time, automatically
    handling pagination.
    
    Args:
        max_items: Maximum total items to yield (default: unlimited)
    
    Yields:
        Individual items from the list response
    
    Example:
        for item in iter_transactions(client, connection_id="..."):
            print(item)
    """
    marker = None
    fetched = 0
    
    while True:
        if max_items is not None and fetched >= max_items:
            return
        
        response = list_transactions(
            client=client,
            start_date=start_date,
            type=type,
            tips_source=tips_source,
            marker=marker,
        )
        
        for item in response.get("list", []):
            if max_items is not None and fetched >= max_items:
                return
            yield item
            fetched += 1
        
        if not response.get("hasMore", False):
            return
        
        marker = response.get("marker")

def list_chargebacks(
    client: OFAuthClient,
    start_date: Optional[Union[str, Any]] = None,
    end_date: Optional[Union[str, Any]] = None,
    marker: Optional[str] = None
) -> V2AccessEarningsChargebacksGetResponse:
    """
    List chargebacks
    Get a list of chargebacks

**Permission Required:** `earnings:read`
    """
    path = f"/v2/access/earnings/chargebacks"
    query = {
        "startDate": start_date,
        "endDate": end_date,
        "marker": marker,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def iter_chargebacks(
    client: OFAuthClient,
    start_date: Optional[Union[str, Any]] = None,
    end_date: Optional[Union[str, Any]] = None,
    page_size: int = 20,
    max_items: Optional[int] = None
) -> Generator[Any, None, None]:
    """
    List chargebacks
    
    Returns a generator that yields items one at a time, automatically
    handling pagination.
    
    Args:
        max_items: Maximum total items to yield (default: unlimited)
    
    Yields:
        Individual items from the list response
    
    Example:
        for item in iter_chargebacks(client, connection_id="..."):
            print(item)
    """
    marker = None
    fetched = 0
    
    while True:
        if max_items is not None and fetched >= max_items:
            return
        
        response = list_chargebacks(
            client=client,
            start_date=start_date,
            end_date=end_date,
            marker=marker,
        )
        
        for item in response.get("list", []):
            if max_items is not None and fetched >= max_items:
                return
            yield item
            fetched += 1
        
        if not response.get("hasMore", False):
            return
        
        marker = response.get("marker")
