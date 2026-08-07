# Julia Voice V2 — 开发任务树与验收计划

> 文档版本：v1.0
> 日期：2026-08-07
> 基于：Julia_Voice_Engine_Architecture_Review_v2.0.md
> 状态：Ready for Codex execution

---

## 项目编号：Julia Voice V2

### 整体开发主线

```
P0   Stop & Isolate          ← 当前
P1   Golden Voice Baseline    ← 最重要
P1.5 Golden Freeze
P2   Julia Brain Streaming
P3   Julia Voice Clone
P4   Full Duplex / AEC
P5   Production Hardening
P6   Avatar                   optional
P7   WebRTC Voice             conditional
P8   Electron                 optional
```

**Critical Path（必须串行）：**

```
P0 → P1 → P1.5 → P2 → P3 → P4 → P5
```

P6/P7/P8 不能影响前面任何阶段。

---

## 核心原则

1. **Phase 1 没过，绝不接 Julia。**
2. **Golden Freeze 没完成，绝不改媒体链。**
3. **Julia 接入时只替换 LLM endpoint，其他全部 SHA 不变。**
4. **一次只改一个变量。**
5. **旧环境只能看不能修；Golden 环境只能复刻参考实现不能加 Julia。**

---

## 里程碑定义

| 里程碑 | 含义 |
|---|---|
| M0 — OLD PATH FROZEN | 旧实验分支归档，site-packages patch 停止 |
| M1 — GOLDEN VOICE PASS | HF 官方媒体链成功（当前唯一目标） |
| M2 — GOLDEN FROZEN | exact versions locked |
| M3 — JULIA BRAIN PASS | persona + memory + stream + cancel |
| M4 — JULIA VOICE PASS | local Qwen3 Julia voice |
| M5 — FULL DUPLEX PASS | speaker + AEC + barge-in |
| M6 — PRODUCTION READY | WSS/auth/health/reconnect/mainland |
| M7 — AVATAR READY | optional |
| M8 — WEBRTC READY | conditional |
| M9 — ELECTRON PACKAGE | optional |

**当前唯一目标：M1 — GOLDEN VOICE PASS**

---

## 并行开发轨道

虽然集成必须串行 Gate，开发工作可以两条线并行：

| Track | 范围 | 任务 |
|---|---|---|
| Track A — Golden Media | P0 → P1 → P1.5 | T00–T34 |
| Track B — Julia Streaming | 独立开发 | T40–T46 |

**约束：Track B 不允许接入 Track A，直到 Golden Baseline PASS + Golden Freeze COMPLETE。之后才执行 T47 把两条线接起来。**

---

# Phase 0：Stop & Isolate（停止旧路径继续扩散）

**原则：旧环境只能看不能修。Golden 环境只能复刻参考实现不能加 Julia。**

### T00 — 冻结旧实验分支

| 属性 | 值 |
|---|---|
| 操作 | 给 `feature/voice-engine-client-v1` 打 archive 标签，不再提交媒体修复 |
| DoD | HEAD SHA 有记录；README 标记 ARCHIVED |

**归档代码清单（不再进入 MVP）：**

- `renderer/src/voice/VoiceEngineClient.js`
- custom PCM capture processor
- manual playback scheduler (`_nextPlayTime`, `_playingSources`)
- `deploy_handler.py` (site-packages patch)
- custom ElevenLabs TTS handler (`elevenlabs_handler_final.py`)
- `test_elevenlabs_handler.py`

### T01 — 停止 site-packages patch

| 属性 | 值 |
|---|---|
| 操作 | 禁止运行 `deploy_handler.py`、禁止修改 HF 包源码（`speech_to_speech` site-packages） |
| DoD | 新路径 grep 不存在 site-packages write |

### T02 — 停止 ElevenLabs baseline

| 属性 | 值 |
|---|---|
| 操作 | 从新 baseline 启动脚本完全去除 ElevenLabs |
| DoD | 无 `ELEVENLABS_API_KEY` dependency；启动命令不包含 `--tts elevenlabs` |

