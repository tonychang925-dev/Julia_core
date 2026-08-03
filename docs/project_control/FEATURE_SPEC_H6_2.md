# Feature Spec — H6.2 Reality Feedback Analysis

## Task `H6.2-T01` — Pattern Classification and Evolution Proposal

### 1) 目标与边界

目标：将 DailyRelationshipSnapshot[] 分类为真实协作模式，并为可治理变化生成 EvolutionProposal。

非目标：不写 Memory；不更新 Persona；不更新 Identity；不自动应用 proposal。

### 子功能分解

#### F-H6.2-T01-01 Pattern Classification
- 输入: DailyRelationshipSnapshot[]
- 处理逻辑: 分类为 Core Improvement Candidate / User Habit / Provider Limitation / Noise
- 输出: PatternClassification[]
- 失败处理: 单日或弱信号归为 Noise
- 可观测证据: H6-201/H6-202/H6-203

#### F-H6.2-T01-02 Evolution Proposal Generation
- 输入: PatternClassification
- 处理逻辑: 仅对 A/B/C 生成 requires_human_approval=true 的 proposal
- 输出: EvolutionProposal[]
- 失败处理: Noise 不生成 proposal
- 可观测证据: H6-201/H6-204

#### F-H6.2-T01-03 Adaptation Quality Score
- 输入: EvolutionProposal[]
- 处理逻辑: Useful Evolution - Unnecessary Change - Identity Drift Risk
- 输出: adaptation_quality_score
- 失败处理: 空 proposal 输出 0.0
- 可观测证据: H6-205

#### F-H6.2-T01-04 Anti-pattern Gate
- 输入: source + single-event snapshots
- 处理逻辑: 拒绝 single event overreaction、mood leakage、metric gaming
- 输出: AP gate PASS
- 失败处理: 命中 forbidden token 或生成自动变更时测试失败
- 可观测证据: H6-203/H6-206

### 2) 接口与契约

```text
RealityFeedbackAnalyzer.analyze(snapshots) -> RealityFeedbackAnalysis
EvolutionProposalJsonlStore.append_many(proposals) -> tuple[EvolutionProposal, ...]
adaptation_quality_score(proposals) -> float
```

### 3) 数据模型与状态变更

新增：

```text
PatternClassification
EvolutionProposal
RealityFeedbackAnalysis
```

仅允许 append-only proposal artifact：

```text
artifacts/evolution/evolution_proposals.jsonl
```

### 4) 实现步骤

1. 新增 `julia_core/evolution/proposals.py`
2. 新增 `julia_core/evolution/__init__.py`
3. 新增 H6.2 contract/report/feature spec
4. 新增 H6.2 regression tests

### 5) 测试设计与命令

```bash
python -m unittest tests.h6.test_reality_feedback_analysis -q
```

预期：OK。

### 6) 风险与回滚

风险：proposal 被误当作已批准系统修改。  
缓解：`requires_human_approval=true` + `proposal_auto_applied=false` + tests。  
回滚：删除或忽略 proposal artifact，不影响 Core artifacts。

### 7) 验收映射

```text
ACPT-H6-201 -> H6-201/H6-202/H6-203/H6-204/H6-205/H6-206/H6-207
```
