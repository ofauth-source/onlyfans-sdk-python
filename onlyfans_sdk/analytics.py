"""
Analytics API
"""
from typing import Any, Dict, List, Literal, Optional, Union, Generator

from ._client import OFAuthClient
from .models import (
    V2AccessAnalyticsCampaignsChartGetResponse,
    V2AccessAnalyticsCampaignsTopGetResponse,
    V2AccessAnalyticsEarningsChargebacksGetResponse,
    V2AccessAnalyticsEarningsChartGetResponse,
    V2AccessAnalyticsEarningsTransactionsGetResponse,
    V2AccessAnalyticsMassMessagesChartGetResponse,
    V2AccessAnalyticsMassMessagesPurchasedGetResponse,
    V2AccessAnalyticsPostsChartGetResponse,
    V2AccessAnalyticsPostsTopGetResponse,
    V2AccessAnalyticsPromotionsChartGetResponse,
    V2AccessAnalyticsPromotionsTopGetResponse,
    V2AccessAnalyticsStoriesChartGetResponse,
    V2AccessAnalyticsStoriesTopGetResponse,
    V2AccessAnalyticsStreamsChartGetResponse,
    V2AccessAnalyticsStreamsTopGetResponse,
    V2AccessAnalyticsTrialsChartGetResponse,
    V2AccessAnalyticsTrialsTopGetResponse,
    V2AccessAnalyticsVisitorCountriesChartGetResponse,
    V2AccessAnalyticsVisitorCountriesTopGetResponse,
)

