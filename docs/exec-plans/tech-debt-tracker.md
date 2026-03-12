# Tech Debt Tracker

This file records durable debt that should survive any single task.

## Current Debt

### Adapter duplication

- Multiple source modules redefine the same `PaperSource` base class locally.
- Follow-up: centralize the base interface if runtime refactors are approved.

### Validation fragility

- Most tests depend on live services, network access, or scraping behavior.
- Follow-up: add deterministic offline fixtures and separate smoke vs
  integration test suites.

### Documentation drift risk

- The public MCP surface is stable, but source capabilities change faster than
  the docs unless the capability matrix is maintained deliberately.
- Follow-up: update `docs/project-specs/source-capability-matrix.md` whenever a
  source adapter changes behavior.
