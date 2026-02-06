# OFAuth Python SDK Examples

Runnable examples demonstrating the OFAuth Python SDK features.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your API key
```

3. Run examples:
```bash
python basic.py                  # Basic account operations
python import_connection.py      # Import connection demo
python access_api.py             # Access API examples (requires connection ID)
python pagination.py             # Pagination with generators
python proxy.py                  # Proxy endpoint examples (requires connection ID)
python error_handling.py         # Error handling patterns
```

## Examples

### basic.py
Demonstrates basic SDK usage:
- Client initialization
- Getting account info (`whoami()`)
- Listing connections
- Getting connection settings

**Requirements:** API key

### import_connection.py
Shows how to import externally managed connections:
- Importing a connection with cookie + user agent
- Updating imported connection session
- Distinguishing imported vs managed connections

**Requirements:** API key, valid OnlyFans session data

### access_api.py
Access API examples for working with OnlyFans data:
- Getting creator profile
- Listing posts
- Getting earnings data
- Listing subscribers

**Requirements:** API key, connection ID

### pagination.py
Pagination patterns:
- Generators for automatic pagination
- Manual pagination with `hasMore`/`marker`
- Limiting total items fetched

**Requirements:** API key

### proxy.py
Direct OnlyFans API calls via proxy:
- GET requests
- POST requests with body
- Query parameters

**Requirements:** API key, connection ID

### error_handling.py
Error handling best practices:
- Catching API errors
- Accessing error details (status, code, message)
- Handling different error types

**Requirements:** API key

## Environment Variables

Create a `.env` file with:

```env
OFAUTH_API_KEY=your_api_key_here
OFAUTH_CONNECTION_ID=conn_xxx  # Optional, for access API examples
```

## Notes

- All examples use `python-dotenv` to load environment variables
- Examples with "requires connection ID" need `OFAUTH_CONNECTION_ID` set
- Import connection example requires valid OnlyFans session data
- Some examples are read-only, others demonstrate write operations (commented out for safety)
