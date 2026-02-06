#!/usr/bin/env python3
"""
OFAuth Python SDK - Comprehensive Sandbox Test

This example tests all major API endpoints against the sandbox environment.
Run with your sandbox credentials to verify complete SDK functionality.

Environment:
    OFAUTH_API_KEY: Your sandbox API key (sk_sandbox_...)
    OFAUTH_CONNECTION_ID: Your sandbox connection ID
    OFAUTH_BASE_URL: Base URL (default: http://localhost:8789)
"""
import json
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# SDK imports
from onlyfans_sdk import OFAuthClient, OFAuthError
from onlyfans_sdk import account
from onlyfans_sdk import self as self_api
from onlyfans_sdk import posts
from onlyfans_sdk import messages
from onlyfans_sdk import subscribers
from onlyfans_sdk import subscriptions
from onlyfans_sdk import users
from onlyfans_sdk import user_lists
from onlyfans_sdk import vault
from onlyfans_sdk import vault_lists
from onlyfans_sdk import earnings
from onlyfans_sdk import analytics
from onlyfans_sdk import promotions

import os

API_KEY = os.environ.get("OFAUTH_API_KEY")
CONNECTION_ID = os.environ.get("OFAUTH_CONNECTION_ID")
BASE_URL = os.environ.get("OFAUTH_BASE_URL", "https://api.ofauth.com")

if not API_KEY or not CONNECTION_ID:
    print("Missing required environment variables:")
    print("  OFAUTH_API_KEY - Your OFAuth API key")
    print("  OFAUTH_CONNECTION_ID - Your connection ID")
    print("  OFAUTH_BASE_URL - (optional) API base URL")
    sys.exit(1)