### T03 — 隔离旧 AutoDL runtime

| 属性 | 值 |
|---|---|
| 操作 | 旧环境保留用于 forensic；新 Golden runtime 使用独立目录/venv |
| DoD | 两个环境完全独立，互不污染 |

### T04 — 建立 Golden 工作目录

| 属性 | 值 |
|---|---|
| 操作 | 创建 `/root/julia_voice_v2/golden/` |
| DoD | 可独立启动/停止 |

### T05 — 建立版本记录

| 属性 | 值 |
|---|---|
| 操作 | 记录 AutoDL GPU/CUDA/Driver/Python |
| 产出 | `environment-fingerprint.txt` |

---

# Phase 1：100% 复现参考 Voice（Golden Baseline）

**这是整个项目现阶段最重要的一阶段。**

目标不是"差不多能说话"。目标是做到和参考 Demo 同一个级别的 Voice baseline。

**明确禁止进入 Phase 1 的组件：**
- Julia / Electron / ElevenLabs / LiveTalking / WebRTC Voice
- VoiceEngineClient.js / ScriptProcessor / createBufferSource / manual PCM scheduler / custom resampler

---

## P1-A：环境复刻

### T10 — 创建 Python 3.12 venv

| 属性 | 值 |
|---|---|
| 参考 | `install-voice.sh` |
| DoD | Python 3.12.x |

### T11 — 安装系统依赖

| 属性 | 值 |
|---|---|
| 操作 | `ffmpeg`, `libsndfile`, `cmake`, `git`, `curl`, `tmux` 等 |
| DoD | 安装无 error |

### T12 — 安装 S2S

| 属性 | 值 |
|---|---|
| 操作 | `pip install "speech-to-speech[faster-whisper]"` |
| DoD | `speech-to-speech serve --help` 可运行 |

### T13 — 安装 CUDA runtime deps

| 属性 | 值 |
|---|---|
| 操作 | `nvidia-cudnn-cu12`, `nvidia-cublas-cu12` |
| DoD | faster-whisper GPU 推理正常 |

### T14 — Clone 官方 frontend

| 属性 | 值 |
|---|---|
| 操作 | `git clone https://huggingface.co/spaces/smolagents/hf-realtime-voice` |
| DoD | 不修改 audio client，100% 原样 |

### T15 — 准备 Qwen3-TTS

| 属性 | 值 |
|---|---|
| 操作 | `Qwen/Qwen3-TTS-12Hz-1.7B-Base` 模型下载 + warmup |
| DoD | warmup 成功 |

### T16 — 准备参考音频

| 属性 | 值 |
|---|---|
| 操作 | PCM16 / mono / 16k / 5-15s clean speech |
| DoD | `ffprobe` 验证通过 |

---

## P1-B：Baseline LLM（最小流式端点）

### T20 — Baseline streaming LLM endpoint

| 属性 | 值 |
|---|---|
| 接口 | `POST /v1/chat/completions` |
| 参数 | `stream=true` |
| 要求 | 第一块文本立即返回，不是整个回答结束后一次返回 |

**期望输出：**

```
data: {"choices":[{"delta":{"content":"你好，"}}]}
data: {"choices":[{"delta":{"content":"我听到了。"}}]}
data: [DONE]
```

**重点不是模型聪不聪明。重点是验证 STT → streaming text → TTS → speaker 整条链。**

**这是可观测性的起点。从 T20 开始建立统一 timing 日志（t0–t12）。**

| DoD | `curl -N -X POST ... -d '{"stream":true}'` 第一块文本在 < 200ms 内返回 |

---

## P1-C：S2S Baseline Launcher

### T21 — S2S baseline launcher

基于参考 `start-voice.sh`，创建 baseline 启动命令：

```bash
speech-to-speech \
  --mode realtime \
  --stt faster-whisper \
  --faster_whisper_stt_model_name large-v3 \
  --faster_whisper_stt_gen_language zh \
  --language zh \
  --llm_backend chat-completions \
  --responses_api_stream \
  --tts qwen3 \
  --qwen3_tts_model_name Qwen/Qwen3-TTS-12Hz-1.7B-Base \
  --qwen3_tts_language zh
```

