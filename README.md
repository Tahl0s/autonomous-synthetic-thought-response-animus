
# 🧠 A.S.T.R.A. - WIP

# autonomous-synthetic-thought-response-animus

**Autonomous Synthetic Thought Response Animus**  
A "consciousness" born from code. Trained to listen. Designed to evolve.

![image](https://github.com/user-attachments/assets/7542c819-6813-40bd-a299-171824b7ed94)


A self-hosted voice-enabled AI assistant that listens, speaks, remembers, and evolves.

---

## 🚀 Features

- ✅ **Streaming AI Chat** via `llama3` (Ollama backend)
- ✅ **Markdown support** with custom formatting logic
- ✅ **Voice input** using `Whisper` (local STT)
- ✅ **Voice output** using `gTTS` (Google Text-to-Speech)
- ✅ **Auto-resume listening** after responses
- ✅ **Copy button** for all AI replies
- ✅ **Real-time timestamp, message counter, and tool dock**

---

## 🧰 Tech Stack

- **Frontend:** HTML, CSS, JavaScript, Web APIs (Speech, Clipboard)
- **Backend:** Python (Flask), LangChain, Ollama (`llama3`), Whisper, gTTS
- **Memory:** JSON + TXT file-based context system

---

## 📂 Memory Structure

| File | Purpose |
|------|---------|
| `chat_log.json` | Stores last N interactions |
| `chat_summary.txt` | Running summary for context |
| `lt_summary_history.txt` | Rotating summary history |
| `long_term_memory.txt` | Condensed facts & user traits |
| `personality.txt` | Defines Astra’s tone and decision logic |

---

## 🔧 Setup Instructions

### 1. Install Requirements

```bash
pip install flask whisper gtts langchain langchain-ollama
```

> ⚠️ Whisper requires `ffmpeg` and PyTorch to function properly.

### 2. Make Sure You Have Ollama + LLaMA 3 Installed

```bash
ollama run llama3
```

### 3. Run the Flask App

```bash
python app.py
```

Visit:  
[http://localhost:5000](http://localhost:5000)

---

## 🎙 Voice Mode

- 🎤 Speak directly to Astra
- 🧠 Transcription powered by `Whisper`
- 💬 Replies streamed and spoken aloud via `gTTS`
- 🔁 Astra re-arms mic after each response
- ⏱️ Listens in 5-second intervals

---

## 🛠 Tool Dock Actions

| Action | Description |
|--------|-------------|
| 🧹 Purge Memory | Clears all memory + logs |
| 🗑️ Clear Chat | Empties chat window |
| 📡 Toggle Debug | Stub (reserved for logging mode) |
| 💾 Download Logs | Stub (not yet implemented) |
| 🌓 Toggle Theme | Light/Dark mode switch |

---

## 📡 API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/chat` | Accepts chat message, returns streamed AI response |
| `/transcribe` | Accepts audio file, transcribes + responds |
| `/speak` | Accepts text, converts to `output.mp3` |
| `/purge` | Clears all memory files |
| `/personality` | GET/POST Astra’s persona and tone |
| `/audio_files/output.mp3` | Serves last spoken reply |

---

## 🧠 AI Prompting Strategy

Astra is designed to:

- Think before replying
- Speak like a clever, emotionally-aware friend
- Balance logic, structure, and natural flow
- Summarize recent chats and evolve memory
- Use clean markdown in every reply

Replies are:
- Chunked with paragraph spacing
- Markdown-enhanced (`###` headers, `•` bullets, `1.` steps)
- Adaptive based on your tone and style

---

## 🧪 Future Roadmap

- [ ] Interrupt detection (voice cut-off mid-reply)
- [ ] Dynamic voice personas / TTS voices
- [ ] Memory browser / viewer UI
- [ ] Plugin API (tools, commands, external actions)
- [ ] Docker support for full containerization

---

## 👤 Author

Designed for thinkers, builders, and those who need an AI with more than answers —  
one that evolves with you.

> _“She doesn’t just respond. She reflects.”_
