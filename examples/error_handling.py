"""
Error handling: automatic retries, recovery-action helpers, missing scopes, request ids.

    OFAUTH_ACCESS_TOKEN=... OFAUTH_LINKED_ACCOUNT_ID=... python error_handling.py
"""

from __future__ import annotations

from _env import API_URL, access_token, require

from onlyfans_sdk import (
    OFAuthAPIError,
    OFAuthClient,
    OFAuthConnectionError,
    OFAuthError,
    OFAuthOAuthError,
    ResponseInfo,
    missing_scopes,
)


def log_response(info: ResponseInfo) -> None:
    print(f"  attempt {info.attempt}: {info.method} {info.url} -> {info.status} ({info.duration_ms:.0f} ms)")


def get_profile(client: OFAuthClient) -> dict | None:
    # 429, 503 authorization_temporarily_unavailable, and (for GET/PUT/DELETE) network
    # errors and 502/503/504 are already retried with backoff (max_retries, default 2).
    try:
        return client.access.profile.get()
    except OFAuthAPIError as error:
        print(f"{error.status} {error.code} -> {error.recovery_action} (request {error.request_id}, "
              f"{error.attempts} attempts, operation {error.operation})")
        if scopes := missing_scopes(error):
            print(f"Ask the user to authorize again with {scopes}")
        elif error.needs_reconnect:
            print("Ask the user to reconnect this account through OFAuth Link.")
        elif error.needs_reauthorization:
            print("Send the user through authorization again.")
        elif error.is_integration_problem:
            print("Fix the integration in the OFAuth dashboard (approval, plan, Vault+).")
        elif error.is_retryable:
            print(f"Try again later (retry_after={error.retry_after})")
    except OFAuthConnectionError as error:
        print(f"No response after {error.attempts} attempts: {error}")
    except OFAuthOAuthError as error:
        # Raised by OAuth refresh. invalid_grant: the refresh token is expired or revoked.
        print(f"Token refresh failed: {error.code}; needs_reauthorization={error.needs_reauthorization}")
    except OFAuthError as error:
        print(f"SDK error: {error}")  # e.g. no linked account configured
    return None


if __name__ == "__main__":
    with OFAuthClient(
        access_token=access_token(),
        linked_account_id=require("OFAUTH_LINKED_ACCOUNT_ID"),
        base_url=API_URL,
        max_retries=3,
        timeout=30,
        on_response=log_response,
        # debug=True,  # or OFAUTH_DEBUG=1: one log line per attempt, never tokens or bodies
    ) as client:
        print(get_profile(client))
        # Per-call options: a copy of the client with retries off.
        print(get_profile(client.with_options(max_retries=0)))
        # Missing linked account: raised locally before any request.
        try:
            OFAuthClient(access_token="unused").access.profile.get()
        except OFAuthError as error:
            print("local error:", error)