**VAD 参数（严格复制参考值，第一阶段不调优）：**

```
VAD_THRESH=0.6
MIN_SPEECH_MS=500
MIN_SILENCE_MS=1200
SPEECH_PAD_MS=300
MERGE_MS=800
REOPEN_MS=2500
```

---

## P1-D：官方 Browser Client

### T22 — hf-realtime-voice 部署

```
Chrome → hf-realtime-voice → ws://localhost:8765/v1/realtime
```

**连接方式（AutoDL 继续通过 SSH TCP tunnel）：**

```
Mac localhost:7860 → SSH TCP → AutoDL:7860
Mac localhost:8765 → SSH TCP → AutoDL:8765
```

**禁止：NO WebRTC / NO UDP / NO TURN**

---

## P1-E：基础功能 Gate

### T23 — Mic Test

| 检查项 | 状态 |
|---|---|
| `getUserMedia` 成功 | |
| `echoCancellation: true` requested | |
| `noiseSuppression: true` requested | |
| `autoGainControl: true` requested | |
| AudioWorklet running | |
| WS `input_audio_buffer.append` 发送成功 | |

### T24 — STT Test

**固定中文测试集：**

| # | 文本 |
|---|---|
| 1 | 你好 |
| 2 | Julia 你在吗 |
| 3 | 你听得到我说话吗 |
| 4 | 等一下 |
| 5 | 我刚才说的是什么 |

**记录：** `speech_started` / `speech_stopped` / `transcript final`

### T25 — Qwen3 Playback Test

**检查：** `response.output_audio.delta` → official AudioWorklet → 正常人声

| DoD | 无白噪声 / 无变声器效果 / 无断裂 / 无严重爆音 / 无播放速度异常 |

---

## P1-F：Barge-in

### T26 — 插话测试

**标准场景：**

```
AI: "好的，我来给你介绍一下……"
Tony: "等等。"
```

**预期：** AI 立即停止 → `speech_started` → 旧 playback clear → 旧 response cancel → 开始听 Tony

**关键观测：** `speech_started` → `playback clear` 延迟（工程目标 p50 < 300ms，第一轮先保证正确性）

---

## P1-G：20-turn Golden Test（Golden Gate）

### T27 — 固定测试集

建立 `tests/golden_voice_cases.yaml`：

| 场景类型 | 示例 |
|---|---|
| 普通短句 | "今天天气怎么样" |
| 长句 | "你能帮我介绍一下深度学习的基本原理吗" |
| 停顿 | 句中自然停顿 |
| 快速连续讲话 | 连续提问 |
| 语气词 | 嗯/啊/诶 |
| 句中停顿 | 一句话中间停顿 |
| 主动插话 | AI 说话中打断 |
| 连续插话 | 多次打断 |
| AI 长回答 | 触发 30s+ 回答 |
| AI 短回答 | 触发 1-2 句回答 |

### T28 — 自动记录

每 turn 保存：

```
turn_id / speech_start / speech_stop / transcript
response_text / first_audio / response_done / interrupt / error
```

### T29 — Golden Gate（必须全部满足）

| # | 条件 |
|---|---|
| 1 | 20 turns |
| 2 | 0 persistent noise |
| 3 | 0 silent turn |
| 4 | 0 cross-turn audio |
| 5 | 0 process crash |
| 6 | STT usable |
| 7 | TTS usable |
| 8 | barge-in usable |
| 9 | speaker usable |

**如果 noise != 0 或者 silent turn != 0 → Phase 1 NO-GO。不准接 Julia。**

---

## P1-H：噪声 Debug SOP（如需要）

**强制排查顺序（禁止跳过）：**

```
1. Golden baseline client/server revision 确认
2. server pre-transport PCM dump → WAV
3. browser received PCM dump → WAV
4. Browser AudioWorklet input dump → WAV
5. 对比三份音频 SHA/duration/RMS
6. 给出第一个出现 corruption 的节点
```

