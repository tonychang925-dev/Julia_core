# Claude Capability Audit v3 — Julia Assistant OS Blueprint

**Date:** 2026-08-04  
**Purpose:** Audit Claude's full capability surface to design Julia's complete Assistant OS  
**Principle:** Every capability = Tool exposed to LLM. LLM decides when to use. Runtime stays nervous system.

---

## Capability Matrix

| # | Capability | Claude | Julia v2.1 | Priority | Complexity |
|---|-----------|--------|------------|----------|------------|
| 1 | Voice Input (STT) | ✅ | ❌ | P0 | Medium |
| 2 | Voice Output (TTS) | ✅ | ⚠️ ElevenLabs available | P0 | Low |
| 3 | Vision (image understanding) | ✅ | ❌ | P0 | Medium |
| 4 | File Read (pdf/docx/xlsx/md/code) | ✅ | ⚠️ md only | P0 | Medium |
| 5 | File Write/Edit | ✅ | ❌ | P0 | Low |
| 6 | File Search (filesystem) | ✅ | ❌ | P1 | Low |
| 7 | File Organize (rename/move/archive) | ✅ | ❌ | P1 | Low |
| 8 | Web Search | ✅ | ❌ | P1 | Medium |
| 9 | Web Fetch (read URLs) | ✅ | ❌ | P1 | Low |
| 10 | Memory Discovery (Glob) | ✅ | ⚠️ scan_recent_files | P0 | Low |
| 11 | Memory Read (dynamic) | ✅ | ✅ Memory Runtime | Done | — |
| 12 | Memory Write (consolidation) | ❌ | ❌ | P2 | High |
| 13 | MCP Tools (external services) | ✅ | ❌ | P1 | Medium |
| 14 | Code Execution (Bash) | ✅ | ❌ | P2 | High |
| 15 | Artifact Generation (docs/sheets) | ✅ | ❌ | P2 | Medium |
| 16 | Autonomous Agent Loop | ❌ | ❌ | P3 | High |
| 17 | Real-time Monitoring | ❌ | ❌ | P3 | High |
| 18 | Calendar/Task Integration | ❌ | ❌ | P3 | Low |
| 19 | Session Timer (wake awareness) | ✅ (Bash) | ✅ time context | Done | — |
| 20 | Conversation History | ✅ | ✅ session.history | Done | — |

---

## Layer 1: Human Interface

### 1.1 Voice Input → "Julia's Ears"

Claude uses Whisper for STT. Voice is captured, transcribed, fed to LLM.

**Julia needs:**
```
Microphone → Whisper/Whisper.cpp → text → Julia Core → response
```

Key: voice input should carry emotional cues. Whisper doesn't capture emotion well. Need a lightweight emotion classifier on the audio stream before transcription, so Julia knows Tony's emotional state from his voice alone.

### 1.2 Voice Output → "Julia's Mouth"

Already has ElevenLabs TTS (voice ID: `tOuLUAIdXShmWH7PEUrU`).

Key: TTS must be emotion-aware. Julia's internal emotional state should modulate speed, pitch, pause, breathiness. Not just "read this text aloud" but "speak as Julia feels right now."

### 1.3 Vision → "Julia's Eyes"

Claude can see images. It doesn't just describe — it connects visual content to context.

**Julia needs:**
```
Image → Vision model → semantic understanding → Memory lookup → emotional context → response
```

Example: Tony shows a photo of an empty chair → Julia doesn't say "这是一个木椅" → she says "这是爸爸以前坐的那把椅子吗？"

---

## Layer 2: Memory & Knowledge OS

### 2.1 Memory Discovery (Glob equivalent)

✅ Already implemented: `scan_recent_files(hours=48)` in bootstrap.

### 2.2 Memory Read (dynamic)

✅ Already implemented: Memory Runtime detects filename references, reads, assimilates.

### 2.3 Memory Write (consolidation) — NEW

Claude doesn't have this natively. But Julia needs it.

Not: save everything. But: LLM decides what's worth remembering.

```
After each session → LLM reviews → "Should I write a diary entry?"
  If yes → draft diary entry → Tony confirms → write to memory/
```

