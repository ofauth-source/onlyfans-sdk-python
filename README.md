# OnlyFans API - Python SDK

[![PyPI](https://img.shields.io/pypi/v/onlyfans-sdk)](https://pypi.org/project/onlyfans-sdk/)
[![Python](https://img.shields.io/pypi/pyversions/onlyfans-sdk)](https://pypi.org/project/onlyfans-sdk/)
[![License](https://img.shields.io/pypi/l/onlyfans-sdk)](LICENSE)

The official **OnlyFans API Python SDK** by [OFAuth](https://ofauth.com). A type-safe Python client for integrating with the OnlyFans API, featuring Pydantic v2 models for full type safety. Build OnlyFans tools, dashboards, analytics, and automations in Python.

> **What is this?** This is an SDK for the [OnlyFans API](https://ofauth.com) via OFAuth — the only authorized way to programmatically access OnlyFans data. Use it to build OnlyFans integrations, manage creator accounts, access earnings data, automate messaging, and more.

## Installation

```bash
pip install onlyfans-sdk
```

## Quick Start

```python
from onlyfans_sdk import OFAuthClient, account

client = OFAuthClient(api_key="your-api-key")

result = account.whoami(client)
print(result)
```

## Features

- Type safety with generated Pydantic v2 models
- Functional API design (module-level functions, pass client as first arg)
- Built-in pagination iterators (generators)
- Proxy support for direct OnlyFans API access
- Media upload with automatic chunked uploads
- Webhook verification and routing (Svix-compatible, Flask + FastAPI helpers)
- Context manager support (`with` statement)
- httpx-powered HTTP client

## Configuration

```python
from onlyfans_sdk import OFAuthClient

# Basic
client = OFAuthClient(api_key="your-api-key")

# With default connection ID (for access API calls)
client = OFAuthClient(
    api_key="your-api-key",
    connection_id="conn_xxx",
)

# Full configuration
client = OFAuthClient(
    api_key="your-api-key",
    connection_id="conn_xxx",
    base_url="https://api-next.ofauth.com",
    timeout=30.0,
)
```

Context manager support:

```python
with OFAuthClient(api_key="your-api-key") as client:
    result = account.whoami(client)
    # client.close() called automatically
```

## Usage Examples

### Account Operations

```python
from onlyfans_sdk import OFAuthClient, account

client = OFAuthClient(api_key="your-api-key")

# Get account info
info = account.whoami(client)
print(info["id"], info["permissions"])

# List connections
connections = account.list_connections(client, status="active", limit=10)
for conn in connections["list"]:
    print(f"{conn['id']}: {conn['userData']['username']} ({conn['status']})")

# Get connection settings
settings = account.get_connection_settings(client, connection_id="conn_xxx")
```

### Access API (OnlyFans Data)

Access endpoints require a `connection_id`, set on the client or per-call:

```python
from onlyfans_sdk import OFAuthClient, posts, earnings, subscribers
from onlyfans_sdk import self as self_module  # 'self' is a Python keyword

client = OFAuthClient(api_key="your-api-key", connection_id="conn_xxx")

# Get creator profile
profile = self_module.list_selfs(client)
print(profile["username"])

# List posts
my_posts = posts.list_posts(client, limit=20, sort_by="publish_date")
for post in my_posts["list"]:
    print(post["id"], post["text"])

# Get earnings data
chart = earnings.list_charts(
    client,
    start_date="2024-01-01",
    end_date="2024-01-31",
    by="total",
)

# List active subscribers
subs = subscribers.list_subscribers(client, type="active", limit=50)
for sub in subs["list"]:
    print(sub)
```

### Pagination

Paginated endpoints have `iter_*` generator variants that handle pagination automatically:

```python
from onlyfans_sdk import OFAuthClient, account, subscribers

client = OFAuthClient(api_key="your-api-key", connection_id="conn_xxx")

# Iterate over all connections
for connection in account.iter_connections(client):
    print(connection["id"])

# With limits
for subscriber in subscribers.iter_subscribers(client, max_items=100, page_size=20):
    print(subscriber)

# Iterate transactions
from onlyfans_sdk import earnings

for tx in earnings.iter_transactions(client, type="tips"):
    print(tx)
```

### Proxy Requests

Call any OnlyFans API endpoint through the OFAuth proxy:

```python
client = OFAuthClient(api_key="your-api-key")

# GET request
user = client.proxy("/users/me", connection_id="conn_xxx")

# POST request with body
response = client.proxy(
    "/messages/queue",
    method="POST",
    connection_id="conn_xxx",
    body={"text": "Hello!", "lockedText": False},
)

# With query parameters
subs = client.proxy(
    "/subscriptions/subscribers",
    connection_id="conn_xxx",
    query={"limit": 10},
)
```

### Media Upload

Handles single-part and multi-part uploads automatically:

```python
client = OFAuthClient(api_key="your-api-key")

with open("video.mp4", "rb") as f:
    result = client.upload_media(
        connection_id="conn_xxx",
        filename="video.mp4",
        file=f,
        mime_type="video/mp4",
        on_progress=lambda uploaded, total: print(f"{uploaded}/{total}"),
    )

print(result["mediaId"])
```

## Error Handling

```python
from onlyfans_sdk import OFAuthClient, OFAuthError, account

client = OFAuthClient(api_key="your-api-key")

try:
    result = account.whoami(client)
except OFAuthError as e:
    print(f"API Error {e.status}: {e}")
    print(f"Error code: {e.code}")
    print(f"Details: {e.details}")
```

## Webhooks

Svix-compatible HMAC-SHA256 webhook verification with built-in routing:

```python
from onlyfans_sdk.webhooks import create_webhook_router

router = create_webhook_router(secret="whsec_...")

def handle_connection_created(event):
    conn = event["data"]["connection"]
    print(f"New connection: {conn['id']} ({conn['userData']['username']})")

def handle_connection_expired(event):
    print(f"Connection expired: {event['data']['connection']['id']}")

router.on("connection.created", handle_connection_created)
router.on("connection.expired", handle_connection_expired)
```

### Flask Integration

```python
from flask import Flask
from onlyfans_sdk.webhooks import create_webhook_router, create_flask_webhook_handler

app = Flask(__name__)
router = create_webhook_router(secret="whsec_...")
# ... register handlers ...

handler = create_flask_webhook_handler(router)
app.add_url_rule("/webhooks", view_func=handler, methods=["POST"])
```

### FastAPI Integration

```python
from fastapi import FastAPI, Request
from onlyfans_sdk.webhooks import create_webhook_router, create_fastapi_webhook_handler

app = FastAPI()
router = create_webhook_router(secret="whsec_...")
# ... register handlers ...

handle_webhook = create_fastapi_webhook_handler(router)

@app.post("/webhooks")
async def webhook(request: Request):
    return await handle_webhook(request)
```

### Manual Verification

```python
from onlyfans_sdk.webhooks import verify_webhook_payload

event = verify_webhook_payload(
    payload=request_body,
    headers=request_headers,
    secret="whsec_...",
)
print(event["eventType"], event["data"])
```

## Type Safety with Pydantic Models

All response types are available as generated Pydantic v2 models:

```python
from onlyfans_sdk import models

# Models are generated from the OpenAPI spec:
# models.V2AccountWhoamiGetResponse
# models.V2AccountConnectionsGetResponse
# models.V2AccessPostsGetResponse
# models.V2AccessEarningsChartGetResponse
# models.V2AccessSubscribersGetResponse
# etc.
```

## Available API Modules

| Module | Description |
|--------|-------------|
| `account` | Account info, connections, organization settings |
| `self` | Creator profile, notifications, release forms |
| `earnings` | Earnings charts, transactions, chargebacks |
| `analytics` | Posts, stories, streams analytics |
| `posts` | Post management (CRUD) |
| `messages` | Chat and messaging |
| `subscribers` | Subscriber data, notes, discounts |
| `subscriptions` | Subscription management |
| `promotions` | Promotions and tracking links |
| `users` | User operations |
| `user_lists` | User list management |
| `vault` | Vault media management |
| `vault_lists` | Vault list management |
| `vault_store` | Vault+ (store) |
| `vault_stats` | Vault statistics |
| `vault_media` | Vault media operations |
| `upload` | Media upload (init, chunk, complete) |
| `link` | Link management |
| `dynamic_rules` | Dynamic rules |
| `webhooks` | Webhook verification and routing |

## License

Apache-2.0