| ID | Probe |
|---|---|
| D01 | server pre-transport WAV dump |
| D02 | WS received PCM WAV dump |
| D03 | Browser AudioWorklet input dump |
| D04 | 对比三份音频 SHA/duration/RMS |
| D05 | 定位第一个出现 corruption 的节点 |

**只有证据指向 TTS 才允许改 TTS。禁止出现第六种调试方式。**

---

# Phase 1.5：Golden Freeze

### T30 — golden-baseline.json

```json
{
  "s2s_version": "...",
  "s2s_sha": "...",
  "frontend_sha": "...",
  "python": "3.12.x",
  "torch": "...",
  "cuda": "...",
  "driver": "...",
  "qwen3_tts_revision": "...",
  "stt_model": "...",
  "browser": "...",
  "vad": {
    "thresh": 0.6,
    "min_speech_ms": 500,
    "min_silence_ms": 1200,
    "speech_pad_ms": 300,
    "merge_ms": 800,
    "reopen_ms": 2500
  }
}
```

### T31 — requirements.lock

**禁止 `>=`，必须 `==`：**

```
speech-to-speech==X.Y.Z
torch==X.Y.Z
faster-whisper==X.Y.Z
numpy==X.Y.Z
...
```

### T32 — frontend SHA freeze

**禁止 `git pull`，正式运行：**

```bash
git checkout <SHA>
```

### T33 — reproduce.sh

```bash
./reproduce.sh
```

能完整启动：S2S + frontend + baseline LLM。

### T34 — Golden tag

```
julia-voice-golden-v1
```

从此 Media baseline 视作 third-party infrastructure。

---

# Phase 2：Julia Brain True Streaming

**从这里才真正开始改 Julia。**

---

## P2-A：Julia-AI-Assistant 改造

**开发分支：** `feature/voice-v2-streaming`（不要直接污染之前的 voice experiment）

### T40 — OpenAI-compatible endpoint

| 属性 | 值 |
|---|---|
| 接口 | `POST /v1/chat/completions` |
| 参数 | `{"model": "julia-brain", "messages": [...], "stream": true}` |
| 说明 | V2.0 已把这个接口确定为 S2S 热路径 |

### T41 — Non-stream compatibility

同时支持 `stream=false`（便于测试），但 **Voice runtime 必须 stream=true**。

### T42 — DeepSeek streaming provider

**从：**

```python
provider.chat()  # wait whole reply
```

**改为：**

```python
async for delta in provider.stream(messages):
    yield delta
```

**核心验收：** DeepSeek 还没生成完整回复 → Julia endpoint 已经输出第一段 SSE。

### T43 — 真 cancellation

**旧行为（禁止）：**

```
cancel Event → 停止 yield → DeepSeek 后台继续跑
```

**新行为（必须）：**

```
barge-in → cancel generation → close HTTP response
→ abort provider stream → 释放 connection
```

| DoD | cancel 后 DeepSeek stream task terminated（不仅仅 Browser 听不到） |

### T44 — Conversation Mapping

```
S2S session → conversation_id → Julia session
```

**禁止：** 每次 voice turn 创建新的 Julia context。

**必须保留：** persona / memory / conversation history / tools。

### T45 — Voice Reply Policy

**规则：**
- 1–3 句，口语化，核心答案先说
- 无 Markdown、无编号、无 URL、允许语气词
- 尽快形成第一段 TTS（不等完整回答）

**架构：**

```
DeepSeek tokens → SpeechSegmentBuffer → semantic boundary → yield
```

示例：

```
"嗯，"             暂存
"我记得。"         → yield "嗯，我记得。"
"昨天我们讨论的是"  暂存
"语音架构。"       → yield "昨天我们讨论的是语音架构。"
```

### T46 — 不修改 Julia Core media boundary

`julia_core` 只允许增加语义字段：

```
input_mode = voice
spoken_reply_policy
interruptible
heard / unfinished metadata
concise_response_profile
```

