# Development tasks. `uv run --no-project` keeps the repo free of uv.lock / .venv.

UV_RUN = uv run --no-project --with-editable .
# `models` and `webhooks` (listed in onlyfans_sdk.__all__) and the integrations' submodules are picked up automatically.
DOC_MODULES = onlyfans_sdk onlyfans_sdk._client onlyfans_sdk._async_client onlyfans_sdk.facade \
	onlyfans_sdk.link onlyfans_sdk.store onlyfans_sdk.scopes onlyfans_sdk.testing onlyfans_sdk.events \
	onlyfans_sdk.realtime onlyfans_sdk.uploads onlyfans_sdk.integrations

.PHONY: test lint docs

test:
	$(UV_RUN) --with pytest --with pytest-asyncio --with fastapi --with httpx --with flask pytest -q

lint:
	$(UV_RUN) --with "ruff>=0.8,<0.9" ruff check onlyfans_sdk tests examples
	$(UV_RUN) --with mypy mypy onlyfans_sdk --ignore-missing-imports

# HTML API reference in docs/ (gitignored).
docs:
	rm -rf docs
	$(UV_RUN) --with pdoc pdoc --docformat google -o docs $(DOC_MODULES)
