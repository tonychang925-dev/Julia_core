# Build Your First Agent

> **Time**: ~30 minutes  
> **Prerequisites**: Python 3.10+, `pip install julia-core`  
> **Result**: A running agent with persona, chat, and optional voice

---

## Overview

You'll build a "Demo Assistant" — a simple agent with:
- A defined persona (friendly helper)
- Text chat capability
- Optional voice output

This is the same pattern used by Julia AI Assistant and Financial Analyst.

```
Your Agent = Runtime + Persona + (optional) Providers
```

---

## Step 1: Install Julia Core

```bash
pip install julia-core
```

Verify installation:

```bash
python -c "from julia_core.chat.persona import Persona; print('OK')"
```

---

## Step 2: Define Your Persona

Create `my_persona.py`:

```python
from julia_core.chat.persona import Persona

# This is a DEMO persona — synthetic, for demonstration.
# For a real agent, supply your own identity facts.
demo = Persona(
    persona_id="demo-assistant-v1",
    name="Demo Assistant",
    role="helpful assistant",
    language="en",
    tone="friendly",
    system_prompt=(
        "You are Demo Assistant, a helpful and friendly AI assistant. "
        "Speak warmly and concisely. Be honest about what you know and don't know."
    ),
)
```

> **Important**: This persona is synthetic demo data. Real personas should load identity facts from private storage — see [Create a Persona](CREATE_PERSONA.md).

---

## Step 3: Start a Chat Session

```python
from julia_core.chat.session import ChatSession

# Create session with your persona
session = ChatSession(persona=demo)

# Send a message
response = session.send("Hello! Who are you?")
print(response)
# → "Hi! I'm Demo Assistant, your friendly helper. How can I help you today?"
```

That's it. You have a running agent.

---

## Step 4: Add Voice (Optional)

Julia Core Voice OS owns emotion and prosody. You provide a TTS engine.

```python
from julia_core.voice_os.emotion_state import CognitiveEmotion, EmotionState
from julia_core.voice_os.prosody import SpeechProsodyPlanner

# Julia Core decides emotion
emotion = CognitiveEmotion(state=EmotionState.WARM, intensity=0.7)
planner = SpeechProsodyPlanner()
metadata = planner.plan(emotion)

# VoiceProvider renders audio
# (requires a VoiceProvider — EdgeTTS is a free option)
from providers.examples.voice.edge_tts_provider import EdgeTTSVoiceProvider

voice = EdgeTTSVoiceProvider()
voice.speak("Hello! How can I help you today?", emotion=emotion, metadata=metadata)
```

Voice is optional. Your agent works perfectly with text-only chat.

---

## Step 5: Run the Demo Server

Julia Core includes a FastAPI demo server:

```bash
python server.py
# → http://127.0.0.1:8002
```

Test it:

```bash
curl -X POST http://127.0.0.1:8002/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello!"}'
```

---

## What You Just Built

```
User Input
    │
    ▼
ChatSession
    │
    ├── Persona Engine   "Demo Assistant — friendly helper"
    ├── Context OS        assembles context
    └── Chat Provider     sends to model
    │
    ▼
Response
    │
    ├── Text output
    └── (optional) Voice OS → VoiceProvider → Audio
```

This is the same architecture Julia AI Assistant uses — just with a different persona.

---

## Next Steps

- **Add domain knowledge**: [Create a Domain Provider](CREATE_DOMAIN_PROVIDER.md)
- **Customize voice**: [Create a Voice Provider](CREATE_VOICE_PROVIDER.md)
- **Define a real persona**: [Create a Persona](CREATE_PERSONA.md)
- **Understand the full architecture**: [Architecture Overview](../architecture/ARCHITECTURE_OVERVIEW.md)

---

## Common Issues

### "No model provider configured"

Julia Core does not include a model provider. For a complete agent, you need:
- A model provider (OpenAI, DeepSeek, local model, etc.)
- See `julia_ai_assistant/providers/llm/` for reference implementations

### "Persona seems generic"

That's intentional — this is a demo. Real personas load identity facts, behavior rules, and memory context. See [Create a Persona](CREATE_PERSONA.md).

### "Can I use this in production?"

Julia Core is the framework. Production agents (like Julia AI Assistant) add:
- Private identity data (persona + memory)
- Model providers (LLM API keys)
- Domain providers (financial data, etc.)
- Voice profiles

---

## Complete Example

```python
# my_first_agent.py
from julia_core.chat.persona import Persona
from julia_core.chat.session import ChatSession

# 1. Define persona
demo = Persona(
    persona_id="demo-assistant-v1",
    name="Demo Assistant",
    role="helpful assistant",
    language="en",
    tone="friendly",
    system_prompt="You are Demo Assistant, a friendly helper. Be warm and concise.",
)

# 2. Create session
session = ChatSession(persona=demo)

# 3. Chat
while True:
    user_input = input("You: ")
    if user_input.lower() in ("exit", "quit"):
        break
    response = session.send(user_input)
    print(f"Assistant: {response}")

session.close()
```
