# 统一 uv 工作流：修复 bug、优化性能、补齐文档

This ExecPlan is a living document. The orchestrator is the single writer for
this file: workers return completion packets; the orchestrator updates task
`status`, `log`, and `files_changed`.

If this work is tracked in `docs/PLANS.md`, keep this file synchronized with
that tracker entry.

## Orchestration

Schema version: 1
Execution mode: super_swarm
Scheduler: waves
Max parallelism: 8
Shared-state policy: orchestrator-only
Plan updates: orchestrator-only
File-scope rule: each task must declare writes/creates; workers must not write
outside without escalation
Write-allowed set: writes ∪ creates

## Purpose / Big Picture

把仓库的开发/运行环境统一到 `uv`（含容器构建的可复现安装策略），
并系统化处理：

- **安全**：路径穿越/任意写文件风险、禁用 TLS 校验，
  以及缺失超时与错误处理等；
- **运行时**：async 工具里调用同步 I/O 导致事件循环阻塞，
  以及共享 `requests.Session` 的并发安全等；
- **性能**：连接复用、并发控制、限流退避，
  以及避免无谓的客户端创建；
- **文档**：把“未完成 TODO”沉淀到 `docs/`，
  并补齐/对齐安全、可靠性、验证与能力矩阵文档。

完成标志：

- `uv` 工作流在 README/文档/容器中一致；
- MCP 工具调用不再明显阻塞；
- 下载/读 PDF 的文件路径受控；
- 文档与验证命令可直接照做；
- TODO 列表可执行且不过期。

## Progress

- [x] (2026-03-12 00:08 BJT) Capture scope and acceptance criteria.
- [x] (2026-03-12 00:08 BJT) Implement the planned changes.
- [x] (2026-03-12 00:08 BJT) Run validation and record evidence.
- [x] (2026-03-12 00:08 BJT) Close review notes and summarize outcomes.

## Surprises & Discoveries

- Observation: `README.md` 当前没有明确的 TODO 清单。
  Evidence: `README.md` 未包含 "TODO"/checkbox/roadmap 段落。
  Impact: TODO 清单将改为从上游 README 与 git 历史线索汇总生成。

## Decision Log

- Decision: 本次执行默认保持 MCP 工具名稳定，不新增/重命名工具，
  仅在实现层面修复与优化。
  Rationale: 仓库不变性要求保持运行时身份与工具名稳定。
  Date/Author: 2026-03-12 / orchestrator
- Decision: 容器内采用 `uv sync --locked` + layer cache 的安装方式。
  Rationale: 可复现、速度快、与 `uv.lock` 对齐。
  Date/Author: 2026-03-12 / orchestrator

Open decisions needing user confirmation:

- None (resolved by maintainer input on 2026-03-12).

Resolved decisions:

- Decision: 下载文件默认写入 `docs/downloads/`。
  Rationale: 统一落盘位置，便于清理与审计；避免散落到仓库根目录。
  Date/Author: 2026-03-12 / maintainer
- Decision: TODO 清单来源为“过往 commit 记录 + 上游 README”。
  Rationale: 本仓库 `README.md` 当前没有 TODO 段落；用可追溯来源补齐。
  Date/Author: 2026-03-12 / maintainer
- Decision: TODO 文件名使用英文，不使用书名号。
  Rationale: 降低跨平台与 shell 引用成本。
  Date/Author: 2026-03-12 / maintainer
- Decision: TODO 文档命名为 `docs/TODO.md`。
  Rationale: 约定俗成、入口明确。
  Date/Author: 2026-03-12 / maintainer

## Outcomes & Retrospective

- `uv` now drives local validation and Docker builds from the same lockfile.
- `server.py` runs sync adapter work via `asyncio.to_thread` under a bounded
  semaphore and keeps downloads under `docs/downloads/`.
- Shared `_http.py` and `_paths.py` now centralize timeouts, retries, safe
  filenames, and path containment.
- Default tests stay offline; live checks require `PAPER_SEARCH_LIVE_TESTS=1`.
- T12 (`Sci-Hub`) stays deferred because it is optional and sensitive.