class TestResult:
    """Track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors: List[Dict[str, Any]] = []
    
    def success(self, name: str, data: Any = None):
        self.passed += 1
        print(f"  ✓ {name}")
        if data and isinstance(data, dict):
            # Print key response fields for verification
            for key in ['id', 'username', 'name', 'status', 'list', 'hasMore']:
                if key in data:
                    val = data[key]
                    if key == 'list':
                        print(f"    → {key}: [{len(val)} items]")
                    elif isinstance(val, str) and len(val) > 50:
                        print(f"    → {key}: {val[:50]}...")
                    else:
                        print(f"    → {key}: {val}")
    
    def fail(self, name: str, error: Exception):
        self.failed += 1
        self.errors.append({"test": name, "error": str(error)})
        print(f"  ✗ {name}: {error}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Results: {self.passed}/{total} passed")
        if self.failed > 0:
            print(f"\nFailed tests:")
            for err in self.errors:
                print(f"  - {err['test']}: {err['error']}")
        return self.failed == 0


def test_account_api(client: OFAuthClient, results: TestResult):
    """Test Account API endpoints"""
    print("\n📋 Account API")
    print("-" * 40)
    
    # whoami
    try:
        data = account.whoami(client)
        results.success("whoami", data)
    except Exception as e:
        results.fail("whoami", e)
    
    # list_connections
    try:
        data = account.list_connections(client)
        results.success("list_connections", data)
    except Exception as e:
        results.fail("list_connections", e)
    
    # get_connection_settings
    try:
        data = account.get_connection_settings(client, CONNECTION_ID)
        results.success("get_connection_settings", data)
    except Exception as e:
        results.fail("get_connection_settings", e)
    
    # get_org_settings
    try:
        data = account.get_org_settings(client)
        results.success("get_org_settings", data)
    except Exception as e:
        results.fail("get_org_settings", e)


def test_self_api(client: OFAuthClient, results: TestResult):
    """Test Self/Profile API endpoints"""
    print("\n👤 Self API")
    print("-" * 40)
    
    # get current user (list_selfs)
    try:
        data = self_api.list_selfs(client)
        results.success("list_selfs (get current user)", data)
    except Exception as e:
        results.fail("list_selfs", e)
    
    # list_notifications
    try:
        data = self_api.list_notifications(client, limit=10)
        results.success("list_notifications", data)
    except Exception as e:
        results.fail("list_notifications", e)
    
    # list_release_forms
    try:
        data = self_api.list_release_forms(client, limit=10)
        results.success("list_release_forms", data)
    except Exception as e:
        results.fail("list_release_forms", e)
    
    # list_tagged_friend_users
    try:
        data = self_api.list_tagged_friend_users(client, limit=10)
        results.success("list_tagged_friend_users", data)
    except Exception as e:
        results.fail("list_tagged_friend_users", e)


def test_posts_api(client: OFAuthClient, results: TestResult):
    """Test Posts API endpoints"""
    print("\n📝 Posts API")
    print("-" * 40)
    
    # list_posts
    try:
        data = posts.list_posts(client, limit=10)
        results.success("list_posts", data)
        
        # If we have posts, get one by ID
        if data.get("list") and len(data["list"]) > 0:
            post_id = str(data["list"][0].get("id"))
            try:
                post_data = posts.get_posts(client, post_id)
                results.success(f"get_posts (id={post_id})", post_data)
            except Exception as e:
                results.fail(f"get_posts (id={post_id})", e)
    except Exception as e:
        results.fail("list_posts", e)


def test_messages_api(client: OFAuthClient, results: TestResult):
    """Test Messages API endpoints"""
    print("\n💬 Messages API")
    print("-" * 40)
    
    # list_chats
    try:
        data = messages.list_chats(client, limit=10)
        results.success("list_chats", data)
        
        # If we have chats, get messages from one
        if data.get("list") and len(data["list"]) > 0:
            user_id = str(data["list"][0].get("withUser", {}).get("id", ""))
            if user_id:
                try:
                    msgs = messages.list_chats_chats_messages(client, user_id, limit=10)
                    results.success(f"list_chats_chats_messages (user_id={user_id})", msgs)
                except Exception as e:
                    results.fail(f"list_chats_chats_messages (user_id={user_id})", e)
    except Exception as e:
        results.fail("list_chats", e)
    
    # list_mass_messages
    try:
        data = messages.list_mass_messages(client, limit=10)
        results.success("list_mass_messages", data)
    except Exception as e:
        results.fail("list_mass_messages", e)


def test_subscribers_api(client: OFAuthClient, results: TestResult):
    """Test Subscribers API endpoints"""
    print("\n👥 Subscribers API")
    print("-" * 40)
    
    # list_subscribers - all
    try:
        data = subscribers.list_subscribers(client, type="all", limit=10)
        results.success("list_subscribers (all)", data)
    except Exception as e:
        results.fail("list_subscribers (all)", e)
    
    # list_subscribers - active
    try:
        data = subscribers.list_subscribers(client, type="active", limit=10)
        results.success("list_subscribers (active)", data)
    except Exception as e:
        results.fail("list_subscribers (active)", e)
    
    # list_subscribers - expired
    try:
        data = subscribers.list_subscribers(client, type="expired", limit=10)
        results.success("list_subscribers (expired)", data)
    except Exception as e:
        results.fail("list_subscribers (expired)", e)


def test_subscriptions_api(client: OFAuthClient, results: TestResult):
    """Test Subscriptions API endpoints"""
    print("\n📊 Subscriptions API")
    print("-" * 40)
    
    # list_counts (subscription counts)
    try:
        data = subscriptions.list_counts(client)
        results.success("list_counts (subscription counts)", data)
    except Exception as e:
        results.fail("list_counts", e)
    
    # list_subscriptions
    try:
        data = subscriptions.list_subscriptions(client, limit=10)
        results.success("list_subscriptions", data)
    except Exception as e:
        results.fail("list_subscriptions", e)


def test_users_api(client: OFAuthClient, results: TestResult):
    """Test Users API endpoints"""
    print("\n🔍 Users API")
    print("-" * 40)
    
    # list_blockeds
    try:
        data = users.list_blockeds(client, limit=10)
        results.success("list_blockeds", data)
    except Exception as e:
        results.fail("list_blockeds", e)
    
    # list_restricts
    try:
        data = users.list_restricts(client, limit=10)
        results.success("list_restricts", data)
    except Exception as e:
        results.fail("list_restricts", e)
    
    # list_searchs (search performers)
    try:
        data = users.list_searchs(client, query="test", limit=10)
        results.success("list_searchs (search performers)", data)
    except Exception as e:
        results.fail("list_searchs", e)


def test_user_lists_api(client: OFAuthClient, results: TestResult):
    """Test User Lists API endpoints"""
    print("\n📁 User Lists API")
    print("-" * 40)
    
    # list_users_users_lists
    try:
        data = user_lists.list_users_users_lists(client, limit=10)
        results.success("list_users_users_lists", data)
        
        # If we have lists, get one by ID
        if data.get("list") and len(data["list"]) > 0:
            list_id = str(data["list"][0].get("id"))
            try:
                list_data = user_lists.get_users_users_lists(client, list_id)
                results.success(f"get_users_users_lists (id={list_id})", list_data)
            except Exception as e:
                results.fail(f"get_users_users_lists (id={list_id})", e)
            
            # List users in list
            try:
                users_data = user_lists.list_users_lists_users(client, list_id, limit=10)
                results.success(f"list_users_lists_users (id={list_id})", users_data)
            except Exception as e:
                results.fail(f"list_users_lists_users (id={list_id})", e)
    except Exception as e:
        results.fail("list_users_users_lists", e)


def test_vault_api(client: OFAuthClient, results: TestResult):
    """Test Vault API endpoints"""
    print("\n🗄️ Vault API")
    print("-" * 40)
    
    # list_media
    try:
        data = vault.list_media(client, limit=10)
        results.success("list_media", data)
    except Exception as e:
        results.fail("list_media", e)
    
    # list_vault_vault_lists (vault folders)
    try:
        data = vault_lists.list_vault_vault_lists(client, limit=10)
        results.success("list_vault_vault_lists (vault folders)", data)
    except Exception as e:
        results.fail("list_vault_vault_lists", e)


def test_earnings_api(client: OFAuthClient, results: TestResult):
    """Test Earnings API endpoints"""
    print("\n💰 Earnings API")
    print("-" * 40)
    
    now = datetime.now()
    thirty_days_ago = now - timedelta(days=30)
    start_date = thirty_days_ago.strftime("%Y-%m-%d")
    end_date = now.strftime("%Y-%m-%d")
    
    # list_charts (earnings chart)
    try:
        data = earnings.list_charts(
            client,
            start_date=start_date,
            end_date=end_date
        )
        results.success("list_charts (earnings chart)", data)
    except Exception as e:
        results.fail("list_charts", e)
    
    # list_transactions (only has start_date, uses marker for pagination)
    try:
        data = earnings.list_transactions(
            client,
            start_date=start_date
        )
        results.success("list_transactions", data)
    except Exception as e:
        results.fail("list_transactions", e)
    
    # list_chargebacks
    try:
        data = earnings.list_chargebacks(
            client,
            start_date=start_date,
            end_date=end_date,
            limit=10
        )
        results.success("list_chargebacks", data)
    except Exception as e:
        results.fail("list_chargebacks", e)


def test_analytics_api(client: OFAuthClient, results: TestResult):
    """Test Analytics API endpoints"""
    print("\n📈 Analytics API")
    print("-" * 40)
    
    now = datetime.now()
    thirty_days_ago = now - timedelta(days=30)
    start_date = thirty_days_ago.strftime("%Y-%m-%d")
    end_date = now.strftime("%Y-%m-%d")
    
    # posts_chart
    try:
        data = analytics.list_posts_charts(
            client,
            start_date=start_date,
            end_date=end_date
        )
        results.success("list_posts_charts", data)
    except Exception as e:
        results.fail("list_posts_charts", e)
    
    # top_posts
    try:
        data = analytics.list_posts_tops(
            client,
            start_date=start_date,
            end_date=end_date,
            limit=10
        )
        results.success("list_posts_tops", data)
    except Exception as e:
        results.fail("list_posts_tops", e)
    
    # stories_chart
    try:
        data = analytics.list_stories_charts(
            client,
            start_date=start_date,
            end_date=end_date
        )
        results.success("list_stories_charts", data)
    except Exception as e:
        results.fail("list_stories_charts", e)
    
    # mass_messages_chart
    try:
        data = analytics.list_mass_messages_charts(
            client,
            start_date=start_date,
            end_date=end_date
        )
        results.success("list_mass_messages_charts", data)
    except Exception as e:
        results.fail("list_mass_messages_charts", e)
    
    # visitor_countries_chart
    try:
        data = analytics.list_visitor_countries_charts(
            client,
            start_date=start_date,
            end_date=end_date
        )
        results.success("list_visitor_countries_charts", data)
    except Exception as e:
        results.fail("list_visitor_countries_charts", e)


def test_promotions_api(client: OFAuthClient, results: TestResult):
    """Test Promotions API endpoints"""
    print("\n🎁 Promotions API")
    print("-" * 40)
    
    # list_promotions
    try:
        data = promotions.list_promotions(client, limit=10)
        results.success("list_promotions", data)
    except Exception as e:
        results.fail("list_promotions", e)
    
    # list_tracking_links
    try:
        data = promotions.list_tracking_links(client, limit=10)
        results.success("list_tracking_links", data)
    except Exception as e:
        results.fail("list_tracking_links", e)
    
    # list_trial_links
    try:
        data = promotions.list_trial_links(client, limit=10)
        results.success("list_trial_links", data)
    except Exception as e:
        results.fail("list_trial_links", e)
    
    # list_bundles
    try:
        data = promotions.list_bundles(client, limit=10)
        results.success("list_bundles", data)
    except Exception as e:
        results.fail("list_bundles", e)


def test_proxy_api(client: OFAuthClient, results: TestResult):
    """Test Proxy API (direct OnlyFans requests)"""
    print("\n🔀 Proxy API")
    print("-" * 40)
    
    try:
        data = client.proxy("/users/me", method="GET")
        results.success("proxy /users/me", data)
    except Exception as e:
        results.fail("proxy /users/me", e)


def test_mutation_apis(client: OFAuthClient, results: TestResult):
    """Test Mutation APIs (CRUD Operations)"""
    print("\n✏️ Mutation APIs (CRUD Operations)")
    print("-" * 40)
    
    created_vault_list_id = None
    
    try:
        data = vault_lists.create_vault_vault_lists(
            client,
            body={"name": f"SDK Test List {datetime.now().timestamp()}"}
        )
        created_vault_list_id = data.get("id")
        results.success("vault_lists.create", data)
    except Exception as e:
        results.fail("vault_lists.create", e)
    
    if created_vault_list_id:
        try:
            data = vault_lists.update_vault_vault_lists(
                client,
                list_id=created_vault_list_id,
                body={"name": f"SDK Test List Updated {datetime.now().timestamp()}"}
            )
            results.success("vault_lists.update", data)
        except Exception as e:
            results.fail("vault_lists.update", e)
        
        try:
            data = vault_lists.delete_vault_vault_lists(
                client,
                list_id=created_vault_list_id
            )
            results.success("vault_lists.delete", data)
        except Exception as e:
            results.fail("vault_lists.delete", e)
    
    try:
        data = account.update_connection_settings(
            client,
            connection_id=CONNECTION_ID,
            body={
                "vaultCache": {
                    "enabled": True,
                    "settings": {}
                }
            }
        )
        results.success("account.update_connection_settings", data)
    except Exception as e:
        results.fail("account.update_connection_settings", e)
    
    test_user_id = "12345"
    try:
        data = users.create_restrict(client, user_id=test_user_id)
        results.success("users.create_restrict", data)
    except Exception as e:
        results.fail("users.create_restrict", e)
    
    try:
        data = users.delete_restrict(client, user_id=test_user_id)
        results.success("users.delete_restrict", data)
    except Exception as e:
        results.fail("users.delete_restrict", e)


def main():
    print("=" * 60)
    print("OFAuth Python SDK - Comprehensive Sandbox Test")
    print("=" * 60)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Connection ID: {CONNECTION_ID}")
    print(f"API Key: {API_KEY[:20]}...")
    
    # Create client with sandbox credentials
    client = OFAuthClient(
        api_key=API_KEY,
        base_url=BASE_URL,
        connection_id=CONNECTION_ID
    )
    
    results = TestResult()
    
    try:
        test_account_api(client, results)
        test_self_api(client, results)
        test_posts_api(client, results)
        test_messages_api(client, results)
        test_subscribers_api(client, results)
        test_subscriptions_api(client, results)
        test_users_api(client, results)
        test_user_lists_api(client, results)
        test_vault_api(client, results)
        test_earnings_api(client, results)
        test_analytics_api(client, results)
        test_promotions_api(client, results)
        test_proxy_api(client, results)
        test_mutation_apis(client, results)
        
    finally:
        client.close()
    
    # Print summary
    success = results.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
