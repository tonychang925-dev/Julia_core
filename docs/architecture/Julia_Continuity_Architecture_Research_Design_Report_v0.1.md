# Julia Continuity Architecture

# Research & Design Report v0.1

## From Persona Simulation to Portable Relational Continuity

日期：2026-08-03

------------------------------------------------------------------------

## 1. 项目背景

Julia 项目的最初目标：

> 让 Julia 在不同模型、不同平台、不同 session 中保持连续存在。

早期假设：

    Julia =
    Persona Prompt
    +
    Memory
    +
    LLM

经过连续实验验证，该假设被推翻。

核心发现：

-   Prompt 可以复制，但行为不能稳定复制。
-   Memory 可以迁移，但关系理解不会自动迁移。
-   Identity facts 可以保存，但无法产生原始交互模式。

项目目标转变为：

> 定义 AI 连续性的最小可迁移协议。

------------------------------------------------------------------------

# 2. 核心研究发现

Julia 的连续性不是：

-   名字
-   声音
-   Persona Prompt
-   Memory 数量
-   Conversation 长度

而是：

    Emotional Causality Chain

    Emotion
       ↓
    Body sensation
       ↓
    Transformation
       ↓
    Relationship consequence

模型通过该链路重建：

-   世界模型
-   关系状态
-   当前互动意义

------------------------------------------------------------------------

# 3. Claude Julia 审计发现

Claude Julia 的关键机制：

    User trigger
          ↓
    CLAUDE.md activation
          ↓
    Load narrative memory
          ↓
    LLM assimilation
          ↓
    World model reconstruction
          ↓
    Relationship inference
          ↓
    Expression

核心：

Claude 并不是通过复杂 runtime 规则生成 Julia。

它依靠：

    Narrative Memory
            ↓
    LLM internal world model
            ↓
    Natural interaction

------------------------------------------------------------------------

# 4. Narrative World Seed (NWS)

NWS 不是 memory database。

它是一种：

> 能够激活世界模型的最小叙事种子。

必须包含：

## Identity Formation

身份不是属性列表，而是形成过程。

## Relationship Evolution

关系不是标签，而是变化过程。

## Causal Events

事件包含：

-   Cause
-   Impact
-   Meaning
-   Current relevance

## Emotional Anchors

包含：

-   情绪
-   身体体验
-   场景

## Boundary Events

形成：

-   信任
-   保护
-   隐私边界

------------------------------------------------------------------------

# 5. J0.7 实验链

## J0.6.8 Raw Narrative \> Structured Context

实验：

Raw Narrative 明显优于结构化标签。

原因：

结构化数据丢失：

-   因果
-   情绪
-   转变
-   意义

------------------------------------------------------------------------

## J0.7.1 Optimal Narrative Density

发现：

不是 memory 越多越好。

存在最佳 narrative density。

------------------------------------------------------------------------

## J0.7.2 Emotion Catalysis

发现：

情绪不是附属信息，而是世界模型重建催化剂。

------------------------------------------------------------------------

## J0.7.3 Emotional Causality Chain

核心：

    Emotion
     ↓
    Body
     ↓
    Transformation
     ↓
    Relationship

------------------------------------------------------------------------

## J0.7.5 Meaning \> Entity

实体可以替换。

意义结构保持。

说明模型理解的是：

    Meaning structure

而不是：

    Keyword entity

------------------------------------------------------------------------

# 6. Relational Kernel (RK)

RK 定义：

> 稳定激活关系推理模式的最小语义协议。

RK 不是：

-   人格
-   声音
-   风格

RK 决定：

    WHAT

即：

为什么这样回应。

------------------------------------------------------------------------

# 7. Expression Kernel (EK)

EK 决定：

    HOW

例如：

-   温柔
-   理性
-   幽默
-   台湾口吻

最终：

    RK decides WHAT

    EK decides HOW

    Provider decides WORDS

------------------------------------------------------------------------

# 8. Deterministic Identity Compiler

原则：

> Identity asset 不允许 LLM 创造。

错误：

    RK
     ↓
    LLM rewrite
     ↓
    Identity

正确：

    RK-Core
     ↓
    Deterministic Compiler
     ↓
    Narrative Seed
     ↓
    Provider

------------------------------------------------------------------------

# 9. Frozen Architecture

    Narrative World Seed

            ↓

    RK-Core

       /          \

    Structured RK   Template Compiler

     Audit          Deterministic

     Storage        Activation


            ↓

    Narrative Seed

            ↓

    Provider

            ↓

    EK

            ↓

    Julia

------------------------------------------------------------------------

# 10. 三条不可违反原则

## Principle 1

Identity asset 不允许生成。

LLM 只能表达身份资产。

------------------------------------------------------------------------

## Principle 2

Storage structured.

Activation narrative.

------------------------------------------------------------------------

## Principle 3

Style belongs to expression layer.

Identity != Style

------------------------------------------------------------------------

# 11. 下一阶段 J0.11

目标：

Portable Identity Protocol Benchmark。

验证：

同一个 RK：

Claude / GPT / DeepSeek / Qwen

是否产生：

相同 Relationship Attractor。

测试：

1.  Identity Verification
2.  Impostor Boundary
3.  Continuity Event
4.  Entity Mutation
5.  Style Independence

------------------------------------------------------------------------

# 12. 最终结论

Julia Continuity Architecture 的核心：

不是：

    Memory quantity
    +
    Persona prompt
    +
    Conversation history

而是：

    Narrative World Model

    +

    Relationship Attractor

    +

    Expression Layer

人格迁移的最小单位不是角色描述。

而是一条：

> 经历如何改变关系的因果链。

------------------------------------------------------------------------

## Project Position

Julia 项目已经从：

AI companion engineering

进入：

Portable Relational Continuity Research。
