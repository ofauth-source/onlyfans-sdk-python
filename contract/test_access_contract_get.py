import json
import os
import re
import time
from pathlib import Path
import sys

import pytest

PYTHON_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_PACKAGE_ROOT))

from onlyfans_sdk._client import OFAuthClient, OFAuthError


MANIFEST_PATH = Path(__file__).with_name("accessEndpoints.manifest.json")


def _load_dotenv_local() -> None:
    # Optional convenience: load `.env.e2e.local` from current or parent dirs if present,
    # without overriding already-set environment variables.
    for rel in [
        ".env.e2e.local",
        "../.env.e2e.local",
        "../../.env.e2e.local",
        "../../../.env.e2e.local",
        "../../../../.env.e2e.local",
    ]:
        p = Path(rel)
        if not p.exists():
            continue
        for line in p.read_text("utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if not key:
                continue
            if len(value) >= 2 and (
                (value[0] == value[-1] == '"') or (value[0] == value[-1] == "'")
            ):
                value = value[1:-1]
            # Only set if the variable is truly unset. This allows callers to explicitly
            # disable contexts by setting empty strings in the environment.
            if key not in os.environ:
                os.environ[key] = value
        return


def _load_manifest():
    raw = MANIFEST_PATH.read_text("utf-8")
    manifest = json.loads(raw)
    assert isinstance(manifest, list)
    assert len(manifest) > 20
    return manifest


def _is_likely_malformed_json(text: str) -> bool:
    return re.search(r"\"url\"\\s*:\\s*\"{3,}", text) is not None


def _default_query(route: str, fixtures: dict[str, str] | None = None):
    if route == "/users/search":
        return {"query": "test"}

    if route == "/users/list":
        user_id = (fixtures or {}).get("userId")
        if not user_id:
            return None
        return {"userIds": user_id}

    if route.endswith("/chart"):
        return {
            "startDate": "2024-01-01",
            "endDate": "2024-01-31",
            "withTotal": True,
        }

    if route.endswith("/top"):
        return {
            "startDate": "2024-01-01",
            "endDate": "2024-01-31",
            "limit": 1,
            "offset": 0,
        }

    if (
        route
        in {
            "/posts",
            "/subscribers",
            "/subscriptions",
            "/chats",
            "/analytics/mass-messages/sent",
            "/analytics/mass-messages/purchased",
            "/earnings/transactions",
            "/earnings/chargebacks",
            "/promotions",
            "/promotions/bundles",
            "/promotions/tracking-links",
            "/promotions/trial-links",
            "/users/blocked",
            "/users/restrict",
            "/users/lists",
            "/vault/media",
            "/vault/lists",
        }
        or route.endswith("/notifications")
        or route.endswith("/release-forms")
        or route.endswith("/tagged-friend-users")
        or route.endswith("/users")
        or route.endswith("/buyers")
    ):
        return {"limit": 1}

    return None


def _route_param_names(route: str):
    return re.findall(r":([A-Za-z0-9_]+)", route)


def _fill_route_params(route: str, params: dict[str, str]) -> str:
    def repl(m):
        key = m.group(1)
        return params.get(key, m.group(0))

    return re.sub(r":([A-Za-z0-9_]+)", repl, route)


def _sleep_until_next(min_delay_ms: int, last_start_at: float) -> float:
    if min_delay_ms <= 0:
        return time.time()
    now = time.time()
    wait_s = max(0.0, (last_start_at + (min_delay_ms / 1000.0)) - now)
    if wait_s > 0:
        time.sleep(wait_s)
    return time.time()


def _env_bool(key: str) -> bool:
    v = (os.getenv(key) or "").strip().lower()
    return v in {"1", "true", "yes", "y"}


def _split_csv(value: str) -> list[str]:
    return [v.strip() for v in (value or "").split(",") if v.strip()]


def _should_run_suite(name: str) -> bool:
    suites = _split_csv(os.getenv("E2E_SDK_SUITES") or "")
    if not suites:
        return True  # default: run getters
    return name in suites


def _as_dict(value: object) -> dict | None:
    return value if isinstance(value, dict) else None


def _as_list(value: object) -> list | None:
    return value if isinstance(value, list) else None


def _self_id(value: object) -> str | None:
    obj = _as_dict(value)
    if not obj:
        return None
    if obj.get("id") is not None:
        return str(obj.get("id"))
    user = _as_dict(obj.get("user")) or _as_dict(obj.get("data"))
    if user and user.get("id") is not None:
        return str(user.get("id"))
    return None


def _first_list_item_id(value: object) -> str | None:
    obj = _as_dict(value)
    if not obj:
        return None
    items = _as_list(obj.get("list")) or _as_list(obj.get("items"))
    if not items:
        return None
    first = _as_dict(items[0])
    if not first:
        return None
    for key in (
        "id",
        "postId",
        "listId",
        "trackingLinkId",
        "trialLinkId",
        "promotionId",
        "bundleId",
        "subscriptionId",
        "massMessageId",
    ):
        if first.get(key) is not None:
            return str(first.get(key))
    return None


def _chat_user_id_from_chats(value: object) -> str | None:
    obj = _as_dict(value)
    if not obj:
        return None
    items = _as_list(obj.get("list")) or _as_list(obj.get("items"))
    if not items:
        return None
    first = _as_dict(items[0])
    if not first:
        return None
    with_user = _as_dict(first.get("withUser")) or _as_dict(first.get("user"))
    if with_user and with_user.get("id") is not None:
        return str(with_user.get("id"))
    for key in ("userId", "withUserId", "id"):
        if first.get(key) is not None:
            return str(first.get(key))
    return None


def _fixture_key_for_route_param(route: str, param_name: str) -> str:
    if param_name == "userId" and route.startswith("/chats/"):
        return "chatUserId"
    if param_name == "listId" and route.startswith("/vault/lists/"):
        return "vaultListId"
    return param_name


@pytest.mark.contract
def test_access_endpoints_manifest_exists():
    manifest = _load_manifest()
    assert any(e.get("method") == "get" and e.get("route") == "/self" for e in manifest)
    assert any(
        e.get("method") == "get" and e.get("route") == "/analytics/posts/top"
        for e in manifest
    )


@pytest.mark.contract
def test_access_get_contract_no_raw_strings_across_contexts():
    if not _should_run_suite("access-get"):
        pytest.skip("suite disabled via E2E_SDK_SUITES")

    _load_dotenv_local()

    manifest = _load_manifest()
    endpoints = [e for e in manifest if (e.get("method") or "").lower() == "get"]
    remaining = {e.get("route") for e in endpoints if isinstance(e.get("route"), str)}

    base_url = os.getenv("E2E_ACCESS_BASE_URL") or ""
    required = _env_bool("E2E_CONTRACT_REQUIRED")
    strict = _env_bool("E2E_CONTRACT_STRICT")
    run_live = _env_bool("E2E_RUN_LIVE")

    contexts = [
        {
            "name": "sandbox-creator",
            "api_key": os.getenv("E2E_SANDBOX_API_KEY_CREATOR") or "",
            "connection_id": os.getenv("E2E_SANDBOX_CONNECTION_ID_CREATOR") or "",
            "min_delay_ms": 0,
        },
        {
            "name": "sandbox-fan",
            "api_key": os.getenv("E2E_SANDBOX_API_KEY_FAN") or "",
            "connection_id": os.getenv("E2E_SANDBOX_CONNECTION_ID_FAN") or "",
            "min_delay_ms": 0,
        },
    ]
    if run_live:
        contexts.extend(
            [
                {
                    "name": "live-creator",
                    "api_key": os.getenv("E2E_LIVE_API_KEY_CREATOR") or "",
                    "connection_id": os.getenv("E2E_LIVE_CONNECTION_ID_CREATOR") or "",
                    "min_delay_ms": 2000,
                },
                {
                    "name": "live-fan",
                    "api_key": os.getenv("E2E_LIVE_API_KEY_FAN") or "",
                    "connection_id": os.getenv("E2E_LIVE_CONNECTION_ID_FAN") or "",
                    "min_delay_ms": 2000,
                },
            ]
        )

    ran_any = False
    for ctx in contexts:
        if not (base_url and ctx["api_key"] and ctx["connection_id"]):
            if required:
                raise RuntimeError(
                    f"Missing env for context {ctx['name']}. Need E2E_ACCESS_BASE_URL + api key + connectionId"
                )
            continue

        ran_any = True

        client = OFAuthClient(
            api_key=ctx["api_key"],
            base_url=base_url,
            connection_id=ctx["connection_id"],
            timeout=60.0,
        )

        last_start_at = 0.0
        fixtures: dict[str, str] = {}
        try:
            # Preflight required-success calls so we actually exercise JSON parsing on 2xx responses.
            last_start_at = _sleep_until_next(ctx["min_delay_ms"], last_start_at)
            self_val = client.request(
                "GET", "/v2/access/self", connection_id=ctx["connection_id"]
            )
            assert not isinstance(self_val, str)
            user_id = _self_id(self_val)
            if user_id:
                fixtures["userId"] = user_id

            if "creator" in ctx["name"]:
                last_start_at = _sleep_until_next(ctx["min_delay_ms"], last_start_at)
                top_val = client.request(
                    "GET",
                    "/v2/access/analytics/posts/top",
                    query={
                        "startDate": "2024-01-01",
                        "endDate": "2024-01-31",
                        "limit": 1,
                        "offset": 0,
                    },
                    connection_id=ctx["connection_id"],
                )
                assert not isinstance(top_val, str)

            def rate_limited_get(path: str, query: dict | None = None) -> object:
                nonlocal last_start_at
                last_start_at = _sleep_until_next(ctx["min_delay_ms"], last_start_at)
                return client.request(
                    "GET", path, query=query, connection_id=ctx["connection_id"]
                )

            def ensure_fixture(name: str) -> str | None:
                if name in fixtures:
                    return fixtures[name]

                # Minimal, read-only fixture discovery.
                if name == "userId":
                    return fixtures.get("userId")

                if name == "postId":
                    val = rate_limited_get("/v2/access/posts", {"limit": 1})
                    pid = _first_list_item_id(val)
                    if pid:
                        fixtures[name] = pid
                        return pid
                    return None

                if name == "listId":
                    val = rate_limited_get("/v2/access/users/lists", {"limit": 1})
                    lid = _first_list_item_id(val)
                    if lid:
                        fixtures[name] = lid
                        return lid
                    return None

                if name == "vaultListId":
                    val = rate_limited_get("/v2/access/vault/lists", {"limit": 1})
                    lid = _first_list_item_id(val)
                    if lid:
                        fixtures[name] = lid
                        return lid
                    return None

                if name == "chatUserId":
                    val = rate_limited_get("/v2/access/chats", {"limit": 1})
                    cid = _chat_user_id_from_chats(val)
                    if cid:
                        fixtures[name] = cid
                        return cid
                    return None

                if name == "subscriptionId":
                    val = rate_limited_get("/v2/access/subscriptions", {"limit": 1})
                    sid = _first_list_item_id(val)
                    if sid:
                        fixtures[name] = sid
                        return sid
                    return None

                if name == "massMessageId":
                    val = rate_limited_get(
                        "/v2/access/analytics/mass-messages/sent", {"limit": 1}
                    )
                    mid = _first_list_item_id(val)
                    if mid:
                        fixtures[name] = mid
                        return mid
                    return None

                if name == "promotionId":
                    val = rate_limited_get("/v2/access/promotions", {"limit": 1})
                    pid = _first_list_item_id(val)
                    if pid:
                        fixtures[name] = pid
                        return pid
                    return None

                if name == "bundleId":
                    val = rate_limited_get(
                        "/v2/access/promotions/bundles", {"limit": 1}
                    )
                    bid = _first_list_item_id(val)
                    if bid:
                        fixtures[name] = bid
                        return bid
                    return None

                if name == "trackingLinkId":
                    val = rate_limited_get(
                        "/v2/access/promotions/tracking-links", {"limit": 1}
                    )
                    tid = _first_list_item_id(val)
                    if tid:
                        fixtures[name] = tid
                        return tid
                    return None

                if name == "trialLinkId":
                    val = rate_limited_get(
                        "/v2/access/promotions/trial-links", {"limit": 1}
                    )
                    tid = _first_list_item_id(val)
                    if tid:
                        fixtures[name] = tid
                        return tid
                    return None

                return None

            for ep in endpoints:
                route = ep["route"]
                names = _route_param_names(route)
                params: dict[str, str] = {}
                can_run = True
                for n in names:
                    v = ensure_fixture(_fixture_key_for_route_param(route, n))
                    if not v:
                        can_run = False
                        break
                    params[n] = v
                if not can_run:
                    continue

                path = "/v2/access" + _fill_route_params(route, params)
                query = _default_query(route, fixtures)

                last_start_at = _sleep_until_next(ctx["min_delay_ms"], last_start_at)

                value = client.request(
                    "GET",
                    path,
                    query=query,
                    connection_id=ctx["connection_id"],
                )

                remaining.discard(route)

                if isinstance(value, str):
                    if _is_likely_malformed_json(value):
                        raise AssertionError(
                            f'[{ctx["name"]}] raw string contains malformed JSON (e.g. url:"""") route={route}'
                        )
                    raise AssertionError(
                        f"[{ctx['name']}] raw string returned (expected parsed JSON) route={route}"
                    )
        finally:
            client.close()

    if not ran_any:
        pytest.skip(
            "no e2e credentials provided (set E2E_ACCESS_BASE_URL + connection/api keys or E2E_CONTRACT_REQUIRED=1)"
        )

    if strict and remaining:
        missing = sorted([r for r in remaining if isinstance(r, str)])
        raise AssertionError(
            "Missing happy-path coverage for GET access endpoints.\n"
            "Provide additional connection ids or explicit fixtures so every endpoint can return 2xx.\n"
            "Missing routes:\n- " + "\n- ".join(missing)
        )
