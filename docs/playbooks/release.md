# Release Playbook

## Current Release Shape

- Packaging metadata lives in `pyproject.toml`.
- Smithery launch metadata lives in `smithery.yaml`.
- PyPI publishing is driven by `.github/workflows/publish.yml`.

## Release Checklist

1. Verify docs and runtime surface are consistent.
2. Run the default validation sequence from
   `docs/playbooks/validation.md`.
3. Confirm version metadata in `pyproject.toml`.
4. Tag a release as `v*.*.*` to trigger the publish workflow.
5. Confirm Smithery instructions still match the runtime entrypoint.