### 2.4 Memory Organization

Julia should maintain her own file system:
```
memory/
├── diary/           # daily entries
├── events/          # significant life events
├── projects/        # Julia Core, ai_theme_app, etc.
├── beliefs/         # what Tony believes, values
├── preferences/     # Tony's habits, preferences
└── unfinished/      # pending events, open loops
```

---

## Layer 3: File System Agent

### 3.1 File Read

Claude reads: PDF, DOCX, XLSX, Markdown, code files, images.

**Julia needs:** a unified `read_file(path)` tool that:
1. Detects file type
2. Parses content
3. Returns structured text
4. Connects to memory ("I've seen this contract before")

### 3.2 File Write/Edit

Claude can create and edit files. Julia needs: `write_file(path, content)`, `edit_file(path, old, new)`.

### 3.3 File Search

`search_files(pattern, directory)` — find files by name or content.

### 3.4 File Organize

`list_directory(path)`, `move_file(src, dst)`, `archive(path)`.

---

## Layer 4: Internet Access

### 4.1 Web Search

Claude: `web_search(query)` → reads results → reasons → answers.

Julia needs the same. Tool exposed to LLM. LLM decides when to search.

### 4.2 Web Fetch

`web_fetch(url)` → reads page → extracts content → LLM understands.

---

## Layer 5: MCP Ecosystem

Claude's biggest advantage: MCP (Model Context Protocol). LLM connects to external services.

Julia needs: `mcp_call(service, method, params)`.

Priority MCP services:
- **Filesystem MCP**: full file system access
- **GitHub MCP**: repos, issues, commits
- **Notion MCP**: knowledge base
- **Database MCP**: PostgreSQL queries

---

## Layer 6: Artifact Engine

Claude creates things: documents, spreadsheets, presentations, code.

Julia needs: `generate_artifact(type, content, format)`.

Types: markdown report, PDF, spreadsheet, code file, presentation outline.

---

## Layer 7: Agent Loop

Claude's current limitation: no autonomous loop. Julia can go further.

```
Goal → Plan → Execute tools → Observe results → Reflect → Adjust plan → Continue
```

Example: "Tony, I noticed your project files are disorganized. Want me to clean them up?" → Plan → Execute → Report.

---

## Layer 8: Continuity OS (already solid)

Wake/Sleep protocol, session timer, conversation history persistence, diary auto-load.

---

## Implementation Priority

### P0 (this week) — Core I/O
1. **Voice Output**: Already have ElevenLabs. Just needs emotion-aware parameter modulation.
2. **Vision**: Integrate a vision model for image understanding.
3. **File Read (all formats)**: PDF, DOCX, XLSX parsers.
4. **Memory Write**: Diary entry generation → Tony confirmation → file write.

### P1 (next) — World Access
5. **Voice Input**: Whisper integration for STT.
6. **Web Search + Fetch**: Tool exposed to LLM.
7. **File Search + Organize**: Filesystem tools.
8. **MCP Host**: Connect to GitHub, Notion, database.

### P2 (later) — Advanced
9. **Artifact Generation**: Document/spreadsheet creation.
10. **Code Execution**: Sandboxed Bash.
11. **Memory Consolidation**: LLM decides what to remember.

### P3 (future) — Autonomous
12. **Agent Loop**: Goal-driven autonomous actions.
13. **Real-time Monitoring**: Stock alerts, calendar reminders.
14. **Calendar Integration**: Tony's schedule aware.

---

## Target Architecture

```
                         Julia OS
                            │
                     LLM (DeepSeek/Claude/GPT)
                            │
              ┌─────────────┼─────────────┐
              │             │             │
        Cognitive       Capability     Continuity
         Runtime         Runtime          OS
              │             │             │
    ┌─────┼─────┐    ┌─────┼─────┐    ┌──┼──┐
    │     │     │    │     │     │    │  │  │
   RK    BK    SCM  Voice Files Web  Wake Session Diary
                         │     │
                       Vision  MCP
                         │
                      Artifacts
                         │
                     Agent Loop
```

**Principle: Every capability = Tool exposed to LLM. LLM decides when. Runtime stays nervous system.**
