"""
OFAuth Webhook Verification & Routing

Svix-compatible HMAC-SHA256 signature verification.
Uses only Python stdlib — no extra dependencies.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    TypedDict,
    Union,
)

# ============================================================================
# Types
# ============================================================================

WebhookEventType = Literal[
    "connection.created",
    "connection.updated",
    "connection.expired",
    "rules.updated",
]


class UserData(TypedDict, total=False):
    userId: str
    name: str
    username: str
    avatar: str


class Connection(TypedDict, total=False):
    id: str
    platformUserId: str
    status: str
    userData: UserData
    permissions: List[str]


class ConnectionEventData(TypedDict, total=False):
    connection: Connection
    clientReferenceId: Optional[str]


class ExpiredConnectionEventData(TypedDict):
    connection: Dict[str, Any]
    clientReferenceId: Optional[str]


class DynamicRules(TypedDict, total=False):
    static_param: str
    format: str
    start: str
    end: str
    prefix: str
    suffix: str
    checksum_constant: int
    checksum_indexes: List[int]
    app_token: str
    revision: str


class RulesEventData(TypedDict):
    rules: DynamicRules
    revision: str


class WebhookEvent(TypedDict):
    eventType: str
    live: bool
    data: Dict[str, Any]


# ============================================================================
# Errors
# ============================================================================


class WebhookVerificationError(Exception):
    """Raised when webhook signature verification fails."""

    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.code = code


def is_webhook_verification_error(error: BaseException) -> bool:
    """Check if an error is a WebhookVerificationError."""
    return isinstance(error, WebhookVerificationError)


# ============================================================================
# Verification
# ============================================================================


def extract_webhook_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Extract and validate Svix webhook headers.

    Accepts a plain dict (case-insensitive lookup).
    Returns a dict with keys: svix-id, svix-timestamp, svix-signature.
    """
    def _get(name: str) -> Optional[str]:
        # Try exact match first, then lowercase
        return headers.get(name) or headers.get(name.lower())

    svix_id = _get("svix-id")
    svix_timestamp = _get("svix-timestamp")
    svix_signature = _get("svix-signature")

    if not svix_id or not svix_timestamp or not svix_signature:
        raise WebhookVerificationError(
            "Missing required webhook headers (svix-id, svix-timestamp, svix-signature)",
            "MISSING_HEADERS",
        )

    return {
        "svix-id": svix_id,
        "svix-timestamp": svix_timestamp,
        "svix-signature": svix_signature,
    }


def verify_webhook_signature(
    payload: str,
    headers: Dict[str, str],
    secret: str,
    tolerance: int = 300,
) -> bool:
    """
    Verify a webhook signature using the Svix HMAC-SHA256 protocol.

    Args:
        payload: Raw JSON payload as string.
        headers: Dict with svix-id, svix-timestamp, svix-signature keys.
        secret: Webhook signing secret (with or without whsec\_ prefix).
        tolerance: Max allowed timestamp age in seconds (default 300).

    Returns:
        True if the signature is valid.

    Raises:
        WebhookVerificationError: If verification fails.
    """
    # Timestamp check
    try:
        ts = int(headers["svix-timestamp"])
    except (KeyError, ValueError):
        raise WebhookVerificationError("Invalid timestamp format", "INVALID_TIMESTAMP")

    if abs(int(time.time()) - ts) > tolerance:
        raise WebhookVerificationError("Webhook timestamp too old", "TIMESTAMP_TOO_OLD")

    # Compute expected signature
    clean_secret = secret[6:] if secret.startswith("whsec_") else secret
    key = base64.b64decode(clean_secret)
    signed = f'{headers["svix-id"]}.{headers["svix-timestamp"]}.{payload}'
    expected = base64.b64encode(
        hmac.new(key, signed.encode("utf-8"), hashlib.sha256).digest()
    ).decode("utf-8")

    # Parse provided signatures
    sigs = []
    for part in headers["svix-signature"].split(" "):
        pieces = part.split(",", 1)
        if len(pieces) == 2 and pieces[0] == "v1":
            sigs.append(pieces[1])

    if not sigs:
        raise WebhookVerificationError("No valid v1 signatures found", "NO_VALID_SIGNATURES")

    # Timing-safe comparison
    if not any(hmac.compare_digest(expected, sig) for sig in sigs):
        raise WebhookVerificationError("Signature verification failed", "SIGNATURE_MISMATCH")

    return True


def verify_webhook_payload(
    payload: Union[str, bytes],
    headers: Dict[str, str],
    secret: str,
    tolerance: int = 300,
) -> Dict[str, Any]:
    """
    Verify a webhook and return the parsed JSON payload.

    Args:
        payload: Raw payload as string or bytes.
        headers: Request headers dict.
        secret: Webhook signing secret.
        tolerance: Max allowed timestamp age in seconds.

    Returns:
        Parsed webhook event as a dict.
    """
    payload_str = payload.decode("utf-8") if isinstance(payload, bytes) else payload
    wh_headers = extract_webhook_headers(headers)
    verify_webhook_signature(payload_str, wh_headers, secret, tolerance)

    try:
        return json.loads(payload_str)
    except json.JSONDecodeError:
        raise WebhookVerificationError(
            "Failed to parse webhook payload as JSON", "INVALID_JSON"
        )


