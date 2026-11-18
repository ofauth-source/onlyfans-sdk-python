from __future__ import annotations

import asyncio
from urllib.parse import parse_qs, urlsplit

import pytest

from onlyfans_sdk import (
    OPERATION_SCOPES,
    RECOVERY_ACTIONS,
    AsyncOFAuthClient,
    OFAuthAPIError,
    OFAuthClient,
    OFAuthError,
    OFAuthLink,
    OFAuthOAuthError,
    UnknownOperationError,
    ValidationIssue,
    missing_scopes,
    scope_for,
    scopes_for,
)
from tests.conftest import Recorder, json_response


def test_operation_scope_map_covers_every_operation():
    assert OPERATION_SCOPES["access.chats.messages.send"] == "messages:write"
    assert OPERATION_SCOPES["linkedAccounts.list"] is None


def test_scopes_for():
    assert scopes_for("access.chats.messages.send", "access.profile.get", "access.chats.messages.send") == [
        "messages:write",
        "profile:read",
    ]
    assert scopes_for("access.profile.get") == ["profile:read"]
    assert scopes_for("linkedAccounts.list") == []
    assert scopes_for("linked_accounts.list") == []  # snake_case spelling
    assert scope_for("vault_plus.get_stats") is None
    with pytest.raises(UnknownOperationError) as info:
        scopes_for("access.nope")
    assert isinstance(info.value, OFAuthError) and isinstance(info.value, ValueError)


def test_create_authorization_url_merges_operations_with_scopes():
    link = OFAuthLink("ofext_sandbox_x", client_secret="fixture", redirect_uri="https://app.test/cb", auth_url="https://auth.test")
    auth = link.create_authorization_url(
        ["profile:read"], operations=["access.chats.messages.send", "access.profile.get"]
    )
    scope = parse_qs(urlsplit(auth.url).query)["scope"][0]
    assert scope == "profile:read messages:write"
    only_ops = link.create_authorization_url(operations=["access.chats.messages.send"])
    assert parse_qs(urlsplit(only_ops.url).query)["scope"] == ["messages:write"]
    with pytest.raises(OFAuthError, match="scopes or operations"):
        link.create_authorization_url()
    with pytest.raises(UnknownOperationError):
        link.create_authorization_url(operations=["nope"])


def test_generated_methods_set_operation_and_required_scope():
    rec = Recorder(lambda r: json_response(403, {"error": "missing_scope", "recovery": {"action": "request_additional_consent"}}))
    client = OFAuthClient(access_token="t", linked_account_id="a", http_client=rec.sync_client())
    with pytest.raises(OFAuthAPIError) as info:
        client.access.chats.messages.send(user_id=1, body={"text": "hi"})
    error = info.value
    assert error.operation == "access.chats.messages.send"
    assert error.required_scope == "messages:write"
    assert missing_scopes(error) == ["messages:write"]
    assert error.needs_reauthorization
    assert "operation='access.chats.messages.send'" in repr(error)

    rec2 = Recorder(lambda r: json_response(404, {"error": "not_found"}))
    client2 = OFAuthClient(access_token="t", http_client=rec2.sync_client())
    with pytest.raises(OFAuthAPIError) as info2:
        client2.linked_accounts.get(id="x")
    assert info2.value.operation == "linkedAccounts.get" and info2.value.required_scope is None
    assert missing_scopes(info2.value) == []


def test_missing_scopes_codes():
    consent = OFAuthAPIError(403, {"error": "additional_consent_required"}, required_scope="posts:write")
    assert missing_scopes(consent) == ["posts:write"]
    other = OFAuthAPIError(403, {"error": "forbidden"}, required_scope="posts:write")
    assert missing_scopes(other) == []
    assert missing_scopes(ValueError()) == []


def api_error(status: int, action: str | None) -> OFAuthAPIError:
    body: dict = {"error": "x"}
    if action:
        body["recovery"] = {"action": action}
    return OFAuthAPIError(status, body)


