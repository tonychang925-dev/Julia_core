# Julia OS E3 Voice Runtime Architecture v1

## WebRTC-based Real-Time Voice Processing Architecture Design

Status: Proposed Architecture

## 1. Design Principle

Julia OS follows:

Client = Body\
Runtime = Brain\
WebRTC = Neural Transport

The Voice subsystem must not become part of Julia Core. Raw audio
processing belongs to the Voice Capability layer.

Goals:

-   Server-side GPU deployment
-   Thin Electron/mobile/web clients
-   Low latency conversation
-   Streaming ASR/TTS
-   Interruptible interaction
-   Multi-provider voice capability

------------------------------------------------------------------------

## 2. Overall Architecture

    Client Layer
    (Electron / Mobile / Web / Robot)

            |
            |
         WebRTC

            |

    Runtime Gateway

    +---------------------------+
    | Command Plane             |
    | Event Plane               |
    | Media Plane               |
    +---------------------------+

            |

    Voice Runtime

    +---------------------------+
    | WebRTC Gateway            |
    | VAD                       |
    | Streaming ASR             |
    | Transcript Runtime        |
    | Streaming TTS             |
    +---------------------------+

            |

    Julia Core

    Identity
    Relationship
    Conversation
    Memory
    Experience
    Capability

------------------------------------------------------------------------

## 3. Why WebRTC

Do not build custom audio streaming.

A custom pipeline requires:

-   Audio capture
-   Packet management
-   Buffer control
-   Network jitter handling
-   Codec processing
-   Echo cancellation
-   Interrupt management

These are RTC problems, not AI problems.

WebRTC provides:

-   Real-time transport
-   Opus codec
-   Adaptive bitrate
-   NAT traversal
-   Jitter buffer
-   Audio processing

------------------------------------------------------------------------

## 4. Gateway Three Plane Model

### Command Plane

Example:

``` json
{
"type":"runtime.command",
"command":"message.send",
"payload":{
"text":"今天市场怎么样"
}
}
```

### Event Plane

Runtime state events:

-   presence.changed
-   voice.started
-   voice.partial
-   voice.final
-   assistant.chunk
-   assistant.completed

Example:

``` json
{
"type":"runtime.event",
"event":"presence.changed",
"data":{
"state":"LISTENING"
}
}
```

### Media Plane

Audio stream:

    Microphone
       |
     WebRTC
       |
    Voice Gateway
       |
    ASR/TTS

------------------------------------------------------------------------

## 5. Voice Interaction Lifecycle

    User presses microphone

            |

    voice.started

            |

    presence.listening

            |

    WebRTC audio stream

            |

    Streaming ASR

            |

    voice.partial

            |

    voice.final

            |

    presence.thinking

            |

    JuliaSession.chat()

            |

    assistant.chunk

            |

    Streaming TTS

            |

    presence.speaking

------------------------------------------------------------------------

## 6. Component Responsibilities

### Electron Client

Responsible:

-   microphone capture
-   WebRTC connection
-   audio playback
-   UI presence rendering

Not responsible:

-   memory
-   persona
-   reasoning
-   model selection

### Voice Gateway

Responsible:

-   WebRTC session
-   media transport
-   codec handling

### ASR Runtime

Interface:

    Audio Stream

    ↓

    ASR Adapter

    ↓

    Transcript Events

Provider examples:

-   Faster Whisper
-   NVIDIA Riva
-   Cloud Speech

### Julia Core

Receives:

``` json
{
"type":"message.send",
"source":"voice",
"text":"你好婉婉"
}
```

Core remains unchanged:

Identity → Relationship → Memory → Reasoning → Response

------------------------------------------------------------------------

## 7. Streaming TTS

Pipeline:

    Julia Response

    ↓

    Text chunks

    ↓

    TTS streaming

    ↓

    WebRTC audio

    ↓

    Client speaker

Supports:

-   low latency
-   interruption
-   barge-in

------------------------------------------------------------------------

## 8. Interrupt Architecture

    Julia speaking

    ↓

    User starts speaking

    ↓

    VAD detects voice

    ↓

    Stop TTS

    ↓

    Switch to LISTENING

    ↓

    Process new input

This creates natural dialogue.

------------------------------------------------------------------------

## 9. Deployment Architecture

Client:

-   normal CPU computer
-   microphone
-   network

Server:

-   GPU ASR
-   GPU LLM
-   GPU TTS
-   Julia Runtime

```{=html}
<!-- -->
```
    Client

       |

    WebRTC

       |

    Cloud Voice Runtime

       |

    Julia OS Runtime

------------------------------------------------------------------------

## 10. Development Roadmap

### E3.1 WebRTC Foundation

-   WebRTC gateway
-   Media Plane
-   voice session lifecycle

### E3.2 Streaming ASR

-   partial transcript
-   final transcript
-   latency measurement

### E3.3 Streaming TTS

-   audio streaming
-   playback control

### E3.4 Interrupt Runtime

-   barge-in
-   generation cancel

### E3.5 Production Voice Runtime

-   multi-client
-   monitoring
-   scaling

------------------------------------------------------------------------

## Final Architecture Principle

Julia OS:

    Client
    =
    Body

    WebRTC
    =
    Nervous System

    Runtime Gateway
    =
    Brain Stem

    Julia Core
    =
    Identity + Memory + Experience

    Capability Layer
    =
    Organs

The goal is not to make Julia process audio.

The goal is to give Julia a real-time body.
