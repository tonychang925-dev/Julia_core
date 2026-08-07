# Julia 实时语音架构重新审计与冻结决议 v2.0

> **审计状态**：完成架构判定  
> **当前语音实现状态**：不得冻结  
> **目标架构状态**：边界冻结，实施待验收  
> **日期**：2026-08-06  
> **建议路径**：`docs/architecture/JULIA_REALTIME_VOICE_ARCHITECTURE_FREEZE_V2.md`

---

## 一、审计结论

当前 `julia_core + julia_electron` 中正在运行的语音方案，不符合 Julia Core 已冻结的架构边界。

此前所谓“语音架构冻结”无效，原因是冻结对象实际包含：

- 自定义 WebRTC 会话
- 自定义 VAD
- 自定义 ASR 管线
- 自定义 PCM packetizer
- 自定义 RTP 发送节拍
- 自定义回声保护
- 自定义半双工门控
- 自定义打断与 TurnManager

这些是实时语音引擎职责，不是 Julia Core 的认知职责。

因此正式判定：

```text
原语音实现冻结：撤销
当前自研媒体链路：Legacy，只允许归档，不允许继续修补
Julia Core 认知架构冻结：继续有效
实时语音引擎架构：重新设计并重新验收
```

---

## 二、仓库冻结文档规定的正确边界

Julia Core 的架构宪法规定：

```text
Runtime = Authority
Provider = Capability
Provider 不拥有认知、身份和记忆
```

Voice Provider 只能提供声音渲染能力；Julia Core 拥有情绪与韵律规划。

架构总览明确规定：

```text
Julia Core Voice OS：
- CognitiveEmotion
- SpeechProsodyPlanner
- VoiceProvider protocol

外部实现：
- EdgeTTS
- ElevenLabs
- Fish Audio
- CosyVoice
```

产品依赖 Core，Core 不能反向依赖产品或具体语音服务。

冻结设计文档同样规定：

```text
Core owns:
- emotion
- prosody
- voice intent

Provider owns:
- audio rendering
```

当前 `VoiceProvider` 协议本身也只定义了 text → audio，并明确声明 Provider 不拥有 emotion、persona 或 prosody planning。

### 冻结边界

```text
Julia Core 可以看到：
- 用户最终文本
- Julia 回复文本
- CognitiveEmotion
- SpeechMetadata
- speech.started
- speech.completed
- speech.cancelled
- presence 状态

Julia Core 不允许看到：
- PCM
- WAV
- Opus
- RTP
- WebRTC Track
- Microphone Device
- VAD frame
- jitter buffer
- AEC 状态
```

---

## 三、当前实现的越界项

### 1. Julia Core 自己实现 VAD

`voice_runtime/pipeline/audio_pipeline.py` 当前自己实现：

- RMS 阈值
- 动态噪声底
- 300ms pre-roll
- 静音 endpoint
- segment buffer

判定：

```text
违反 Core 与媒体能力边界
必须迁出 Julia Core
```

### 2. Julia Core 自己实现 WebRTC 媒体会话

当前 `WebRTCSession` 自己负责：

- aiortc PeerConnection
- Track 接收
- PyAV 重采样
- PCM 提取
- 麦克风门控
- TTS Track

判定：

```text
这是自研 Realtime Audio Engine
不属于 Julia Core
```

### 3. Gateway 承担 ASR、TTS 和回声处理

当前 Gateway 自己处理：

- 3 秒 echo guard
- speaking 状态抑制
- TTS output gate
- TTS drain
- 尾音等待
- Whisper 实例化
- AudioPipeline 实例化

判定：

```text
Gateway 已从协议网关变成媒体运行时
职责严重膨胀
```

### 4. Electron 安装了 LiveKit，但没有使用

`julia_electron/package.json` 已经包含：

```text
livekit-client ^2.21.0
```

但当前实际运行代码仍然自己创建：

```javascript
new RTCPeerConnection()
createOffer()
setLocalDescription()
setRemoteDescription()
pc.ontrack
```

判定：

