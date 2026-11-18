from __future__ import annotations

import asyncio
import io
import json
from collections.abc import Callable

import httpx
import pytest

from onlyfans_sdk import AsyncOFAuthClient, OFAuthClient, OFAuthError, md5_hex, models
from onlyfans_sdk.uploads import _vault_media_ids
from tests.conftest import Recorder, json_response

DATA = b"0123456789abcdefghij"  # 20 bytes

MEDIA = {
    "id": 77,
    "type": "photo",
    "canView": True,
    "convertedToVideo": False,
    "createdAt": "2030-01-01T00:00:00Z",
    "error": False,
    "ready": True,
    "releaseForms": [],
}


def vault_handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/v3/access/uploads/finalize":
        return json_response(
            200,
            {
                "listId": 5,
                "uploads": [
                    {"uploadId": "up_1", "mediaId": 9001, "media": {**MEDIA, "id": 9001}},
                    {"uploadId": "up_2", "mediaId": 9002.0, "media": {**MEDIA, "id": 9002}},
                ],
            },
        )
    return upload_handler(request)


def test_md5_hex():
    assert md5_hex(b"") == "d41d8cd98f00b204e9800998ecf8427e"
    assert md5_hex(b"The quick brown fox jumps over the lazy dog") == "9e107d9d372bb6826bd81d3542a419d6"


def upload_handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/v3/access/uploads/start":
        return json_response(
            200,
            {
                "status": "needs_upload",
                "uploadId": "up_1",
                "uploadType": "multipart",
                "totalParts": 2,
                "partSize": 12,
                "expiresAt": "2030-01-01T00:00:00Z",
                "parts": [
                    {"partNumber": 1, "uploadUrl": "https://api.test/v3/access/uploads/up_1/parts/1?sig=a",
                     "byteRange": {"start": 0, "end": 11}},
                    {"partNumber": 2, "uploadUrl": "https://api.test/v3/access/uploads/up_1/parts/2?sig=b",
                     "byteRange": {"start": 12, "end": 19}},
                ],
            },
        )
    if request.method == "PUT":
        return httpx.Response(200)
    if path == "/v3/access/uploads/finalize":
        return json_response(200, {"uploadIds": ["up_1"]})
    return json_response(404, {"error": "not_found"})


def test_upload_media_flow():
    rec = Recorder(upload_handler)
    client = OFAuthClient(access_token="tok", linked_account_id="acct_1", base_url="https://api.test",
                          http_client=rec.sync_client())
    progress: list[tuple[int, int]] = []
    result = client.upload_media(
        DATA, filename="upload.png", content_type="image/jpeg", vault_upload={"userId": "42"}, on_progress=lambda a, b: progress.append((a, b))
    )
    assert result.status == "uploaded" and result.upload_id == "up_1" and result.media_item == "up_1"
    assert isinstance(result.finalize, models.V3AccessUploadsFinalizePostResponse)
    assert result.finalize.root.uploadIds == ["up_1"]
    assert result.vault_media_ids == []

    start, put1, put2, finalize = rec.requests
    assert json.loads(start.content) == {"filename": "upload.png", "etag": md5_hex(DATA), "size": 20, "contentType": "image/jpeg"}
    assert str(put1.url) == "https://api.test/v3/access/uploads/up_1/parts/1?sig=a"
    assert put1.content == DATA[:12] and put2.content == DATA[12:]
    assert put1.headers["content-type"] == "image/jpeg"
    for req in rec.requests:
        assert req.headers["authorization"] == "Bearer tok"
        assert req.headers["x-linked-account-id"] == "acct_1"
    assert json.loads(finalize.content) == {"uploadIds": ["up_1"], "vaultUpload": {"userId": "42"}}
    assert progress == [(12, 20), (20, 20)]


def test_upload_media_already_exists_and_file_objects():
    rec = Recorder(lambda r: json_response(200, {"status": "already_exists", "media": {"id": 77, "type": "photo"}}))
    client = OFAuthClient(access_token="tok", linked_account_id="a", http_client=rec.sync_client())
    handle = io.BytesIO(DATA)
    handle.name = "photo.png"
    result = client.upload_media(handle, filename="photo.png", etag="custom")
    assert result.status == "already_exists" and result.media_id == 77 and result.media_item == 77
    assert json.loads(rec.last.content) == {"filename": "photo.png", "etag": "custom", "size": 20, "contentType": "image/png"}
    assert len(rec.requests) == 1

    with pytest.raises(OFAuthError, match="content_type"):
        client.upload_media(DATA, filename="upload.png")


def test_async_upload_media_flow():
    async def run() -> None:
        rec = Recorder(upload_handler)
        async with AsyncOFAuthClient(access_token="tok", linked_account_id="acct_1", base_url="https://api.test",
                                     http_client=rec.async_client()) as client:
            result = await client.upload_media(DATA, filename="upload.png", content_type="video/mp4")
        assert result.upload_id == "up_1"
        assert [r.method for r in rec.requests] == ["POST", "PUT", "PUT", "POST"]
        assert json.loads(rec.requests[-1].content) == {"uploadIds": ["up_1"]}

    asyncio.run(run())


def part_url_handler(upload_url: str) -> Callable[[httpx.Request], httpx.Response]:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v3/access/uploads/start":
            return json_response(200, {"status": "needs_upload", "uploadId": "up_1",
                                       "parts": [{"partNumber": 1, "uploadUrl": upload_url,
                                                  "byteRange": {"start": 0, "end": 19}}]})
        if request.method == "PUT":
            return httpx.Response(200)
        return json_response(200, {"uploadIds": ["up_1"]})

    return handler


