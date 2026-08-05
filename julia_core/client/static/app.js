const sessionId = crypto.randomUUID();
let voiceOutputEnabled = true;
const messages = document.getElementById('messages');
const trace = document.getElementById('trace');
const input = document.getElementById('text-input');
const form = document.getElementById('chat-form');
const voiceIn = document.getElementById('voice-in');
const voiceOut = document.getElementById('voice-out');
let currentAudio = null;
const health = document.getElementById('health');

function addMessage(role, text) {
  const el = document.createElement('div');
  el.className = `message ${role}`;
  const label = role === 'user' ? 'Tony' : 'Julia';
  el.innerHTML = `<span class="label">${label}</span><span class="content">${escapeHtml(text)}</span>`;
  messages.appendChild(el);
  messages.scrollTop = messages.scrollHeight;
  return el;
}

function setMessageText(el, text) {
  const content = el.querySelector('.content');
  content.textContent = text;
  messages.scrollTop = messages.scrollHeight;
}

function escapeHtml(value) {
  return value.replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
}

async function checkHealth() {
  try {
    const res = await fetch('/health');
    const data = await res.json();
    health.textContent = `${data.status} · ${data.persona || 'Julia'}`;
    health.classList.add('ok');
  } catch (_) {
    health.textContent = 'offline';
    health.classList.remove('ok');
  }
}

async function sendMessage(text, mode = 'text') {
  if (!text.trim()) return;
  addMessage('user', text);
  input.value = '';
  try {
    await streamMessage(text, mode);
  } catch (error) {
    trace.textContent = JSON.stringify({ stream: 'fallback', reason: String(error) }, null, 2);
    await sendMessageFallback(text, mode);
  }
}

async function streamMessage(text, mode = 'text') {
  const assistantEl = addMessage('assistant', '');
  let full = '';
  const res = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ text, session_id: sessionId, interaction_mode: mode, voice_output: voiceOutputEnabled })
  });
  if (!res.ok || !res.body) throw new Error(`stream failed: ${res.status}`);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split('\n\n');
    buffer = events.pop() || '';
    for (const raw of events) {
      const parsed = parseSseEvent(raw);
      if (!parsed) continue;
      if (parsed.event === 'trace') {
        trace.textContent = JSON.stringify(parsed.data, null, 2);
      }
      if (parsed.event === 'chunk' || parsed.event === 'text_delta') {
        full += parsed.data.text || parsed.data.content || '';
        setMessageText(assistantEl, full);
      }
    }
  }
  if (voiceOutputEnabled) speak(full);
}

function parseSseEvent(raw) {
  const lines = raw.split('\n');
  const eventLine = lines.find(line => line.startsWith('event: '));
  const dataLine = lines.find(line => line.startsWith('data: '));
  if (!eventLine || !dataLine) return null;
  return { event: eventLine.slice(7), data: JSON.parse(dataLine.slice(6)) };
}

async function sendMessageFallback(text, mode = 'text') {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ text, session_id: sessionId, interaction_mode: mode, voice_output: voiceOutputEnabled })
  });
  const data = await res.json();
  addMessage('assistant', data.reply || '');
  trace.textContent = JSON.stringify(data.trace || {}, null, 2);
  if (voiceOutputEnabled) speak(data.reply || '');
}

async function speak(text) {
  if (!text) return;
  try {
    const res = await fetch('/api/voice/synthesize', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ text })
    });
    if (!res.ok) throw new Error(`voice service failed: ${res.status}`);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    if (currentAudio) {
      currentAudio.pause();
      URL.revokeObjectURL(currentAudio.src);
    }
    currentAudio = new Audio(url);
    await currentAudio.play();
  } catch (error) {
    trace.textContent = JSON.stringify({ voice: 'edge_tts_failed', fallback: 'browser_speechSynthesis', reason: String(error) }, null, 2);
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'zh-CN';
      utterance.rate = 0.92;
      utterance.pitch = 1.08;
      window.speechSynthesis.speak(utterance);
    }
  }
}


function setupVoiceInput() {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) {
    voiceIn.title = '当前浏览器未提供 SpeechRecognition；可使用文字输入';
    voiceIn.disabled = true;
    return;
  }
  const recognition = new Recognition();
  recognition.lang = 'zh-CN';
  recognition.interimResults = false;
  recognition.continuous = false;
  recognition.onstart = () => voiceIn.classList.add('active');
  recognition.onend = () => voiceIn.classList.remove('active');
  recognition.onerror = (event) => {
    trace.textContent = JSON.stringify({ input: { type: 'voice', stt: 'error', reason: event.error } }, null, 2);
  };
  recognition.onresult = (event) => {
    const text = Array.from(event.results).map(r => r[0].transcript).join('');
    sendMessage(text, 'voice');
  };
  voiceIn.addEventListener('click', () => recognition.start());
}

form.addEventListener('submit', (event) => {
  event.preventDefault();
  sendMessage(input.value, 'text');
});

input.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendMessage(input.value, 'text');
  }
});

voiceOut.addEventListener('click', () => {
  voiceOutputEnabled = !voiceOutputEnabled;
  voiceOut.classList.toggle('active', voiceOutputEnabled);
  if (!voiceOutputEnabled) { if (currentAudio) currentAudio.pause(); if ('speechSynthesis' in window) window.speechSynthesis.cancel(); }
});
voiceOut.classList.toggle('active', voiceOutputEnabled);

addMessage('assistant', 'Tony，我在。现在这个客户端支持文字输入/输出，也支持浏览器语音输入和语音输出。');
setupVoiceInput();
checkHealth();