```text
LiveKit 依赖存在
LiveKit 实时语音引擎没有真正接管链路
“LiveKit ready”不等于“LiveKit integrated”
```

### 5. Julia AI Assistant 只有 TTS Provider 路由

`Julia-AI-Assistant` 当前定位是 Julia 的产品实例，包含 persona、memory 和 voice。

其中 `voice_router.py` 只负责在 ElevenLabs、Fish Audio、Edge TTS 之间选择声音渲染 Provider。

它尚未承担成熟实时语音 Session Runtime。

---

## 四、重新冻结的目标架构

正式选择：

```text
Realtime Voice Engine：LiveKit
Client SDK：livekit-client
Agent Runtime：LiveKit Agents
Julia cognition：Julia Core
Julia product adapter：Julia AI Assistant
```

### 目标结构

```text
julia_electron
│
├── LiveKit Client SDK
│   ├── microphone capture
│   ├── remote audio playback
│   ├── room/session lifecycle
│   └── SDK 内部 WebRTC
│
▼
LiveKit Server
│
├── signaling
├── ICE/TURN
├── media transport
├── track lifecycle
└── network adaptation
│
▼
Julia-AI-Assistant Voice Runtime
│
├── LiveKit AgentSession
├── mature VAD
├── mature turn detection
├── STT provider
├── TTS provider
├── interruption/barge-in
├── JuliaCoreAdapter
└── JuliaEventBridge
│
▼
Julia Core
│
├── JuliaSession
├── Context OS
├── Memory OS
├── Persona Engine
├── CognitiveEmotion
└── SpeechProsodyPlanner
```

---

## 五、三仓职责冻结

### `julia_core`

允许保留：

```text
JuliaSession
Runtime
Context OS
Memory OS
Persona Engine
Voice OS
CognitiveEmotion
SpeechProsodyPlanner
VoiceProvider protocol
语音意图与状态事件
```

禁止包含：

```text
aiortc
PyAV media processing
faster-whisper runtime
WebRTC signaling
VAD
PCM packetizer
TTSAudioTrack
RTP pacing
echo guard
microphone gate
jitter buffer
turn detection algorithm
```

### `Julia-AI-Assistant`

负责：

```text
JuliaCoreAdapter
LiveKit AgentSession
STT/TTS provider configuration
Julia voice profile
emotion/prosody 参数适配
LiveKit event → Julia event bridge
产品级会话配置
```

不得负责：

```text
Julia 身份权威
Context OS
Memory governance
独立 prompt assembly
```

### `julia_electron`

负责：

```text
LiveKit room connect/disconnect
microphone enable/disable
remote audio subscription
UI 音量与连接状态
展示 transcript 与 Julia 事件
```

禁止：

```text
new RTCPeerConnection
手写 SDP/ICE
/rtc/offer
自定义 ontrack 媒体生命周期
本地 ASR 旁路
自定义 AEC
自定义 VAD
文本 echo filter
```

### Gateway

负责：

```text
身份验证
LiveKit token issuance
Julia Runtime API
事件传输
Session ID 映射
健康检查
```

禁止：

```text
接收 RTP
处理 PCM
运行 Whisper
运行 VAD
创建 TTSAudioTrack
处理 jitter buffer
实现回声消除
```

---

## 六、冻结层级

以后必须分成两个冻结阶段。

### A. Architecture Boundary Freeze

本决议通过后立即冻结：

```text
1. LiveKit 是唯一实时媒体引擎
2. Julia Core 不处理媒体
3. Julia AI Assistant 承载产品级 Voice Runtime
4. Electron 只使用 LiveKit Client SDK
5. Gateway 不处理 RTP/PCM/VAD/ASR/TTS
6. 不允许新增第二条语音路径
```

这部分一旦冻结，不得因某个 bug 重新把媒体逻辑塞回 Core。

### B. Implementation Freeze

只有完成实机验收后才允许冻结。

禁止再用：

```text
单元测试全部通过
代码看起来正确
事件顺序正确
PCM 已经 enqueue
```

作为实现冻结依据。

实现冻结必须包含真实设备运行证据。

---

## 七、旧实现处理方式