## Artifacts and Notes

- Audit: `docs/references/2026-03-12_bug-and-perf-audit.md`
- `uv sync --locked` -> pass
- `docker build -t paper-search-mcp .` -> pass
- `docker run --rm paper-search-mcp python -c "from paper_search_mcp.server
  import mcp; print(mcp.name)"` -> `paper_search_server`
- `markdownlint README.md $(find docs -type f -name '*.md' | sort)` -> pass
- `uv run python -m compileall paper_search_mcp tests` -> pass
- `uv run python -c "import paper_search_mcp.server as s; print(s.mcp.name)"`
  -> `paper_search_server`
- `uv run python -m unittest discover -q` -> `OK (skipped=25)`

## Context and Orientation

- 运行入口：`paper_search_mcp/server.py`
  使用 `mcp.server.fastmcp.FastMCP` 注册工具。
- 适配器：`paper_search_mcp/academic_platforms/*.py` 以同步 `requests` 为主，部分包含
  `time.sleep()` 退避与随机延迟。
- 统一模型：`paper_search_mcp/paper.py` 的 `Paper.to_dict()` 是返回兼容面。
- 测试：`tests/` 多为 live-network 集成检查，且存在高开销下载测试。
- 文档：`docs/` 与 `codemap/` 已建立治理与验证流程，但需要与本次修复同步。

核心问题概览（用于任务拆分）：

- async 工具函数内部调用同步网络/磁盘 I/O（含 `time.sleep`）
  会阻塞事件循环；
- 多处 `requests.get()` 缺少超时/`raise_for_status()`；
- 下载/读取 PDF 的输出路径拼接不一致，存在路径穿越与目录不存在问题；
- `tests/test_server.py` 会下载 10 篇论文 PDF，默认验证过重；
- `Dockerfile` 当前使用 `pip install .`，与 `uv.lock` 没有形成可复现闭环。

## Task Graph (Dependencies)

Note: 任务编号不强制连续；例如 T12 是后续插入的可选敏感任务。

### T0: 依赖与锁文件调整（如需要）

depends_on: []
reads: [pyproject.toml, uv.lock]
writes: [pyproject.toml, uv.lock]
creates: []
mutex: scope:deps
description: 仅在需要新增/调整依赖时修改 `pyproject.toml` 与 `uv.lock`；
  否则标注为 skipped。
acceptance: 如无新增依赖需求，本任务不修改任何文件并标注为 skipped。
acceptance: 如有修改，`uv sync --locked` 成功且不产生意外依赖漂移。
validation: uv sync --locked
status: done
log: 2026-03-12 / orchestrator / dispatched via super-swarm
log: 2026-03-12 / worker / skipped; no dependency or lockfile changes required
log: 2026-03-12 / worker / validation passed: `uv sync --locked`

### T1: 用 uv 改造 Docker 构建/运行

depends_on: [T0]
reads: [Dockerfile, pyproject.toml, uv.lock, README.md]
writes: [Dockerfile]
creates: [.dockerignore]
mutex: scope:container-build
description: 让容器构建使用 `uv sync --locked`，并通过 layer cache 加速与保证可复现。
acceptance: Docker 构建不依赖宿主 `.venv`。
acceptance: 依赖安装由 `uv.lock` 驱动（`uv sync --locked`）。
acceptance: 镜像启动命令能运行 `python -m paper_search_mcp.server`。
acceptance: `.dockerignore` 排除 `.venv/` 与 `docs/downloads/` 等运行时产物。
acceptance: Dockerfile 明确安装 uv（固定版本或校验方式）。
acceptance: 如 Alpine/musl 下 uv 不可用，切换到 debian-slim 基础镜像。
note: 如使用 cache mount，需要 BuildKit；否则仍应保持正确性，只是更慢。
validation: docker build -t paper-search-mcp .
validation: docker run --rm paper-search-mcp python -c \
  "from paper_search_mcp.server import mcp; print(mcp.name)"
