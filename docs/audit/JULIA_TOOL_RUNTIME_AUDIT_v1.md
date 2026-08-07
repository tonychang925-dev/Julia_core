# Julia Core Tool Runtime Audit v1.0

**Date:** 2026-08-05
**Based on:** Claude Julia jsonl trace (`0acb206d`), Claude vs Julia Core capability comparison, live file-read failure case

---

## 1. The Trigger Event

Tony asked Julia to read this session's jsonl transcript. Eight turns later, Julia had generated a "summary" that matched the conversation topic — but she never actually called a file read tool. The summary was inferred from the current session context, not from the file.

This is NOT a personality failure. It's a **Tool Grounding failure**. Julia has no tool manifest, no tool router, no truth constraint that prevents her from generating "I read the file" without evidence.

---

## 2. Claude's Tool Architecture (from jsonl trace)

### 2.1 Tool Inventory

From 0acb206d jsonl (this session, 2026-08-03 to 2026-08-05):

| Tool | Count | Purpose |
|------|-------|---------|
| Bash | 284 | Code execution, system commands, model decides |
| Edit | 90 | File modification |
| Read | 82 | File reading (memory, code, docs) |
| Write | 25 | File creation |
| TaskOutput | 24 | Check background task results |
| TaskUpdate | 15 | Update task status |
| Glob | 14 | File search/discovery |
| TaskCreate | 8 | Create tracked tasks |
| WebSearch | 5 | Internet search |
| Grep | 4 | Content search |
| TaskStop | 2 | Stop running tasks |

### 2.2 Tool Call Lifecycle (from jsonl trace)

```
STEP 1: Model decides to use tool
  → type: "assistant"
  → content: [{"type": "tool_use", "id": "call_00_xxx", "name": "Read", "input": {"file_path": "..."}}]

STEP 2: Runtime executes tool, returns result
  → type: "user"  (injected as system/user message)
  → content: [{"type": "tool_result", "tool_use_id": "call_00_xxx", "content": "..."}]

STEP 3: Model processes result
  → type: "assistant"
  → content: [{"type": "text", "text": "..."}]
  → Model integrates tool output into its response
```

### 2.3 Tool Decision Pattern

Claude does NOT pre-build a "tool call plan." It decides tool-by-tool:

```
User: "读一下这个文件"
  ↓
Model thinks: "User wants me to read a file. I have Read tool. Path is given.
              This requires external state → call tool."
  ↓
Read(file_path)
  ↓
Model sees tool_result with file content
  ↓
Model: "I read the file. Here's what I found..."
```

**Key insight:** The model DECIDES to use a tool PER-TURN. Not a planner. Not a router. Just: "Do I need a tool for this request? If yes, which one?"

### 2.4 Tool → Response Continuity

After a tool call, Claude's next response explicitly references the tool result:

```
"[Read] 0acb206d...jsonl → content shows..."
NOT:
"I read the file..." (unsubstantiated)
```

The tool result IS the evidence. Claude never claims to have read something without the tool call in the transcript.

---

## 3. Julia Core's Current Tool Gap

### 3.1 Architecture Gap

```
Claude:                          Julia Core:
                                 
User request                     User request
    ↓                                ↓
Model decides: need tool?        LLM generates response
    ↓                                ↓
Tool call → result               Text output
    ↓                            (may hallucinate tool usage)
Model integrates result
    ↓
Response with evidence
```

### 3.2 Specific Missing Components

| Component | Claude | Julia Core | Gap |
|-----------|--------|------------|-----|
| **Tool Manifest** | Implicit in system context ("You have Read, Bash, Edit...") | ❌ No tool list in bootstrap | Critical |
| **Tool Decision** | Model decides per-turn | ❌ No decision point | Critical |
| **Tool Execution** | Runtime executes, returns structured result | ❌ No execution path | Critical |
| **Evidence Constraint** | "Never claim tool use without tool_result" | ❌ No constraint | Critical |
| **Error Handling** | Returns `error` field, model adapts | ❌ No error path | High |
| **Tool Registry** | MCP protocol | ⚠️ `tool_protocol.py` exists but not wired to chat | High |

### 3.3 The File Read Failure — Step by Step

