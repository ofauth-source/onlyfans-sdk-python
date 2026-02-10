# SDK Contract Tests (Access API)

Pytest contract tests that hit real OFAuth Access API connections (sandbox + live).

## Environment Variables

- `E2E_ACCESS_BASE_URL`: base URL for the Access API (e.g. `https://api.ofauth.com`)
- `E2E_CONTRACT_REQUIRED`: when `true`, missing creds fail the test run

Per-context credentials:

- `E2E_SANDBOX_API_KEY_CREATOR`, `E2E_SANDBOX_CONNECTION_ID_CREATOR`
- `E2E_SANDBOX_API_KEY_FAN`, `E2E_SANDBOX_CONNECTION_ID_FAN`
- `E2E_LIVE_API_KEY_CREATOR`, `E2E_LIVE_CONNECTION_ID_CREATOR`
- `E2E_LIVE_API_KEY_FAN`, `E2E_LIVE_CONNECTION_ID_FAN`

## Rate Limiting

Live contexts enforce a minimum `2000ms` delay between requests in-code.