status: done
log: 2026-03-12 / orchestrator / dispatched via super-swarm after T0
log: 2026-03-12 / worker / switched container build to pinned `uv` on `python:3.10-slim`
log: 2026-03-12 / worker / validated: `docker build -t paper-search-mcp .`
log: 2026-03-12 / worker / validated: import smoke -> `paper_search_server`
files_changed: Dockerfile
files_changed: .dockerignore

### T2: 汇总安全/运行时/性能问题清单（审计报告）

depends_on: []
reads: [
  paper_search_mcp/**/*.py,
  tests/**/*.py,
  docs/SECURITY.md,
  docs/RELIABILITY.md,
]
writes: []
creates: [docs/references/2026-03-12_bug-and-perf-audit.md]
mutex: file:docs/references/2026-03-12_bug-and-perf-audit.md
description: 按风险级别整理安全/运行时/性能问题，并给出修复建议。
acceptance: 文档包含风险分级、影响范围、修复建议与验证建议。
acceptance: 文档注明审计基于的代码版本（记录 `git rev-parse HEAD`）。
acceptance: 文档记录“公共 MCP 工具名快照”（用于后续确认工具名保持不变）。
validation: markdownlint docs/references/2026-03-12_bug-and-perf-audit.md
validation: uv run python -c \
  "import asyncio; from paper_search_mcp.server import mcp; \
tools=asyncio.run(mcp.list_tools()); \
print('\\n'.join(t.name for t in tools))"
status: done
log: 2026-03-12 / orchestrator / dispatched via super-swarm
log: 2026-03-12 / worker / created audit report with risk grades and MCP snapshot
log: 2026-03-12 / worker / validation passed: `markdownlint docs/references/2026-03-12_bug-and-perf-audit.md`
log: 2026-03-12 / worker / validation passed: MCP tool snapshot command
files_changed: docs/references/2026-03-12_bug-and-perf-audit.md

### T3: 提供共享的安全路径与 HTTP 约定（供各适配器复用）

depends_on: [T0, T2]
reads: [paper_search_mcp, docs/SECURITY.md, .gitignore]
writes: [.gitignore]
creates: [paper_search_mcp/_http.py, paper_search_mcp/_paths.py]
mutex: scope:core-utils
description: 新增内部工具模块：默认超时/UA、重试退避、下载安全路径；
  先完成 T2 以保持审计快照一致。
acceptance: 适配器与 server 可通过共享函数得到一致的超时与安全路径行为。
acceptance: `_paths.py` 提供可机械验证的路径安全函数（路径穿越/绝对路径拒绝等）。
acceptance: `_paths.py` 默认下载目录为 `docs/downloads/`。
acceptance: 当下载目录不存在时会自动创建（不会因目录缺失报错）。
acceptance: `.gitignore` 忽略 `docs/downloads/`，避免提交下载产物。
validation: uv run python -m compileall paper_search_mcp
validation: uv run python -c \
  "from paper_search_mcp._paths import safe_download_root; print(safe_download_root())"
validation: uv run python -c \
  "import paper_search_mcp._paths as p; assert p.safe_download_root().is_dir()"
status: done
log: 2026-03-12 / orchestrator / dispatched via super-swarm after T0+T2
log: 2026-03-12 / worker / added shared `_paths.py` + `_http.py` and ignored `docs/downloads/`
log: 2026-03-12 / worker / validation passed: `uv run python -m compileall paper_search_mcp`
log: 2026-03-12 / worker / validated: `_paths.safe_download_root()` smoke checks
files_changed: .gitignore
files_changed: paper_search_mcp/_paths.py
files_changed: paper_search_mcp/_http.py

### T4: 修复 server 的 async 调用方式与并发安全

depends_on: [T3]
reads: [paper_search_mcp/server.py]
writes: [paper_search_mcp/server.py]
creates: []
mutex: file:paper_search_mcp/server.py
description: 避免阻塞事件循环；增加并发限制；对下载路径进行安全归一化。
acceptance: 在工具调用路径中不再创建无用的 `httpx.AsyncClient()`。
acceptance: 同步适配器通过 `asyncio.to_thread`（或等价）运行，
  不阻塞事件循环。