@pytest.mark.parametrize(
    ("status", "action", "expected"),
    [
        (400, "retry", {"is_retryable"}),
        (400, "retry_after_reset", {"is_retryable"}),
        (429, None, {"is_retryable"}),
        (502, None, {"is_retryable"}),
        (503, None, {"is_retryable"}),
        (504, None, {"is_retryable"}),
        (401, "obtain_external_oauth_token", {"needs_token_refresh"}),
        (401, "restart_authorization", {"needs_reauthorization"}),
        (403, "request_additional_consent", {"needs_reauthorization"}),
        (403, "grant_linked_account", {"needs_reauthorization"}),
        (409, "reconnect_linked_account", {"needs_reconnect"}),
        (403, "complete_integration_approval", {"is_integration_problem"}),
        (402, "update_developer_plan", {"is_integration_problem"}),
        (403, "contact_integration_owner", {"is_integration_problem"}),
        (403, "enable_vault_plus", {"is_integration_problem"}),
        (400, "check_request", set()),
        (400, "some_future_action", set()),
        (400, None, set()),
    ],
)
def test_error_convenience_properties(status, action, expected):
    error = api_error(status, action)
    flags = {"is_retryable", "needs_token_refresh", "needs_reauthorization", "needs_reconnect", "is_integration_problem"}
    assert {flag for flag in flags if getattr(error, flag)} == expected
    assert error.recovery_action == action


def test_recovery_actions_list_and_oauth_errors():
    assert len(RECOVERY_ACTIONS) == 19 and "restart_upload" in RECOVERY_ACTIONS
    assert OFAuthOAuthError(400, {"error": "invalid_grant"}).needs_reauthorization
    assert not OFAuthOAuthError(400, {"error": "invalid_client"}).needs_reauthorization
    assert OFAuthOAuthError(400, {"error": "x", "recovery": {"action": "restart_authorization"}}).needs_reauthorization
    assert not OFAuthError("plain").needs_reauthorization


VALIDATION_BODY = {
    "success": False,
    "error": {
        "name": "ZodError",
        "issues": [
            {"code": "too_big", "path": ["limit"], "message": "Number must be less than or equal to 100"},
            {"code": "invalid_type", "path": ["body", "items", 0], "message": "Required"},
        ],
    },
}
HANDLER_BODY = {"error": "Upload not found", "type": "RESOURCE_NOT_FOUND", "requestId": "req_3", "success": False}


def test_runtime_error_body():
    error = OFAuthAPIError(
        403,
        {"error": "missing_scope", "message": "needs vault:read", "recovery": {"action": "request_additional_consent"}, "requestId": "req_1"},
    )
    assert (error.code, error.recovery_action, error.request_id) == ("missing_scope", "request_additional_consent", "req_1")
    assert str(error) == "missing_scope: needs vault:read"
    assert error.issues is None and error.error_type is None
    assert error.needs_reauthorization


def test_request_validation_error_body():
    error = OFAuthAPIError(400, VALIDATION_BODY, {"x-request-id": "req_2"})
    assert error.code == "invalid_request"
    assert error.recovery_action == "check_request"
    assert error.message == "limit: Number must be less than or equal to 100; body.items.0: Required"
    assert str(error) == "invalid_request: " + error.message
    assert error.issues == [
        ValidationIssue(code="too_big", path=["limit"], message="Number must be less than or equal to 100"),
        ValidationIssue(code="invalid_type", path=["body", "items", 0], message="Required"),
    ]
    assert error.request_id == "req_2" and error.body is VALIDATION_BODY
    assert error.error_type is None and not error.is_retryable


def test_access_handler_error_body():
    error = OFAuthAPIError(404, HANDLER_BODY)
    assert error.code == "resource_not_found"
    assert error.error_type == "RESOURCE_NOT_FOUND"
    assert error.message == "Upload not found"
    assert str(error) == "resource_not_found: Upload not found"
    assert error.recovery_action is None and error.issues is None
    assert error.request_id == "req_3"
    assert OFAuthAPIError(502, {"error": "Upstream failed", "type": "PROXY_ERROR"}).is_retryable


@pytest.mark.parametrize(
    ("body", "code"),
    [(VALIDATION_BODY, "invalid_request"), (HANDLER_BODY, "resource_not_found")],
)
def test_error_shapes_through_sync_and_async_clients(body, code):
    rec = Recorder(lambda r: json_response(400 if code == "invalid_request" else 404, body))
    client = OFAuthClient(access_token="t", linked_account_id="a", http_client=rec.sync_client())
    with pytest.raises(OFAuthAPIError) as info:
        client.access.chats.list()
    assert info.value.code == code

    async def run() -> OFAuthAPIError:
        async_client = AsyncOFAuthClient(access_token="t", linked_account_id="a", http_client=rec.async_client())
        try:
            await async_client.access.chats.list()
        except OFAuthAPIError as error:
            return error
        raise AssertionError("expected OFAuthAPIError")

    error = asyncio.run(run())
    assert error.code == code
    assert (error.issues is not None) == (code == "invalid_request")
    assert (error.error_type is not None) == (code == "resource_not_found")
