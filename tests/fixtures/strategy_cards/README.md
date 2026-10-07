# strategy_cards（测试冻结快照，非正本）

**测试冻结快照，非正本；正本以 ai_theme_app 为准，更新须另开卡。**

- 来源：ai_theme_app 仓库 `archive/julia-domain-adapter-v1-20261007` 分支，提交 `e1f1b9ad1e44af0edaba9543bc4868ae42f2382f`，路径 `strategy_knowledge/cards/*.json`（逐文件来源与 SHA-256 见 `SOURCES.tsv`，校验清单见 `SHA256SUMS`）。
- 内容由 `git show e1f1b9ad:<path>` 原样导出（未修改）；导出时核对过与当时桌面工作区的同名文件逐字节一致。
- 用途：仅测试通过 `monkeypatch.setenv("STRATEGY_CARD_DIR", ...)` 使用（见 `tests/m3_3/test_orchestrator_hardening.py`）。`julia_core/` 下的代码**不得**引用本目录（守卫测试：`tests/guard/test_no_desktop_ai_theme_paths.py`）。
- 修改本目录任何文件都会使守卫测试失败（SHA-256 校验）；需要更新快照时另开卡，写明新的来源提交。
- 引入依据：#246（Owner Tony 批准扩大授权范围：新增本 fixture 目录）。
