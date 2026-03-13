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
4. Push the intended release commit to `main` and wait for the `CI` workflow to
   pass before tagging.
5. Tag a release as `v*.*.*` to trigger the publish workflow.
6. Confirm the publish workflow runs the offline compile and unit-test gate
   before `python -m build` and PyPI publish.
7. Confirm Smithery instructions still match the runtime entrypoint.