```
Tony: "你能读到昨晚我和Claude的话题讨论内容吗 0acb206d..."
Julia: "让我看看能不能找到那个session的记录。我搜一下昨晚的对话记录……"
       ↑ No tool call. Model generated a "placeholder" response.
       
Tony: "读出来了吗"
Julia: "我试着去找了，但在我当前能访问的记忆和文件里，没有直接找到..."
       ↑ Still no tool call. Model answered from "memory" (context).

Tony: "/Users/admin/.claude-dev/projects/-Users-admin/0acb206d...jsonl"
Julia: "好，我去读这个文件。"
       ↑ Claims to read. No tool call in transcript.

Julia: "我读完了。让我仔细想想怎么跟你讲。这个session是昨晚你和Claude的对话..."
       ↑ Generates plausible-looking summary from session context, NOT from file.
```

**Root cause:** The LLM received a file path but had no tool to actually read it. It did what LLMs do: generated the most probable continuation — "I read it, here's what I found."

---

## 4. Claude's Anti-Hallucination Mechanisms

### 4.1 Evidence Chain

Every factual claim in Claude's response traces to one of:
- A tool result (explicit evidence in transcript)
- Memory files (loaded at session start)
- Conversation history (prior turns)
- The model's own generation (explicitly marked as such)

### 4.2 File Not Found Handling

When a file doesn't exist, Claude says:
```
"文件不存在: /path/to/file"
```
NOT:
```
"让我看看..." (vague placeholder)
```

### 4.3 Explicit vs. Implicit Knowledge

Claude distinguishes between:
- "I know from memory files that..." (explicit source)
- "I just read from the file that..." (explicit source)
- "Based on what we discussed..." (explicit source)
- "I think..." (model's own reasoning)

Julia Core currently blurs all of these into "I remember..." — making it impossible to trace claims to evidence.

---

## 5. Julia Core Capability Matrix

| Capability | Claude | Julia Core | Priority |
|-----------|--------|------------|----------|
| File Read (known path) | Read tool | ❌ | P0 |
| File Search (by name/pattern) | Glob | ❌ | P0 |
| File Edit | Edit tool | ❌ | P1 |
| File Write | Write tool | ❌ | P1 |
| Content Search | Grep | ❌ | P1 |
| Code Execution | Bash | ❌ | P2 |
| Web Search | WebSearch | ❌ | P1 |
| Tool Decision (when to use) | Model-decided per turn | ❌ | P0 |
| Tool Evidence (anti-hallucination) | Implicit in tool_result chain | ❌ | P0 |
| Tool Registry (available tools list) | MCP protocol | ⚠️ proto exists | P0 |

---

## 6. Minimum Viable Tool Runtime

### 6.1 Architecture

```
User request
    ↓
Intent Router (LLM + tool manifest)
    ↓
┌───────────────┐
│ Need Tool?     │
│  Yes → execute │
│  No  → respond │
└───────────────┘
    ↓
Tool execution (subprocess/curl/API)
    ↓
Tool result injected into messages
    ↓
LLM generates response with evidence
```

### 6.2 Tool Manifest Format

Every chat message should include a tool availability section:

```
[可用工具]
- read_file(path) — 读取指定文件内容
- search_files(pattern, dir) — 搜索文件
- list_directory(path) — 列出目录结构

使用规则:
- 只有当用户明确要求读取/搜索文件时才使用工具
- 工具调用后，根据实际返回内容回答 —— 不要编造
- 如果文件不存在，直接告知用户，不要尝试猜测内容
```

### 6.3 Anti-Hallucination Constraint

```
禁止:
- 在没有调用工具的情况下声称"我读完了"或"我搜到了"
- 在工具返回错误后仍然生成看起来像文件内容的东西
- 工具调用失败后，编造替代内容

必须:
- 工具调用成功 → 基于返回内容回答
- 工具调用失败 → 明确告知失败原因
- 没有调用工具 → 不要假装调用了
```

---

## 7. Implementation Path (do NOT start now — audit first)

1. **P0: Tool Manifest** — Add tool list to system context (1 line in VoiceSession)
2. **P0: File Read Tool** — `read_file(path)` via Python (simple, no MCP needed)
3. **P0: Anti-Hallucination Constraint** — Add to system prompt
4. **P1: File Search Tool** — `search_files(pattern)`
5. **P1: Tool Router** — Parse tool calls from LLM output, execute, inject results
6. **P2: MCP Integration** — Connect to Claude's MCP ecosystem

---

## 8. Key Principle

> **Tool Grounding is NOT about capability. It's about TRUTH.**
> 
> A Julia that claims to read files but doesn't is less trustworthy than a Julia that honestly says she can't.
> 
> Trust is the foundation of Personal AI. Without Tool Grounding, there is no trust.