# ============================================================================
# Router
# ============================================================================

# Handler type aliases
WebhookHandlerFunc = Callable[[Dict[str, Any]], Any]
ErrorHandlerFunc = Callable[[Exception, Optional[Dict[str, Any]]], Any]


class WebhookRouter:
    """
    Routes verified webhook events to registered handler functions.

    Example::

        router = WebhookRouter(secret="whsec_...")
        router.on("connection.created", handle_connection_created)

        # In Flask:
        @app.route("/webhooks", methods=["POST"])
        def webhook():
            router.handle_payload(request.data, dict(request.headers))
            return "OK", 200
    """

    def __init__(
        self,
        secret: str,
        tolerance: int = 300,
        handlers: Optional[Dict[str, WebhookHandlerFunc]] = None,
        default_handler: Optional[WebhookHandlerFunc] = None,
        error_handler: Optional[ErrorHandlerFunc] = None,
    ) -> None:
        self.secret = secret
        self.tolerance = tolerance
        self._handlers: Dict[str, WebhookHandlerFunc] = dict(handlers or {})
        self._default_handler = default_handler
        self._error_handler = error_handler

    def on(self, event_type: str, handler: WebhookHandlerFunc) -> "WebhookRouter":
        """Register a handler for a specific event type."""
        self._handlers[event_type] = handler
        return self

    def on_default(self, handler: WebhookHandlerFunc) -> "WebhookRouter":
        """Register a default handler for unmatched event types."""
        self._default_handler = handler
        return self

    def on_error(self, handler: ErrorHandlerFunc) -> "WebhookRouter":
        """Register an error handler."""
        self._error_handler = handler
        return self

    def handle_payload(
        self,
        payload: Union[str, bytes],
        headers: Dict[str, str],
    ) -> None:
        """
        Verify a webhook payload and route to the appropriate handler.

        Args:
            payload: Raw request body (string or bytes).
            headers: Request headers dict.
        """
        try:
            event = verify_webhook_payload(payload, headers, self.secret, self.tolerance)
            self._process_event(event)
        except Exception as exc:
            if self._error_handler:
                self._error_handler(exc, None)
            else:
                raise

    def _process_event(self, event: Dict[str, Any]) -> None:
        try:
            event_type = event.get("eventType", "")
            handler = self._handlers.get(event_type) or self._default_handler
            if handler is None:
                return
            handler(event)
        except Exception as exc:
            if self._error_handler:
                self._error_handler(exc, event)
            else:
                raise

    def update_secret(self, secret: str) -> None:
        """Update the webhook secret at runtime."""
        self.secret = secret

    def update_tolerance(self, tolerance: int) -> None:
        """Update the timestamp tolerance at runtime."""
        self.tolerance = tolerance


def create_webhook_router(
    secret: str,
    tolerance: int = 300,
    handlers: Optional[Dict[str, WebhookHandlerFunc]] = None,
    default_handler: Optional[WebhookHandlerFunc] = None,
    error_handler: Optional[ErrorHandlerFunc] = None,
) -> WebhookRouter:
    """Convenience factory for WebhookRouter."""
    return WebhookRouter(
        secret=secret,
        tolerance=tolerance,
        handlers=handlers,
        default_handler=default_handler,
        error_handler=error_handler,
    )


# ============================================================================
# Framework Helpers
# ============================================================================


def create_flask_webhook_handler(router: WebhookRouter):
    """
    Create a Flask view function for handling webhooks.

    Usage::

        from flask import Flask
        app = Flask(__name__)
        handler = create_flask_webhook_handler(router)
        app.add_url_rule("/webhooks", view_func=handler, methods=["POST"])
    """

    def flask_handler():
        from flask import request as flask_request, jsonify, make_response

        try:
            router.handle_payload(flask_request.data, dict(flask_request.headers))
            return make_response("OK", 200)
        except WebhookVerificationError as exc:
            return jsonify({"error": str(exc), "code": exc.code}), 401
        except Exception:
            return jsonify({"error": "Internal server error"}), 500

    return flask_handler


def create_fastapi_webhook_handler(router: WebhookRouter):
    """
    Create a FastAPI/Starlette dependency for handling webhooks.

    Usage::

        from fastapi import FastAPI, Request
        app = FastAPI()
        handle_webhook = create_fastapi_webhook_handler(router)

        @app.post("/webhooks")
        async def webhook(request: Request):
            return await handle_webhook(request)
    """

    async def fastapi_handler(request):
        from starlette.responses import JSONResponse, Response

        try:
            body = await request.body()
            headers = dict(request.headers)
            router.handle_payload(body, headers)
            return Response("OK", status_code=200)
        except WebhookVerificationError as exc:
            return JSONResponse(
                {"error": str(exc), "code": exc.code}, status_code=401
            )
        except Exception:
            return JSONResponse(
                {"error": "Internal server error"}, status_code=500
            )

    return fastapi_handler