def list_campaigns_charts(
    client: OFAuthClient,
    start_date: Optional[Union[str, Any]] = None,
    end_date: Optional[Union[str, Any]] = None,
    with_total: Optional[bool] = None
) -> V2AccessAnalyticsCampaignsChartGetResponse:
    """
    Campaigns chart
    Get time-series campaign performance data

**Permission Required:** `analytics:read`
    """
    path = f"/v2/access/analytics/campaigns/chart"
    query = {
        "startDate": start_date,
        "endDate": end_date,
        "withTotal": with_total,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def list_campaigns_tops(
    client: OFAuthClient,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    start_date: Optional[Union[str, Any]] = None,
    end_date: Optional[Union[str, Any]] = None
) -> V2AccessAnalyticsCampaignsTopGetResponse:
    """
    Top campaigns
    Get top performing campaigns

**Permission Required:** `analytics:read`
    """
    path = f"/v2/access/analytics/campaigns/top"
    query = {
        "limit": limit,
        "offset": offset,
        "startDate": start_date,
        "endDate": end_date,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def iter_campaigns_tops(
    client: OFAuthClient,
    start_date: Optional[Union[str, Any]] = None,
    end_date: Optional[Union[str, Any]] = None,
    page_size: int = 20,
    max_items: Optional[int] = None
) -> Generator[Any, None, None]:
    """
    Top campaigns
    
    Returns a generator that yields items one at a time, automatically
    handling pagination.
    
    Args:
        page_size: Number of items per page (default: 20)
        max_items: Maximum total items to yield (default: unlimited)
    
    Yields:
        Individual items from the list response
    
    Example:
        for item in iter_campaigns_tops(client, connection_id="..."):
            print(item)
    """
    offset = 0
    fetched = 0
    
    while True:
        if max_items is not None and fetched >= max_items:
            return
        
        remaining = page_size if max_items is None else min(page_size, max_items - fetched)
        response = list_campaigns_tops(
            client=client,
            start_date=start_date,
            end_date=end_date,
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

def list_earnings_chargebacks(
    client: OFAuthClient,
    start_date: Optional[Union[str, Any]] = None,
    end_date: Optional[Union[str, Any]] = None,
    marker: Optional[str] = None
) -> V2AccessAnalyticsEarningsChargebacksGetResponse:
    """
    Chargebacks
    Get a list of chargebacks

**Permission Required:** `earnings:read`
    """
    path = f"/v2/access/analytics/earnings/chargebacks"
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

def iter_earnings_chargebacks(
    client: OFAuthClient,
    start_date: Optional[Union[str, Any]] = None,
    end_date: Optional[Union[str, Any]] = None,
    page_size: int = 20,
    max_items: Optional[int] = None
) -> Generator[Any, None, None]:
    """
    Chargebacks
    
    Returns a generator that yields items one at a time, automatically
    handling pagination.
    
    Args:
        max_items: Maximum total items to yield (default: unlimited)
    
    Yields:
        Individual items from the list response
    
    Example:
        for item in iter_earnings_chargebacks(client, connection_id="..."):
            print(item)
    """
    marker = None
    fetched = 0
    
    while True:
        if max_items is not None and fetched >= max_items:
            return
        
        response = list_earnings_chargebacks(
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

def list_earnings_charts(
    client: OFAuthClient,
    start_date: Optional[Union[str, Any]] = None,
    end_date: Optional[Union[str, Any]] = None,
    by: Optional[Literal["total", "messages", "tips", "stream", "post", "subscribes", "tips_profile", "tips_post", "tips_chat", "tips_stream", "tips_story", "ref"]] = None,
    with_total: Optional[bool] = None,
    monthly_total: Optional[bool] = None
) -> V2AccessAnalyticsEarningsChartGetResponse:
    """
    Earnings chart
    Get time-series earnings data

**Permission Required:** `earnings:read`
    """
    path = f"/v2/access/analytics/earnings/chart"
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

def list_earnings_transactions(
    client: OFAuthClient,
    start_date: Optional[str] = None,
    marker: Optional[str] = None,
    type: Optional[Literal["subscribes", "chat_messages", "post", "stream", "tips"]] = None,
    tips_source: Optional[Literal["chat", "post_all", "profile", "story", "stream"]] = None
) -> V2AccessAnalyticsEarningsTransactionsGetResponse:
    """
    Transactions
    Get a list of earnings transactions

**Permission Required:** `earnings:read`
    """
    path = f"/v2/access/analytics/earnings/transactions"
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

def iter_earnings_transactions(
    client: OFAuthClient,
    start_date: Optional[str] = None,
    type: Optional[Literal["subscribes", "chat_messages", "post", "stream", "tips"]] = None,
    tips_source: Optional[Literal["chat", "post_all", "profile", "story", "stream"]] = None,
    page_size: int = 20,
    max_items: Optional[int] = None
) -> Generator[Any, None, None]:
    """
    Transactions
    
    Returns a generator that yields items one at a time, automatically
    handling pagination.
    
    Args:
        max_items: Maximum total items to yield (default: unlimited)
    
    Yields:
        Individual items from the list response
    
    Example:
        for item in iter_earnings_transactions(client, connection_id="..."):
            print(item)
    """
    marker = None
    fetched = 0
    
    while True:
        if max_items is not None and fetched >= max_items:
            return
        
        response = list_earnings_transactions(
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

def list_mass_messages_buyers(
    client: OFAuthClient,
    mass_message_id: str,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    marker: Optional[int] = None
) -> Dict[str, Any]:
    """
    Mass message buyers
    Get list of users who purchased a specific mass message

**Permission Required:** `analytics:read`
    """
    path = f"/v2/access/analytics/mass-messages/{mass_message_id}/buyers"
    query = {
        "limit": limit,
        "offset": offset,
        "marker": marker,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def iter_mass_messages_buyers(
    client: OFAuthClient,
    mass_message_id: str,
    page_size: int = 20,
    max_items: Optional[int] = None
) -> Generator[Any, None, None]:
    """
    Mass message buyers
    
    Returns a generator that yields items one at a time, automatically
    handling pagination.
    
    Args:
        max_items: Maximum total items to yield (default: unlimited)
    
    Yields:
        Individual items from the list response
    
    Example:
        for item in iter_mass_messages_buyers(client, connection_id="..."):
            print(item)
    """
    marker = None
    fetched = 0
    
    while True:
        if max_items is not None and fetched >= max_items:
            return
        
        response = list_mass_messages_buyers(
            client=client,
            mass_message_id=mass_message_id,
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

def list_mass_messages_charts(
    client: OFAuthClient,
    start_date: Optional[Union[str, Any]] = None,
    end_date: Optional[Union[str, Any]] = None,
    with_total: Optional[bool] = None
) -> V2AccessAnalyticsMassMessagesChartGetResponse:
    """
    Mass messages chart
    Get time-series mass message performance data

**Permission Required:** `analytics:read`
    """
    path = f"/v2/access/analytics/mass-messages/chart"
    query = {
        "startDate": start_date,
        "endDate": end_date,
        "withTotal": with_total,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def list_mass_messages_purchaseds(
    client: OFAuthClient,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> V2AccessAnalyticsMassMessagesPurchasedGetResponse:
    """
    Mass messages purchased
    Get list of mass messages that were purchased

**Permission Required:** `analytics:read`
    """
    path = f"/v2/access/analytics/mass-messages/purchased"
    query = {
        "limit": limit,
        "offset": offset,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def get_posts(
    client: OFAuthClient,
    post_id: str
) -> Dict[str, Any]:
    """
    Post stats
    Get detailed stats for a specific post

**Permission Required:** `analytics:read`
    """
    path = f"/v2/access/analytics/posts/{post_id}"
    return client.request(
        "GET",
        path,
    )

def list_posts_charts(
    client: OFAuthClient,
    start_date: Optional[Union[str, Any]] = None,
    end_date: Optional[Union[str, Any]] = None,
    with_total: Optional[bool] = None,
    by: Optional[Literal["purchases", "posts", "tips", "views", "likes", "comments"]] = None
) -> V2AccessAnalyticsPostsChartGetResponse:
    """
    Posts chart
    Get time-series post performance data

**Permission Required:** `analytics:read`
    """
    path = f"/v2/access/analytics/posts/chart"
    query = {
        "startDate": start_date,
        "endDate": end_date,
        "withTotal": with_total,
        "by": by,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def list_posts_tops(
    client: OFAuthClient,
    by: Optional[Literal["purchases", "tips", "views", "likes", "comments"]] = None,
    start_date: Optional[Union[str, Any]] = None,
    end_date: Optional[Union[str, Any]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> V2AccessAnalyticsPostsTopGetResponse:
    """
    Top posts
    Get top performing posts

**Permission Required:** `analytics:read`
    """
    path = f"/v2/access/analytics/posts/top"
    query = {
        "by": by,
        "startDate": start_date,
        "endDate": end_date,
        "limit": limit,
        "offset": offset,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def list_promotions_charts(
    client: OFAuthClient,
    start_date: Optional[Union[str, Any]] = None,
    end_date: Optional[Union[str, Any]] = None,
    with_total: Optional[bool] = None
) -> V2AccessAnalyticsPromotionsChartGetResponse:
    """
    Promotions chart
    Get time-series promotion performance data

**Permission Required:** `analytics:read`
    """
    path = f"/v2/access/analytics/promotions/chart"
    query = {
        "startDate": start_date,
        "endDate": end_date,
        "withTotal": with_total,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def list_promotions_tops(
    client: OFAuthClient,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    start_date: Optional[Union[str, Any]] = None,
    end_date: Optional[Union[str, Any]] = None
) -> V2AccessAnalyticsPromotionsTopGetResponse:
    """
    Top promotions
    Get top performing promotions

**Permission Required:** `analytics:read`
    """
    path = f"/v2/access/analytics/promotions/top"
    query = {
        "limit": limit,
        "offset": offset,
        "startDate": start_date,
        "endDate": end_date,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def list_stories_charts(
    client: OFAuthClient,
    start_date: Optional[Union[str, Any]] = None,
    end_date: Optional[Union[str, Any]] = None,
    with_total: Optional[bool] = None,
    by: Optional[Literal["tips", "stories", "views", "likes", "comments"]] = None
) -> V2AccessAnalyticsStoriesChartGetResponse:
    """
    Stories chart
    Get time-series story performance data

**Permission Required:** `analytics:read`
    """
    path = f"/v2/access/analytics/stories/chart"
    query = {
        "startDate": start_date,
        "endDate": end_date,
        "withTotal": with_total,
        "by": by,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def list_stories_tops(
    client: OFAuthClient,
    by: Optional[Literal["tips", "views", "likes", "comments"]] = None,
    start_date: Optional[Union[str, Any]] = None,
    end_date: Optional[Union[str, Any]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> V2AccessAnalyticsStoriesTopGetResponse:
    """
    Top stories
    Get top performing stories

**Permission Required:** `analytics:read`
    """
    path = f"/v2/access/analytics/stories/top"
    query = {
        "by": by,
        "startDate": start_date,
        "endDate": end_date,
        "limit": limit,
        "offset": offset,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def list_streams_charts(
    client: OFAuthClient,
    start_date: Optional[Union[str, Any]] = None,
    end_date: Optional[Union[str, Any]] = None,
    with_total: Optional[bool] = None,
    by: Optional[Literal["purchases", "duration", "tips", "views", "likes", "comments"]] = None
) -> V2AccessAnalyticsStreamsChartGetResponse:
    """
    Streams chart
    Get time-series stream performance data

**Permission Required:** `analytics:read`
    """
    path = f"/v2/access/analytics/streams/chart"
    query = {
        "startDate": start_date,
        "endDate": end_date,
        "withTotal": with_total,
        "by": by,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def list_streams_tops(
    client: OFAuthClient,
    by: Optional[Literal["purchases", "duration", "tips", "views", "likes", "comments"]] = None,
    start_date: Optional[Union[str, Any]] = None,
    end_date: Optional[Union[str, Any]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> V2AccessAnalyticsStreamsTopGetResponse:
    """
    Top streams
    Get top performing streams

**Permission Required:** `analytics:read`
    """
    path = f"/v2/access/analytics/streams/top"
    query = {
        "by": by,
        "startDate": start_date,
        "endDate": end_date,
        "limit": limit,
        "offset": offset,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def list_trials_charts(
    client: OFAuthClient,
    start_date: Optional[Union[str, Any]] = None,
    end_date: Optional[Union[str, Any]] = None,
    with_total: Optional[bool] = None
) -> V2AccessAnalyticsTrialsChartGetResponse:
    """
    Trials chart
    Get time-series trial link performance data

**Permission Required:** `analytics:read`
    """
    path = f"/v2/access/analytics/trials/chart"
    query = {
        "startDate": start_date,
        "endDate": end_date,
        "withTotal": with_total,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def list_trials_tops(
    client: OFAuthClient,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    start_date: Optional[Union[str, Any]] = None,
    end_date: Optional[Union[str, Any]] = None
) -> V2AccessAnalyticsTrialsTopGetResponse:
    """
    Top trials
    Get top performing trial links

**Permission Required:** `analytics:read`
    """
    path = f"/v2/access/analytics/trials/top"
    query = {
        "limit": limit,
        "offset": offset,
        "startDate": start_date,
        "endDate": end_date,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def list_visitor_countries_charts(
    client: OFAuthClient,
    start_date: Optional[Union[str, Any]] = None,
    end_date: Optional[Union[str, Any]] = None,
    by: Optional[Literal["guests", "total", "users"]] = None
) -> V2AccessAnalyticsVisitorCountriesChartGetResponse:
    """
    Visitor countries chart
    Get time-series visitor country data

**Permission Required:** `analytics:read`
    """
    path = f"/v2/access/analytics/visitor-countries/chart"
    query = {
        "startDate": start_date,
        "endDate": end_date,
        "by": by,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )

def list_visitor_countries_tops(
    client: OFAuthClient,
    start_date: Optional[Union[str, Any]] = None,
    end_date: Optional[Union[str, Any]] = None,
    by: Optional[Literal["guests", "total", "users"]] = None
) -> V2AccessAnalyticsVisitorCountriesTopGetResponse:
    """
    Top visitor countries
    Get top visitor countries

**Permission Required:** `analytics:read`
    """
    path = f"/v2/access/analytics/visitor-countries/top"
    query = {
        "startDate": start_date,
        "endDate": end_date,
        "by": by,
    }
    return client.request(
        "GET",
        path,
        query=query,
    )