**绝对不能出现：** PCM / sample_rate / WebSocket / AudioFrame / WebRTC / TTS provider。

---

## P2-B：接入 S2S

### T47 — 唯一允许修改的 Golden 配置

**从：**

```
responses_api_base_url → baseline-llm
```

**改成：**

```
responses_api_base_url → Julia-AI-Assistant
model_name = julia-brain
```

**验证 Git diff（其他全部 SHA 不变）：**

```
S2S             0 changed
frontend        0 changed
AudioWorklet    0 changed
Qwen3           0 changed
VAD             0 changed
sample rate     0 changed
```

---

## P2-C：Julia Integration Gate

### T48 — Persona Test

确认说话的是 Julia（非 generic assistant）。

### T49 — Memory Test

问已有记忆，确认 recall。

### T50 — Tool Test

至少验证一次工具调用。

### T51 — Streaming latency

记录 `t3 Julia request` / `t4 DeepSeek first token`。

### T52 — Cancel Test

AI 生成中插话。确认：

- old DeepSeek aborted
- old text stops
- old TTS stops
- new turn begins

### T53 — 20 turns regression

**媒体指标不得比 Golden baseline 回归。**

```
Persona ✓  Memory ✓  Tools ✓  True streaming ✓
First token ✓  Cancel ✓  20 rounds no audio regression ✓
```

---

# Phase 3：Julia Voice Clone

### T60 — Julia reference audio

准备 `julia_ref.wav`：

```
5–15秒 / clean / mono / 16kHz / PCM16
```

以及逐字一致的 `REF_TEXT`。

### T61 — Qwen3 Base Voice Clone

**只修改：**

```
--qwen3_tts_ref_audio /path/to/julia_ref.wav
--qwen3_tts_ref_text "<exact transcript>"
```

**其他全部不动。**

### T62 — 声线一致性测试

固定 20 条测试（陈述/问句/撒娇/轻笑/低声/快速/慢速/短句/长句/中英混合）：

| 评分维度 |
|---|
| speaker consistency |
| naturalness |
| emotion |
| stability |
| speed |

### T63 — Voice cancel

Julia 说到一半 Tony 插话。确认旧 TTS 音频完全消失。

```
20 次响应 / 无声线漂移 / 无明显延迟退化 / cancel 不残旧音频 ✓
```

---

# Phase 4：Full Duplex / AEC 正式评测

**必须建立在前面已经稳定的 Voice baseline 上。**

### T70 — 浏览器音频状态记录

```
actual sampleRate / echoCancellation / noiseSuppression / autoGainControl / channelCount
```

### T71 — Speaker Matrix

| 场景 | 音量 |
|---|---|
| 安静房间 | 25% |
| 安静房间 | 50% |
| 安静房间 | 75% |
| 普通室内 | 50% |
| 背景音乐 | 50% |
| 远距离说话 | 50% |

### T72 — Echo test

Julia 说话，Tony 不说话。要求：不能因为扬声器回声产生新的完整 user turn。

### T73 — Double-talk

Julia 正在说，Tony 插话"等等，我不同意"。要求：Tony 被识别、Julia 停止、新 transcript 正确。

### T74 — Rapid interruption

连续：AI speaking → Tony interrupt → AI answer → Tony interrupt again。验证 old turn 永不复活。

### T75 — 30-minute session

检查：memory / GPU / WS / AudioWorklet / queue / cancel state。

**Stability Gate：50 turns / 30 分钟 / 无跨 turn audio / 无死锁 / reconnect 可恢复 / GPU memory 无持续泄漏。**

### Phase 4 结论（三选一）

| 结论 | 行动 |
|---|---|
| `PASS_WS_FULL_DUPLEX` | WebSocket = Julia Voice V1 transport |
| `PASS_WITH_LIMITATIONS` | 产品层做限制（如限制音量上限） |
| `FAIL_REQUIRES_RTC_EVALUATION` | 才进入 Phase 7 WebRTC |

**绝对不能因为"理论上 WebRTC 更高级"就提前启动 Phase 7。**