def test_upload_part_on_api_origin_is_sent_with_credentials():
    rec = Recorder(part_url_handler("https://API.test:443/v3/access/uploads/up_1/parts/1"))
    client = OFAuthClient(access_token="tok", linked_account_id="acct_1", base_url="https://api.test",
                          http_client=rec.sync_client())
    client.upload_media(DATA, filename="upload.png", content_type="image/png")
    put = rec.requests[1]
    assert put.method == "PUT"
    assert put.headers["authorization"] == "Bearer tok"
    assert put.headers["x-linked-account-id"] == "acct_1"


CROSS_ORIGIN_PART_URLS = [
    "https://evil.example/v3/access/uploads/up_1/parts/1",
    "https://uploads.api.test/v3/access/uploads/up_1/parts/1",
    "http://api.test/v3/access/uploads/up_1/parts/1",
    "https://api.test:8443/v3/access/uploads/up_1/parts/1",
    "https://api.test@evil.example/v3/access/uploads/up_1/parts/1",
    "/v3/access/uploads/up_1/parts/1",
]


@pytest.mark.parametrize("upload_url", CROSS_ORIGIN_PART_URLS)
def test_upload_part_off_api_origin_is_refused_before_sending(upload_url: str):
    rec = Recorder(part_url_handler(upload_url))
    client = OFAuthClient(access_token="tok", linked_account_id="acct_1", base_url="https://api.test",
                          http_client=rec.sync_client())
    with pytest.raises(OFAuthError, match="Refusing to send"):
        client.upload_media(DATA, filename="upload.png", content_type="image/png")
    assert [r.url.path for r in rec.requests] == ["/v3/access/uploads/start"]


@pytest.mark.parametrize("upload_url", CROSS_ORIGIN_PART_URLS)
def test_async_upload_part_off_api_origin_is_refused_before_sending(upload_url: str):
    async def run() -> None:
        rec = Recorder(part_url_handler(upload_url))
        async with AsyncOFAuthClient(access_token="tok", linked_account_id="acct_1", base_url="https://api.test",
                                     http_client=rec.async_client()) as client:
            with pytest.raises(OFAuthError, match="not the API origin|not an absolute"):
                await client.upload_media(DATA, filename="upload.png", content_type="image/png")
        assert len(rec.requests) == 1

    asyncio.run(run())


def test_relative_paths_are_unaffected():
    rec = Recorder(lambda request: json_response(200, {}))
    client = OFAuthClient(access_token="tok", base_url="https://api.test/", http_client=rec.sync_client())
    client.request("GET", "/v3/access/profile")
    assert str(rec.last.url) == "https://api.test/v3/access/profile"


def test_upload_media_vault_upload_typed_finalize_and_vault_media_ids():
    rec = Recorder(vault_handler)
    client = OFAuthClient(access_token="tok", linked_account_id="acct_1", base_url="https://api.test",
                          http_client=rec.sync_client())
    result = client.upload_media(DATA, filename="upload.png", content_type="image/jpeg", vault_upload={"userId": "42", "listId": 5})
    assert result.status == "uploaded" and result.media_item == "up_1"
    assert result.vault_media_ids == [9001, 9002]
    finalize = result.finalize.root
    assert isinstance(finalize, models.V3AccessUploadsFinalizePostResponse2)
    assert finalize.uploads[0].uploadId == "up_1"
    assert isinstance(finalize.uploads[0].media, models.MediaAsset)


def test_upload_media_already_exists_media_is_typed():
    rec = Recorder(lambda r: json_response(200, {"status": "already_exists", "media": MEDIA}))
    client = OFAuthClient(access_token="tok", linked_account_id="a", http_client=rec.sync_client())
    result = client.upload_media(DATA, filename="upload.png", content_type="image/png")
    assert isinstance(result.media, models.MediaAsset)
    assert result.media.type == models.MediaType.PHOTO and result.media_id == 77
    assert result.finalize is None and result.vault_media_ids == []


def test_off_spec_responses_still_return_models_unvalidated():
    rec = Recorder(lambda r: json_response(200, {"status": "already_exists", "media": {"id": 5, "extra": 1}}))
    client = OFAuthClient(access_token="tok", linked_account_id="a", http_client=rec.sync_client())
    result = client.upload_media(DATA, filename="upload.png", content_type="image/png")
    assert isinstance(result.media, models.MediaAsset) and result.media.id == 5 and result.media_id == 5


def test_vault_media_ids_shapes():
    assert _vault_media_ids({"uploads": [{"mediaId": 1}, {"mediaId": "2"}, {"mediaId": None}, "x"]}) == [1, 2]
    assert _vault_media_ids({"mediaIds": [3, 4.0, True]}) == [3, 4]
    assert _vault_media_ids({"media": [{"id": 5}, {"id": "nope"}]}) == [5]
    assert _vault_media_ids({"uploadIds": ["up_1"]}) == []
    assert _vault_media_ids(None) == []


def test_async_upload_media_vault_media_ids():
    async def run() -> None:
        rec = Recorder(vault_handler)
        async with AsyncOFAuthClient(access_token="tok", linked_account_id="acct_1", base_url="https://api.test",
                                     http_client=rec.async_client()) as client:
            result = await client.upload_media(DATA, filename="upload.png", content_type="image/jpeg", vault_upload={"userId": "42"})
        assert result.vault_media_ids == [9001, 9002]
        assert isinstance(result.finalize, models.V3AccessUploadsFinalizePostResponse)

    asyncio.run(run())
