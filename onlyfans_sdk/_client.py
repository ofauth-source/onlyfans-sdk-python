"""
OFAuth Python SDK v2 - Minimal, direct API client
"""
from typing import Any, Dict, Optional, Union, BinaryIO
import json
import httpx

BASE_URL = "https://api-next.ofauth.com"


class OFAuthError(Exception):
    """OFAuth API error"""
    def __init__(self, status: int, message: str, code: Optional[str] = None, details: Any = None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.details = details


class OFAuthClient:
    """OFAuth API Client"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = BASE_URL,
        connection_id: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.connection_id = connection_id
        self._client = httpx.Client(timeout=timeout)
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self._client.close()
    
    def close(self):
        self._client.close()
    
    def request(
        self,
        method: str,
        path: str,
        *,
        query: Optional[Dict[str, Any]] = None,
        body: Optional[Any] = None,
        connection_id: Optional[str] = None,
    ) -> Any:
        """Make an API request"""
        url = f"{self.base_url}{path}"
        conn_id = connection_id or self.connection_id
        
        headers = {"apiKey": self.api_key}
        if conn_id:
            headers["x-connection-id"] = conn_id
        if body is not None:
            headers["Content-Type"] = "application/json"
        
        # Filter None values from query
        if query:
            query = {k: v for k, v in query.items() if v is not None}
        
        response = self._client.request(
            method,
            url,
            params=query,
            json=body,
            headers=headers,
        )
        
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = {}
            raise OFAuthError(
                status=response.status_code,
                message=error_body.get("message", f"HTTP {response.status_code}"),
                code=error_body.get("code"),
                details=error_body.get("details"),
            )
        
        if response.status_code == 204:
            return {}
        
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        return response.text
    
    def proxy(
        self,
        path: str,
        method: str = "GET",
        *,
        query: Optional[Dict[str, Any]] = None,
        body: Optional[Any] = None,
        connection_id: Optional[str] = None,
    ) -> Any:
        """
        Make a proxied request to the OnlyFans API.
        
        This allows calling any OnlyFans API endpoint through the OFAuth proxy.
        The path can be provided with or without the '/api2/v2' prefix.
        
        Args:
            path: The OnlyFans API path (e.g., '/users/me' or '/api2/v2/users/me')
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            query: Query parameters
            body: Request body for POST/PUT/PATCH
            connection_id: Connection ID
        
        Returns:
            The API response
        
        Example:
            # Both of these are equivalent:
            user = client.proxy('/users/me', connection_id='conn_xxx')
            user = client.proxy('/api2/v2/users/me', connection_id='conn_xxx')
        """
        # Strip /api2/v2 prefix if present
        target_path = path
        if target_path.startswith('/api2/v2'):
            target_path = target_path[8:]
        elif target_path.startswith('api2/v2'):
            target_path = '/' + target_path[7:]
        
        # Ensure path starts with /
        if not target_path.startswith('/'):
            target_path = '/' + target_path
        
        url = f"{self.base_url}/v2/access/proxy{target_path}"
        conn_id = connection_id or self.connection_id
        
        headers = {"apiKey": self.api_key}
        if conn_id:
            headers["x-connection-id"] = conn_id
        if body is not None:
            headers["Content-Type"] = "application/json"
        
        if query:
            query = {k: v for k, v in query.items() if v is not None}
        
        response = self._client.request(
            method,
            url,
            params=query,
            json=body,
            headers=headers,
        )
        
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = {}
            raise OFAuthError(
                status=response.status_code,
                message=error_body.get("message", f"HTTP {response.status_code}"),
                code=error_body.get("code"),
                details=error_body.get("details"),
            )
        
        if response.status_code == 204:
            return {}
        
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        return response.text
    
    def upload_media(
        self,
        connection_id: str,
        filename: str,
        file: Union[bytes, BinaryIO],
        mime_type: str,
        vault_upload: Optional[Dict[str, Any]] = None,
        on_progress: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """Upload media file (handles single/multi-part automatically)"""
        if hasattr(file, 'read'):
            file_data = file.read()
        else:
            file_data = file
        
        filesize = len(file_data)
        
        # Initialize upload
        init_response = self._client.post(
            f"{self.base_url}/v2/access/uploads/init",
            headers={
                "apiKey": self.api_key,
                "x-connection-id": connection_id,
                "Content-Type": "application/json",
            },
            json={
                "filename": filename,
                "filesize": filesize,
                "mimeType": mime_type,
                "vaultUpload": vault_upload,
            },
        )
        
        if not init_response.is_success:
            try:
                error_body = init_response.json()
            except Exception:
                error_body = {}
            raise OFAuthError(
                status=init_response.status_code,
                message=error_body.get("message", "Upload init failed"),
            )
        
        init_data = init_response.json()
        media_upload_id = init_data["mediaUploadId"]
        total_parts = int(init_response.headers.get("x-ofauth-upload-total-parts", "1"))
        part_size = int(init_response.headers.get("x-ofauth-upload-part-size", str(filesize)))
        
        # Single-part upload
        if total_parts == 1:
            upload_response = self._client.put(
                f"{self.base_url}/v2/access/uploads/{media_upload_id}",
                headers={
                    "apiKey": self.api_key,
                    "x-connection-id": connection_id,
                    "Content-Type": mime_type,
                },
                content=file_data,
            )
            
            if not upload_response.is_success:
                try:
                    error_body = upload_response.json()
                except Exception:
                    error_body = {}
                raise OFAuthError(
                    status=upload_response.status_code,
                    message=error_body.get("message", "Upload failed"),
                )
            
            if on_progress:
                on_progress(filesize, filesize)
            return upload_response.json()
        
        # Multi-part upload
        uploaded = 0
        for part_number in range(1, total_parts + 1):
            start = (part_number - 1) * part_size
            end = min(start + part_size, filesize)
            chunk = file_data[start:end]
            
            part_response = self._client.put(
                f"{self.base_url}/v2/access/uploads/{media_upload_id}/parts/{part_number}",
                headers={
                    "apiKey": self.api_key,
                    "x-connection-id": connection_id,
                    "Content-Type": mime_type,
                },
                content=chunk,
            )
            
            if not part_response.is_success:
                try:
                    error_body = part_response.json()
                except Exception:
                    error_body = {}
                raise OFAuthError(
                    status=part_response.status_code,
                    message=error_body.get("message", "Chunk upload failed"),
                )
            
            uploaded += len(chunk)
            if on_progress:
                on_progress(uploaded, filesize)
        
        # Complete upload
        complete_response = self._client.post(
            f"{self.base_url}/v2/access/uploads/complete",
            headers={
                "apiKey": self.api_key,
                "x-connection-id": connection_id,
                "Content-Type": "application/json",
            },
            json={"mediaUploadId": media_upload_id},
        )
        
        if not complete_response.is_success:
            try:
                error_body = complete_response.json()
            except Exception:
                error_body = {}
            raise OFAuthError(
                status=complete_response.status_code,
                message=error_body.get("message", "Upload complete failed"),
            )
        
        return complete_response.json()