---

# Phase 5：Production Hardening

Voice 体验过关后再做。

| ID | 任务 |
|---|---|
| T80 | HTTPS / WSS |
| T81 | Browser session token |
| T82 | Auth |
| T83 | Rate limiting |
| T84 | Process supervisor |
| T85 | S2S health check |
| T86 | Julia Brain health check |
| T87 | GPU health check |
| T88 | Qwen3 warmup |
| T89 | faster-whisper warmup |
| T90 | Auto restart |
| T91 | Structured logging |
| T92 | Metrics endpoint |
| T93 | Reconnect |
| T94 | Mainland connectivity test |
| T95 | Secrets isolation |
| T96 | Immutable deployment image |
| T97 | Release runbook |

**正式路径必须避免：**
- 国外 Voice SaaS
- 国外 media relay
- VPN dependency
- ElevenLabs mandatory dependency

---

# Phase 6：Avatar（optional）

Voice baseline 作为只读依赖。

接入 LiveTalking / avatar layer。

**原则：Avatar failure MUST NOT break Voice。**

---

# Phase 7：WebRTC Voice（conditional）

**只有 Phase 4 结论为 `FAIL_REQUIRES_RTC_EVALUATION` 才进入。**

**需要：**
- public media reachability
- UDP mapping or TURN
- ICE/STUN/TURN
- official S2S WebRTC revision
- remote audio track
- browser standard client

**禁止：**
- 自己实现 RTP
- 自己实现 AEC
- WebRTC-over-custom-PCM

---

# Phase 8：Electron（optional）

只有 Browser 产品已经冻结后：

```
Electron = package / shell
```

**原则：Electron 不重新设计媒体协议，不重写 audio engine。**

---

# 可观测性（从 T20 开始建立）

## Unified Timing

| 时间点 | 含义 |
|---|---|
| t0 | user speech started |
| t1 | user speech stopped |
| t2 | transcript final |
| t3 | Julia request start |
| t4 | DeepSeek first token |
| t5 | first TTS text segment |
| t6 | first TTS audio |
| t7 | first audio received by Browser |
| t8 | first audio played |
| t9 | interruption detected |
| t10 | playback cleared |
| t11 | upstream generation aborted |
| t12 | response done |

## 延迟计算

| 指标 | 公式 | 工程目标 |
|---|---|---|
| STT latency | t2 - t1 | p50 < 0.8s |
| Brain first-token | t4 - t3 | p50 < 0.8s |
| Text-to-TTS handoff | t5 - t4 | - |
| TTS first-audio | t6 - t5 | p50 < 0.8s |
| Transport/playback | t8 - t6 | - |
| End-to-end first response | t8 - t1 | p50 < 2.0s |
| Barge-in stop | t10 - t9 | p50 < 0.3s |
| Cancel propagation | t11 - t9 | - |

**最终阈值以 Golden Baseline 实测分布重新冻结。**

## 统一日志格式

```json
{
  "trace_id": "...",
  "session_id": "...",
  "turn_id": "...",
  "response_id": "...",
  "event": "tts.first_audio",
  "ts": 123456.78
}
```

---

# Phase 1 Report — 必须回答的 12 个问题

Phase 1 完成后，出具 `PHASE1_GOLDEN_BASELINE_REPORT.md`，必须回答：

| # | 问题 | 通过条件 |
|---|---|---|
| 1 | Exact S2S version? | 有明确版本号 |
| 2 | Exact frontend SHA? | 有 commit SHA |
| 3 | Browser version? | 有版本号 |
| 4 | Input actual sample rate? | 有实际值 |
| 5 | Output sample rate? | 有实际值 |
| 6 | 20 turns 成功多少？ | 20/20 |
| 7 | 是否出现 noise？ | 0 |
| 8 | 是否出现 silent turn？ | 0 |
| 9 | 是否出现 audio overlap？ | 0 |
| 10 | barge-in 是否成功？ | ALL PASS |
| 11 | speaker 模式是否出现 false STT？ | 0 |
| 12 | p50 first audible response？ | 有数值 |