acceptance: 下载默认写入 `docs/downloads/`，且不会写出该目录。
acceptance: `save_path` 参数存在时也不会导致写出 `docs/downloads/`。
validation: uv run python -c \
  "import pathlib; \
t=pathlib.Path('paper_search_mcp/server.py').read_text(encoding='utf-8'); \
assert 'time.sleep' not in t"
validation: uv run python -m compileall paper_search_mcp tests
validation: uv run python -c \
  "import httpx, mcp, paper_search_mcp.server as s; print(s.mcp.name)"
status: done
log: 2026-03-12 / orchestrator / dispatched via super-swarm after T3
log: 2026-03-12 / worker / moved sync adapters behind `to_thread` + semaphore
log: 2026-03-12 / worker / normalized download/read save paths through `docs/downloads/`
log: 2026-03-12 / orchestrator / validated: server compiles; no sync-work client
log: 2026-03-12 / orchestrator / validation passed: import smoke printed `paper_search_server`
files_changed: paper_search_mcp/server.py

### T5: 适配器修复 A（arXiv + PubMed）

depends_on: [T3]
reads: [
  paper_search_mcp/academic_platforms/arxiv.py,
  paper_search_mcp/academic_platforms/pubmed.py,
]
writes: [
  paper_search_mcp/academic_platforms/arxiv.py,
  paper_search_mcp/academic_platforms/pubmed.py,
]
creates: []
mutex: scope:adapters-arxiv-pubmed
description: 增加超时/错误处理与安全文件名；减少潜在阻塞点与不一致行为。
acceptance: arXiv/PubMed 网络请求均有超时且对非 2xx 失败显式处理。
acceptance: arXiv 下载输出路径不会因输入导致路径穿越或目录不存在异常。
validation: uv run python -m compileall \
  paper_search_mcp/academic_platforms/arxiv.py \
  paper_search_mcp/academic_platforms/pubmed.py
status: done
log: 2026-03-12 / orchestrator / dispatched via super-swarm after T3
log: 2026-03-12 / worker / added shared timeouts and safe paths for arXiv/PubMed
log: 2026-03-12 / orchestrator / validated: arXiv/PubMed compileall passed
files_changed: paper_search_mcp/academic_platforms/arxiv.py
files_changed: paper_search_mcp/academic_platforms/pubmed.py

### T6: 适配器修复 B（bioRxiv + medRxiv）

depends_on: [T3]
reads: [
  paper_search_mcp/academic_platforms/biorxiv.py,
  paper_search_mcp/academic_platforms/medrxiv.py,
]
writes: [
  paper_search_mcp/academic_platforms/biorxiv.py,
  paper_search_mcp/academic_platforms/medrxiv.py,
]
creates: []
mutex: scope:adapters-biorxiv-medrxiv
description: 统一下载/读取的路径生成与错误处理；补齐缺失的安全与超时策略。
acceptance: 下载文件名对 DOI 等包含 `/` 的标识稳定且安全（不会创建意外目录）。
validation: uv run python -m compileall \
  paper_search_mcp/academic_platforms/biorxiv.py \
  paper_search_mcp/academic_platforms/medrxiv.py
status: done
log: 2026-03-12 / orchestrator / dispatched via super-swarm after T3
log: 2026-03-12 / worker / initial launch hit FD limit (`os error 24`)
log: 2026-03-12 / orchestrator / resumed locally; aligned bioRxiv/medRxiv
log: 2026-03-12 / orchestrator / validated: bioRxiv/medRxiv compileall passed
files_changed: paper_search_mcp/academic_platforms/biorxiv.py
files_changed: paper_search_mcp/academic_platforms/medrxiv.py

### T7: 适配器修复 C（Google Scholar + CrossRef）