当前代码不得继续修补。

先创建归档点：

```bash
# Julia Core
git tag voice-legacy-custom-runtime-20260806
git branch archive/voice-custom-runtime

# Julia Electron
git tag voice-legacy-raw-webrtc-20260806
git branch archive/voice-raw-webrtc
```

随后在主分支中：

```text
停用 /rtc/offer
停用 WebRTCSession
停用 AudioPipeline
停用 WhisperCPUProvider 的实时入口
停用 EdgeTTSPCMProvider
停用 TTSAudioTrack
停用 raw WebRTCVoice.js
```

历史代码可以保留在 archive 分支，但不得继续进入生产启动路径。

---

## 八、迁移阶段

### Phase V2-0：冻结旧链路

验收：

```text
旧实现已 tag
主分支不再继续修 custom voice runtime
冻结文档合入
```

### Phase V2-1：纯 LiveKit 最小闭环

链路：

```text
Electron
→ LiveKit
→ AgentSession
→ 固定文字回复
→ 官方 TTS
→ Electron
```

此阶段不接 Julia Core。

目标：

```text
验证成熟引擎自身能否稳定运行
```

### Phase V2-2：接入 STT 与打断

只使用成熟组件：

```text
LiveKit AgentSession
+ STT Provider
+ VAD/Turn Detection Provider
+ TTS Provider
```

不允许出现自定义回声 guard、VAD 或 pacing。

### Phase V2-3：接入 JuliaCoreAdapter

链路：

```text
final transcript
→ JuliaCoreAdapter
→ JuliaSession
→ Context OS / Memory / Persona
→ response text
→ prosody metadata
→ LiveKit TTS
```

### Phase V2-4：事件协议恢复

映射：

```text
user transcript final → client.voice.final
agent speaking start   → speech.started
agent text stream      → speech.chunk
user interrupt         → speech.cancelled
playback complete      → speech.completed
runtime error          → speech.failed
```

---

## 九、实现冻结验收标准

### 静态架构验收

必须同时满足：

```text
Julia Core 不依赖 aiortc
Julia Core 不依赖 faster-whisper
Julia Core 不依赖 LiveKit
Julia Core 不出现 PCM/RTP/WebRTC Track
Electron 不出现 new RTCPeerConnection
Electron 不调用 /rtc/offer
Electron 媒体链路只经过 livekit-client
LiveKit Agent Runtime 只位于产品能力层
```

### 实机语音验收

必须完成：

```text
1. Julia 连续播放 100 次
   错误触发 ASR：0

2. 用户连续说话 100 次
   每次恰好产生一个 final transcript

3. 连续运行 30 分钟
   自回声循环：0
   重复回复：0
   重复房间/音轨：0

4. 重连 10 次
   每次只有一个有效 Voice Session

5. 用户打断
   P95 停止播放延迟 < 250ms

6. Julia 播放结束
   不产生尾音 transcript

7. 模型切换
   Julia 的身份、记忆和会话连续性不变化
```

### 识别质量验收

建立固定中文测试集：

```text
日常对话
长句
数字
中英文混合
Julia / Tony
A股与金融术语
```

每次切换 STT Provider 都必须在同一测试集上比较，禁止凭一次主观体验判断。

---

## 十、冻结判决

```text
Julia Core 五项架构原则             FROZEN
三仓依赖方向                        FROZEN
Voice OS emotion/prosody ownership  FROZEN
Provider capability boundary         FROZEN
LiveKit 作为唯一媒体引擎             DESIGN FROZEN

当前 aiortc 自研实现                 REJECTED / LEGACY
当前语音实现                         NOT FROZEN
LiveKit 实际集成                     NOT IMPLEMENTED
实时语音生产可用                     NOT ACCEPTED
```

最终只有在 V2-1 至 V2-4 全部完成，并提交三仓准确 SHA、测试报告和实机运行记录之后，才能签发：

```text
JULIA_REALTIME_VOICE_IMPLEMENTATION_FREEZE_V2
```

在此之前，任何“架构冻结通过”“语音链路完成”的表述均无效。
