"""
Calls every V3 Access GET operation through the SDK against a real authorization.

Skipped unless E2E_LINKED_ACCOUNT_ID and either E2E_ACCESS_TOKEN or the E2E_SANDBOX_* client
credentials are set. See README.md.
"""

from __future__ import annotations

import datetime
import inspect
import json
import os
import re
import sys
import time
import warnings
from pathlib import Path
from typing import Any

import pytest

PYTHON_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_PACKAGE_ROOT))

from onlyfans_sdk import AccessTokenSource, OFAuthAPIError, OFAuthClient, OFAuthLink  # noqa: E402

MANIFEST_PATH = Path(__file__).with_name("accessEndpoints.manifest.json")

# Errors that mean "this authorization cannot exercise the operation", not "the SDK is broken".
SKIPPABLE = {
    "missing_scope",
    "additional_consent_required",
    "provider_resource_not_found",
    "provider_request_rejected",
    "subscription_required",
    "vault_plus_disabled",
    "linked_account_vault_plus_disabled",
}


def _flag(name: str) -> bool:
    return (os.getenv(name) or "").strip().lower() in {"1", "true", "yes"}


def _snake(name: str) -> str:
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def _load_manifest() -> list[dict[str, Any]]:
    manifest = json.loads(MANIFEST_PATH.read_text("utf-8"))
    assert isinstance(manifest, list) and manifest
    return manifest


def resolve_sdk_method(client: Any, sdk_path: str) -> Any:
    """The bound SDK method for a manifest `sdk` path (camelCase), or None."""
    target = client
    for part in sdk_path.split("."):
        target = getattr(target, _snake(part), None)
        if target is None:
            return None
    return target if callable(target) else None


def route_params(route: str) -> list[str]:
    return re.findall(r"\{([A-Za-z0-9_]+)\}", route)


def fixture(param: str) -> str | None:
    """Path and required query values come from E2E_FIXTURE_<PARAM>, e.g. E2E_FIXTURE_USER_ID."""
    return os.getenv("E2E_FIXTURE_" + _snake(param).upper())


def default_required(name: str) -> Any:
    today = datetime.date.today()
    defaults = {
        "start_date": (today - datetime.timedelta(days=30)).isoformat(),
        "end_date": today.isoformat(),
        "query": "a",
    }
    return defaults.get(name)


def test_manifest_maps_to_sdk_methods():
    """Offline: every manifest entry resolves to a generated SDK method."""
    client = OFAuthClient(access_token="offline", linked_account_id="offline")
    missing = [e["sdk"] for e in _load_manifest() if resolve_sdk_method(client, e["sdk"]) is None]
    client.close()
    assert missing == []


@pytest.mark.contract
def test_access_get_contract():
    base_url = os.getenv("E2E_ACCESS_BASE_URL") or "https://api.ofauth.com"
    token: AccessTokenSource = os.getenv("E2E_ACCESS_TOKEN") or ""
    linked_account_id = os.getenv("E2E_LINKED_ACCOUNT_ID") or ""
    if not (token and linked_account_id):
        message = (
            "set E2E_LINKED_ACCOUNT_ID and E2E_ACCESS_TOKEN"
        )
        if _flag("E2E_CONTRACT_REQUIRED"):
            pytest.fail(message)
        pytest.skip(f"no E2E credentials ({message})")

    min_delay = float(os.getenv("E2E_MIN_DELAY_MS") or 250) / 1000
    client = OFAuthClient(access_token=token, linked_account_id=linked_account_id, base_url=base_url)
    failures: list[str] = []
    skipped: list[str] = []
    last = 0.0
    try:
        for entry in (e for e in _load_manifest() if e.get("method") == "get"):
            route = entry["route"]
            method = resolve_sdk_method(client, entry["sdk"])
            if method is None:
                failures.append(f"{route}: SDK method {entry['sdk']} missing")
                continue

            kwargs: dict[str, Any] = {}
            missing = []
            for name in route_params(route):
                value = fixture(name)
                if value is None:
                    missing.append(name)
                else:
                    kwargs[_snake(name)] = value
            for name, param in inspect.signature(method).parameters.items():
                if param.default is inspect.Parameter.empty and name not in kwargs:
                    value = fixture(name) or default_required(name)
                    if value is None:
                        missing.append(name)
                    else:
                        kwargs[name] = value
            if missing:
                skipped.append(f"{route}: no fixture for {', '.join(missing)}")
                continue

            wait = last + min_delay - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            last = time.monotonic()
            try:
                result = method(**kwargs)
                if isinstance(result, str):
                    failures.append(f"{route}: returned a raw string, expected JSON")
            except OFAuthAPIError as error:
                if error.code in SKIPPABLE:
                    skipped.append(f"{route}: {error.code}")
                else:
                    failures.append(f"{route}: {error} (request_id={error.request_id})")
            except Exception as error:  # noqa: BLE001
                failures.append(f"{route}: {type(error).__name__}: {error}")
    finally:
        client.close()

    if skipped:
        warnings.warn(f"Skipped {len(skipped)} operations:\n  " + "\n  ".join(skipped), stacklevel=1)
    assert failures == []
    if _flag("E2E_CONTRACT_STRICT"):
        assert skipped == []
