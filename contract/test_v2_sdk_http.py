import json
import os
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from onlyfans_sdk import OFAuthClient, vault


def test_vault_filter_survives_pagination_with_existing_and_canonical_arguments():
    requests = []
    media = [{"id": i, "type": "photo" if i in (1, 3) else "video"} for i in range(1, 6)]

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_GET(self):
            requests.append(self.path)
            url = urlparse(self.path)
            query = parse_qs(url.query)
            if url.path != "/v2/access/vault/media":
                self.send_error(404)
                return
            filtered = [item for item in media if not query.get("type") or item["type"] == query["type"][0]]
            offset, limit = int(query.get("offset", [0])[0]), int(query.get("limit", [24])[0])
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"list": filtered[offset:offset + limit], "hasMore": offset + limit < len(filtered)}).encode())

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = OFAuthClient(api_key="http-contract-fixture", base_url=f"http://127.0.0.1:{server.server_port}")
        for params in [
            {"media_type": "video", "sort_by": "recent", "sort_direction": "asc"},
            {"type": "video", "sort": "oldest"},
        ]:
            videos = list(vault.iter_media(client, page_size=2, **params))
            assert [item["id"] for item in videos] == [2, 4, 5]
            assert all(item["type"] == "video" for item in videos)
        for request in requests:
            query = parse_qs(urlparse(request).query)
            assert query["type"] == ["video"]
            assert query["sort"] == ["oldest"]
            assert "mediaType" not in query
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
        artifact_dir = Path(os.environ.get("SDK_HTTP_ARTIFACT_DIR", tempfile.mkdtemp(prefix="ofauth-python-http-")))
        artifact_dir.mkdir(parents=True, exist_ok=True)
        artifact = artifact_dir / "python-requests.json"
        artifact.write_text(json.dumps(requests, indent=2))
        print(f"HTTP request artifact: {artifact}")
