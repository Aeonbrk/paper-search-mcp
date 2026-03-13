# Offline fixtures

This folder holds deterministic, source-specific fixture files used by
offline unit tests.

Guidelines:

- Store fixtures under `tests/fixtures/{source}/` (for example:
  `tests/fixtures/arxiv/search_response.xml`).
- Keep fixtures small and representative; remove volatile fields when possible.
- Offline tests should fail fast on outbound network access. Prefer using
  `tests._offline.OfflineTestCase`
  or `tests._offline.deny_network()` around any fixture-driven tests.
- When loading fixtures in tests, prefer
  `tests._offline.read_fixture_text()` / `read_fixture_bytes()` /
  `read_fixture_json()` to keep paths consistent and error messages helpful.