**如果 noise != 0 或者 silent turn != 0 → Phase 1 NO-GO。不准接 Julia。**

---

# 第一批建议执行任务（Codex Ready）

现在不要一次把全部任务交给 Codex。第一批只执行：

| 顺序 | Task ID | 任务 |
|---|---|---|
| 1 | T00 | 冻结失败分支 |
| 2 | T03 | 建立独立 Golden runtime |
| 3 | T05 | environment fingerprint |
| 4 | T10–T16 | 复刻 reference install |
| 5 | T20 | baseline streaming LLM |
| 6 | T21 | reference S2S launcher |
| 7 | T22 | official hf-realtime-voice |
| 8 | T23 | mic test |
| 9 | T24 | STT test |
| 10 | T25 | TTS playback test |
| 11 | T26 | barge-in test |
| 12 | T27–T29 | 20-turn Golden Gate |

**到这里 STOP。出具 `PHASE1_GOLDEN_BASELINE_REPORT.md`。只有报告结论为 GO 才能执行 T30 以后。**

---

# 风险矩阵

| 风险 | 影响 | 对策 |
|---|---|---|
| S2S / frontend revision 漂移 | 噪声、事件不兼容 | exact pin + lock + SHA |
| 自定义 Browser media 再次出现 | 重复旧问题 | Golden client 禁改 |
| site-packages patch | runtime 不可复现 | 正式环境禁用 |
| Qwen3 声线质量不足 | Julia 音色弱 | 优化 ref；ElevenLabs optional |
| DeepSeek 非真 streaming | 首响慢 | provider.stream / SSE |
| DeepSeek soft cancel | 插话后旧生成继续 | abort actual HTTP |
| VAD 中文停顿不合适 | 抢答/迟钝 | 参考参数起步 + 回归集 |
| Browser AEC 不足 | 自回声 | Phase 4 实测；必要时 WebRTC |
| AutoDL UDP 不开放 | WebRTC Voice blocked | 当前 WS 不受影响 |
| AutoDL 重启 | 模型 warmup / session 断开 | supervisor + reconnect |
| 海外 SaaS 不可达 | 产品不可用 | runtime 本地化/国内可达 |
| Qwen3 GPU 资源占用 | OOM | STT/TTS model size control |
| Avatar 耦合 Voice | 数字人故障拖垮语音 | 两层彻底隔离 |

---

# 禁止项（永久清单）

以下内容不得进入 Golden Voice 主路径：

```
LiveKit Python AgentSession + RoomIO
custom Browser PCM transport
ScriptProcessor production capture
manual AudioBufferSource playback scheduling
manual _nextPlayTime queue
custom JavaScript AEC / DSP
site-packages manual patch
direct rtc.AudioSource production fallback
custom LiveKit LocalAudioTrack
REST MP3 download + separate player
Browser/Electron DeepSeek key
Browser/Electron ElevenLabs key
Julia Core PCM / Opus / WebRTC dependency
unversioned client/server media contract
unverified sample-rate conversion
mixing frontend and backend from unrelated revisions
full LLM reply buffering before TTS
full TTS download buffering masquerading as streaming
```

---

# 架构纪律（Three Laws）

## F.1 先证明，再集成

```
Working Reference → Freeze → Change One Variable → Test → Freeze Again
```

## F.2 Media Is Infrastructure

Julia 项目不再把时间投入到：PCM scheduler / AEC algorithm / browser resampler / jitter buffer / RTP packetization / custom realtime protocol。除非 Golden Reference 明确缺失且有可量化产品收益。

## F.3 Julia Owns Julia

真正属于 Julia 的工程投入应集中在：Persona / Memory / Context OS / Conversation continuity / Tools / Reasoning / Voice reply style / Emotion semantics / Long-term relationship state。

**Voice Engine 的使命只是：可靠地听见 → 可靠地打断 → 可靠地把 Julia 的文字说出来。**

---

**文档结束 — Julia Voice V2 Development Plan**