depends_on: [T3]
reads: [
  paper_search_mcp/academic_platforms/google_scholar.py,
  paper_search_mcp/academic_platforms/crossref.py,
]
writes: [
  paper_search_mcp/academic_platforms/google_scholar.py,
  paper_search_mcp/academic_platforms/crossref.py,
]
creates: []
mutex: scope:adapters-scholar-crossref
description: 减少不必要的阻塞与不稳定标识；补齐请求超时与 429 退避策略的一致性。
acceptance: Google Scholar 的 `paper_id` 生成稳定（避免使用进程随机 hash）。
acceptance: CrossRef 429 退避不依赖阻塞 event loop（与 T4 的调用策略一致）。
acceptance: Google Scholar 不再使用 Python 内置 `hash()` 生成 `paper_id`。
validation: uv run python -m compileall \
  paper_search_mcp/academic_platforms/google_scholar.py \
  paper_search_mcp/academic_platforms/crossref.py
validation: uv run python -c \
  "import pathlib; \
p=pathlib.Path('paper_search_mcp/academic_platforms/google_scholar.py'); \
t=p.read_text(encoding='utf-8'); \
assert 'hash(' not in t"
status: done
log: 2026-03-12 / orchestrator / dispatched via super-swarm after T3
log: 2026-03-12 / worker / replaced Scholar `hash()` IDs; aligned retries
log: 2026-03-12 / orchestrator / validated: Scholar/CrossRef compileall passed
log: 2026-03-12 / orchestrator / validated: Scholar no longer uses `hash()`
files_changed: paper_search_mcp/academic_platforms/google_scholar.py
files_changed: paper_search_mcp/academic_platforms/crossref.py

### T8: 适配器修复 D（Semantic Scholar）

depends_on: [T3]
reads: [paper_search_mcp/academic_platforms/semantic.py]
writes: [paper_search_mcp/academic_platforms/semantic.py]
creates: []
mutex: file:paper_search_mcp/academic_platforms/semantic.py
description: 修复返回类型/错误处理不一致；补齐 timeout；
  清晰化 429 重试与 API key 行为。
acceptance: `request_api` 返回类型一致且调用方处理清晰，
  不再混用 dict/Response。
acceptance: 429 重试具备可解释的退避与最大尝试次数。
validation: uv run python -m compileall paper_search_mcp/academic_platforms/semantic.py
status: done
log: 2026-03-12 / orchestrator / started local integration after slot pressure
log: 2026-03-12 / orchestrator / made `request_api()` return JSON/`None`
log: 2026-03-12 / orchestrator / validated: Semantic compileall passed
files_changed: paper_search_mcp/academic_platforms/semantic.py

### T9: 适配器修复 E（IACR ePrint）

depends_on: [T3]
reads: [paper_search_mcp/academic_platforms/iacr.py]
writes: [paper_search_mcp/academic_platforms/iacr.py]
creates: []
mutex: file:paper_search_mcp/academic_platforms/iacr.py
description: 补齐下载/读取的路径安全与错误处理，并对 scraping 的失败场景更稳健。
acceptance: 下载与读取对 `paper_id` 中的 `/` 等字符可安全落盘，不写出下载目录。
validation: uv run python -m compileall paper_search_mcp/academic_platforms/iacr.py
status: done
log: 2026-03-12 / orchestrator / started local integration after slot pressure
log: 2026-03-12 / orchestrator / aligned IACR flows with shared helpers
log: 2026-03-12 / orchestrator / validated: IACR compileall passed
files_changed: paper_search_mcp/academic_platforms/iacr.py

### T12: Sci-Hub（可选敏感）安全姿态收敛

depends_on: [T3]
reads: [paper_search_mcp/academic_platforms/sci_hub.py, docs/SECURITY.md]
writes: [paper_search_mcp/academic_platforms/sci_hub.py]
creates: []
mutex: file:paper_search_mcp/academic_platforms/sci_hub.py
description: 移除默认的 `verify=False`，并把“不验证 TLS”变成显式 opt-in 行为。
note: T12 为可选敏感任务，不应阻塞 T10/T11；仅在需要时执行。
acceptance: 默认请求启用 TLS 校验；如需跳过校验必须通过环境变量显式开启。
acceptance: 写盘路径使用共享 `_paths.py` 规则，写入 `docs/downloads/`。
validation: uv run python -c \
  "import pathlib, re; \
p=pathlib.Path('paper_search_mcp/academic_platforms/sci_hub.py'); \
t=p.read_text(encoding='utf-8'); \
assert re.search(r'verify\\s*=\\s*False', t) is None"
validation: uv run python -m compileall paper_search_mcp/academic_platforms/sci_hub.py
status: deferred

