# Quality Score

This scorecard is a lightweight snapshot, not a compliance badge.

- 2026-03-12 — Runtime safety — Grade: B+ — Evidence: bounded server
  concurrency, safe download root, explicit adapter timeouts — Next action:
  add deterministic parser fixtures so adapter behavior can be checked without
  the network.
- 2026-03-12 — Verification speed — Grade: B+ — Evidence: default
  `unittest discover -q` is now offline and `PAPER_SEARCH_LIVE_TESTS=1`
  gates network checks — Next action: add CI coverage for one targeted live
  adapter smoke job.
- 2026-03-12 — Docs alignment — Grade: A- — Evidence: README, validation
  playbook, security/reliability docs, and TODO tracker now describe the same
  `uv` workflow — Next action: keep the capability matrix synchronized when a
  source changes behavior.
