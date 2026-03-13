# TODO

本清单把上游 README 的 TODO 和本仓库的 git 历史线索迁移到 `docs/`。
目标不是保留一个会过期的愿望清单，而是保留下一步可执行的事项。

## 来源

- 上游 README TODO：`origin/main:README.md`
- 历史提交：`c37c3e3 add todo`
- 适配器扩展线索：`2dcf241`、`d701d9c`、`ba9c81b`、`a4ad325`、`53c34a6`

## P0

### 为主要适配器补齐离线 fixture 或 contract tests

- 建议负责人：`maintainer / runtime`
- 验收方式：至少为 `arxiv`、`pubmed`、`crossref`、`semantic`、`iacr`
  各补一条不依赖网络的解析或契约测试；`uv run python -m unittest
  discover -q` 继续保持离线。
- 来源：git 历史显示近几轮工作持续新增来源，测试仍以 live 为主。

### 收敛公共适配器接口

- 建议负责人：`maintainer / runtime`
- 验收方式：明确一个共享接口或协议，并把重复骨架迁移过去；若暂不
  处理，则在 docs 中写清为何继续保留重复实现。
- 来源：git 历史显示适配器数量持续增加，重复代码会继续放大维护成本。

## P1

### 增加 PubMed Central (`PMC`) 适配器调研或实现

- 建议负责人：`maintainer / source-owner`
- 验收方式：输出能力结论，至少说明 `search`、`download`、`read`
  哪些支持；若实现，则补齐测试和能力矩阵。
- 补充说明（占位但诚实）：优先做一个可合并的 v1：`search: yes`；同时
  提供 `download_pmc` / `read_pmc_paper` 的占位工具，直接返回明确限制
  信息（能力矩阵仍标记 `download: no`、`read: no`）。
- 未实现 / 遗憾：真正的全文下载/阅读（即便只做 OA 子集）仍需要处理许可
  判定、限流/重试策略、格式差异（PDF/JATS/补充材料）与离线 fixture
  维护成本；建议另起 ExecPlan 单独推进。
- 来源：上游 README TODO。

### 评估下一批高价值来源

- 建议负责人：`maintainer / source-owner`
- 验收方式：为 `Science Direct`、`Springer Link`、`IEEE Xplore`、
  `ACM Digital Library` 各产出一条可执行结论：实现、延期，或明确
  阻塞原因。
- 来源：上游 README TODO。

## P2

### 建立长期候选来源清单的准入规则

- 建议负责人：`maintainer / docs`
- 验收方式：为 `Web of Science`、`Scopus`、`JSTOR`、`ResearchGate`、
  `CORE`、`Microsoft Academic` 替代面各补一条准入说明，覆盖许可
  风险、抓取稳定性，以及是否值得进入默认支持面。
- 来源：上游 README TODO。

### 为“继续扩源”写一页简短 playbook

- 建议负责人：`maintainer / docs`
- 验收方式：说明最小实现面，包括能力矩阵、测试要求、文档要求和
  敏感来源边界。
- 来源：git 历史显示来源扩展频繁，缺统一落地模板。

## 已完成但需要持续维护

- `Google Scholar`、`Semantic Scholar`、`bioRxiv`、`medRxiv` 已从上游
  TODO 进入当前支持面。
- `IACR ePrint Archive`、`CrossRef`、可选 `Sci-Hub` 也已在 git 历史中补入。
- 后续不要再把根 README 当成长期 TODO 仓库；维护入口改为本文件。