### T10: 测试分层与默认验证减负

depends_on: [T4, T5, T6, T7, T8, T9]
reads: [tests, docs/RELIABILITY.md, docs/playbooks/validation.md]
writes: [
  tests/test_server.py,
  tests/test_arxiv.py,
  tests/test_biorxiv.py,
  tests/test_crossref.py,
  tests/test_google_scholar.py,
  tests/test_iacr.py,
  tests/test_medrxiv.py,
  tests/test_sci_hub.py,
  tests/test_semantic.py,
  tests/test.pubmed.py,
]
creates: [tests/test_pubmed.py, tests/test_paths.py]
mutex: scope:tests
description: 把 live-network 与重下载测试改为 opt-in；
  提供快速 smoke gate（默认验证不下载 10 个 PDF）。
acceptance: 默认测试/验证不执行大规模下载与易碎 scraping（除非显式开启）。
acceptance: 默认运行 `uv run python -m unittest discover -q` 不发起网络请求；
  live 测试必须通过环境变量显式启用（例如 `PAPER_SEARCH_LIVE_TESTS=1`）。
acceptance: PubMed 测试文件命名统一（`test_pubmed.py`），便于常见测试发现。
acceptance: 旧的 `tests/test.pubmed.py` 最终不存在（避免 `unittest` discovery 误导入）。
acceptance: 新增纯离线 `tests/test_paths.py`，覆盖路径穿越与非法路径输入。
acceptance: 默认下载目录为 `docs/downloads/`，且不会写出该目录。
validation: uv run python -m compileall tests
validation: uv run python -m unittest discover -q
validation: uv run python -m unittest -q tests.test_paths
validation: test ! -f tests/test.pubmed.py
status: done
log: 2026-03-12 / orchestrator / starting local test-layering and offline gate work
log: 2026-03-12 / orchestrator / rewrote default tests to stay offline
log: 2026-03-12 / orchestrator / validated: compileall, discover, paths, rename
files_changed: tests/test_server.py
files_changed: tests/test_arxiv.py
files_changed: tests/test_biorxiv.py
files_changed: tests/test_crossref.py
files_changed: tests/test_google_scholar.py
files_changed: tests/test_iacr.py
files_changed: tests/test_medrxiv.py
files_changed: tests/test_sci_hub.py
files_changed: tests/test_semantic.py
files_changed: tests/test_pubmed.py
files_changed: tests/test_paths.py

### T11: 文档补齐 + TODO 清单迁移（中文）

depends_on: [T1, T2, T4, T5, T6, T7, T8, T9, T10]
reads: [
  README.md,
  docs/PLANS.md,
  docs/SECURITY.md,
  docs/RELIABILITY.md,
  docs/playbooks/validation.md,
  docs/project-specs/source-capability-matrix.md,
  docs/exec-plans/tech-debt-tracker.md,
]
writes: [
  README.md,
  docs/PLANS.md,
  docs/SECURITY.md,
  docs/RELIABILITY.md,
  docs/playbooks/validation.md,
  docs/project-specs/source-capability-matrix.md,
  docs/QUALITY_SCORE.md,
]
creates: [docs/TODO.md]
mutex: scope:docs
description: 把 TODO 清单沉淀到 `docs/`（中文、可执行、带优先级）；
  同步安全/可靠性/验证与能力矩阵。
  TODO 来源：上游 README + 本仓库 git 历史线索（例如 `git log`）。
acceptance: `docs/TODO.md` 存在且内容为中文，
  包含优先级/负责人建议/验收方式。
acceptance: TODO 清单包含来源字段（上游 README + git 历史线索）。
acceptance: README/验证 playbook 指向正确的 uv 与测试分层命令。
acceptance: `docs/PLANS.md` 对应条目已更新并指向本 ExecPlan 与审计文档。
validation: markdownlint README.md docs/**/*.md
status: done
log: 2026-03-12 / orchestrator / started final docs pass after T1–T10
log: 2026-03-12 / orchestrator / updated README, docs, and TODO tracker
log: 2026-03-12 / orchestrator / validated: markdownlint README + docs passed
files_changed: README.md
files_changed: docs/PLANS.md
files_changed: docs/SECURITY.md
files_changed: docs/RELIABILITY.md
files_changed: docs/playbooks/validation.md
files_changed: docs/project-specs/source-capability-matrix.md
files_changed: docs/QUALITY_SCORE.md
files_changed: docs/TODO.md

## Plan of Work

1. Wave 1：基线与前置：T2（审计报告）+ T0（依赖/锁文件；无变更则 skipped）。
   T1（Docker uv）依赖 T0，可与 T2 并行。
2. Wave 2：共用约定与 server：T3（路径/HTTP 约定）→ T4（server 并发与 async）。
3. Wave 3：适配器并行修复：T5–T9。
4. Wave 4：测试减负与离线 gate：T10。
5. Wave 5：文档补齐：T11（含 `docs/TODO.md`）。
6. Wave 6（Optional）：T12（Sci-Hub）仅在明确需要时执行；默认 deferred 且不作为完成门槛。

注意事项：

- 不更改 MCP 工具名；如需调整参数语义（例如 `save_path`），需在文档与决策中明确。
- Sci-Hub 相关能力保持“可选且敏感”，默认不宣传、不作为主路径验收。
- 对 scraping 源（Scholar/IACR）优先做“可控失败 + 不阻塞”而非追求 100% 成功。

## Concrete Steps

1. From `[repo-root]`, run:

       uv sync --locked

2. Run Markdown validation (quote globs if your shell does not expand `**`):

       markdownlint AGENTS.md ARCHITECTURE.md README.md \
         docs/**/*.md codemap/**/*.md

3. Run offline Python checks:

       uv run python -m compileall paper_search_mcp tests
       uv run python -c "import httpx, mcp, paper_search_mcp.server as s; print(s.mcp.name)"
       uv run python -m unittest discover -q

4. (Optional, opt-in) Run live-network tests for a specific adapter only when
   it changed:

       PAPER_SEARCH_LIVE_TESTS=1 uv run python -m unittest -q tests.test_arxiv

5. (If Dockerfile changed) Validate container build/run:

       docker build -t paper-search-mcp .
       docker run --rm paper-search-mcp python -c \
         "from paper_search_mcp.server import mcp; print(mcp.name)"

   Manual (not a gate):

       docker run --rm paper-search-mcp python -m paper_search_mcp.server

## Validation and Acceptance

Baseline gate (required):

- `markdownlint` passes on changed Markdown.
- `uv run python -m compileall paper_search_mcp tests` passes.
- `uv run python -c "import paper_search_mcp.server as s; print(s.mcp.name)"`
  prints `paper_search_server`.
- Prefer `uv run` in docs; avoid `.venv/bin/python` for portability.

Runtime gate (when server/adapters changed):

- Tool calls return quickly (no obvious event-loop blocking for simple queries).
- Downloads land under `docs/downloads/` and do not escape the directory.

Integration gate (opt-in, targeted):

- Run the relevant single-adapter tests for the modified source(s),
  acknowledging upstream flakiness.

## Idempotence and Recovery

- `uv sync --locked` is safe to rerun; it should converge `.venv` to `uv.lock`.
- Adapter changes are localized per-file; if a source breaks, revert that
  adapter file and keep others.
- Docker build changes can be tested independently; if broken, revert
  `Dockerfile` and `.dockerignore`.

## Revision Notes

- 2026-03-12 / orchestrator — Created initial swarm ExecPlan for uv + bug/perf
  and docs work.
