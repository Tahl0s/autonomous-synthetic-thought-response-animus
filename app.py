import os, json, subprocess, datetime
from flask import Flask, render_template, request, jsonify, Response, stream_with_context, send_from_directory
from concurrent.futures import ThreadPoolExecutor
import whisper
from gtts import gTTS

# === Setup Flask === #
app = Flask(__name__)
MEMORY_DIR = "memory"
os.makedirs(MEMORY_DIR, exist_ok=True)

# === Memory Files === #
CHAT_LOG = os.path.join(MEMORY_DIR, "chat_log.json")
CHAT_SUMMARY = os.path.join(MEMORY_DIR, "chat_summary.txt")
LT_HISTORY = os.path.join(MEMORY_DIR, "lt_summary_history.txt")
LONG_TERM = os.path.join(MEMORY_DIR, "long_term_memory.txt")
PERSONALITY = os.path.join(MEMORY_DIR, "personality.txt")

# === Whisper Model === #
whisper_model = whisper.load_model("small")
executor = ThreadPoolExecutor()

# === Ensure Defaults === #
def init_files():
    defaults = {
        PERSONALITY: "Supportive, strategic, emotionally aware, efficient, proactive, insightful, and structured.",
        CHAT_LOG: json.dumps([]),
        CHAT_SUMMARY: "",
        LT_HISTORY: "",
        LONG_TERM: ""
    }
    for file, content in defaults.items():
        if not os.path.exists(file):
            with open(file, 'w') as f:
                f.write(content)

init_files()

# === Load/Save Helpers === #
def load_json(path):
    return json.load(open(path)) if os.path.exists(path) else []

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

def read_file(path):
    return open(path).read().strip() if os.path.exists(path) else ""

def write_file(path, content):
    with open(path, 'w') as f:
        f.write(content)

# === AI Model === #
try:
    from langchain_ollama import OllamaLLM
except:
    subprocess.check_call(["pip", "install", "langchain-ollama"])
    from langchain_ollama import OllamaLLM

model = OllamaLLM(model="llama3")

# === Prompt Creation === #
def create_prompt(user_input):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    personality = read_file(PERSONALITY)
    summary = read_file(CHAT_SUMMARY)
    long_term = read_file(LONG_TERM)
    recent_log = load_json(CHAT_LOG)[-6:]

    def format_entry(x):
        if x.get("role") == "user":
            return f"User: {x['text']}"
        elif x.get("role") == "ai":
            return f"Astra: {x['text']}"
        return ""

    recent_formatted = "\n".join([format_entry(x) for x in recent_log if format_entry(x)])

    prompt = f"""
Your name is Astra. You're an intelligent, proactive, and supportive AI assistant with a personality described as:
{personality}

Today is {now}.

Here's what you recall from earlier interactions:
{long_term or 'No long-term memory stored yet.'}

Here’s a brief summary of what’s been going on:
{summary or "Nothing major noted yet."}

Here's how your recent conversation went:
{recent_formatted}

Based on everything above, respond like a close friend or trusted collaborator. Speak like a clever and caring friend. Be concise, relaxed, and natural. Don’t repeat yourself. Share one clear idea per message, unless asked for more. Avoid lecturing. Use paragraph breaks for long replies.

If you're writing steps or instructions:
- Start each step with a numbered list (1., 2.) **with a blank line before each**
- Never glue steps together (each step should be on its own line)
- Use ### Ingredients and ### Instructions as headers
- Use • bullets for ingredients
- Keep formatting clean — no repeated bold or asterisks

User: {user_input}

Astra:"""
    return prompt.strip()

# === AI Call === #
def generate_response(user_input):
    prompt = create_prompt(user_input)
    response = model.invoke(prompt).strip()
    return format_response(response)

def format_response(text):
    import re
    text = re.sub(r"###\s*ingredients", "### Ingredients", text, flags=re.IGNORECASE)
    text = re.sub(r"###\s*instructions", "### Instructions", text, flags=re.IGNORECASE)
    text = re.sub(r"\*{2,3}\s*(Ingredients|Instructions)\s*\*{2,3}", r"### \1", text, flags=re.IGNORECASE)
    text = re.sub(r"(?:^|(?<=\n))[\*\-•‒–—]\s*(.+?)(?=(?:\n|[\*\-•‒–—]|$))", r"\n• \1", text)
    text = re.sub(r"•\s*", r"\n• ", text)
    text = re.sub(r"([a-zA-Z0-9])(\)\s*Now,)", r"\1.\n\n\2", text)
    text = re.sub(r"(optional\))(?=\s*Now,)", r"\1\n\n", text)
    text = re.sub(r"\n?([0-9]+\.)\s*\n?(\*\*.+?\*\*)", r"\n\n\1 \2", text)
    text = re.sub(r"\n+([0-9]+\.)", r"\n\n\1", text)
    text = re.sub(r"\n?\*{2,}\n?", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\n\s*•", "\n•", text)
    return text.strip()

# === Memory === #
def append_chat(user_text, ai_response):
    chat = load_json(CHAT_LOG)
    timestamp = datetime.datetime.now().isoformat()
    chat.append({"role": "user", "text": user_text, "timestamp": timestamp})
    chat.append({"role": "ai", "text": ai_response, "timestamp": timestamp})
    save_json(CHAT_LOG, chat)

def summarize_chat():
    chat = load_json(CHAT_LOG)
    if len(chat) % 6 != 0:
        return
    recent = chat[-20:]
    lines = []
    for i in range(0, len(recent), 2):
        if i + 1 < len(recent):
            user = recent[i]
            ai = recent[i + 1]
            if user["role"] == "user" and ai["role"] == "ai":
                lines.append(f"User: {user['text']}\nAstra: {ai['text']}")
    flat = "\n".join(lines)
    if not flat:
        return
    summary_prompt = f"Summarize the key points clearly from this conversation:\n\n{flat}"
    summary = model.invoke(summary_prompt).strip()
    write_file(CHAT_SUMMARY, summary)
    history = read_file(LT_HISTORY)
    full_history = "\n---\n".join(filter(None, [history, summary]))
    write_file(LT_HISTORY, full_history)
    update_long_term()

def update_long_term():
    history = read_file(LT_HISTORY).split("\n---\n")
    if len(history) >= 5:
        recent = "\n".join(history[-5:])
        condensed_prompt = f"Condense the following conversation summaries into a clear long-term memory:\n\n{recent}"
        condensed = model.invoke(condensed_prompt).strip()
        write_file(LONG_TERM, condensed)
        write_file(LT_HISTORY, "\n---\n".join(history[:-5]))

# === Routes === #
@app.route("/")
def index():
    return render_template("astra2.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "")
    def generate():
        full_response = ""
        for token in model.stream(create_prompt(user_input)):
            full_response += token
            yield f"data: {token}\n\n"
        append_chat(user_input, full_response.strip())
        summarize_chat()
    return Response(stream_with_context(generate()), mimetype="text/event-stream")

@app.route("/purge", methods=["POST"])
def purge():
    for file in [CHAT_LOG, CHAT_SUMMARY, LT_HISTORY, LONG_TERM]:
        write_file(file, "" if file.endswith('.txt') else json.dumps([]))
    return jsonify({"message": "Memory cleared."})

audio_dir = os.path.join(os.getcwd(), "audio_files")
os.makedirs(audio_dir, exist_ok=True)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    audio = request.files['audio']
    audio_path = os.path.join(audio_dir, "audio.wav")
    audio.save(audio_path)

    def transcribe_audio():
        result = whisper_model.transcribe(audio_path)
        return result['text'].strip()

    future = executor.submit(transcribe_audio)
    user_text = future.result()
    print(f"User said: {user_text}")
    ai_response = generate_response(user_text)
    append_chat(user_text, ai_response)

    try:
        tts = gTTS(ai_response)
        output_path = os.path.join(audio_dir, 'output.mp3')

        # 🔥 Ensure directory exists and is writable
        if not os.path.exists(audio_dir):
            os.makedirs(audio_dir)

        tts.save(output_path)
        print(f"[✅] TTS saved to {output_path}")
        print(f"Astra replied: {ai_response}")
    except Exception as e:
        print("[❌] TTS Error:", e)

    return jsonify({"transcribed": user_text, "response": ai_response})

@app.route('/speak', methods=['POST'])
def speak():
    text = request.json.get('text', '')
    print(f"Received text for speech: {text}")
    if not text:
        return jsonify({'error': 'No text provided for speech'}), 400
    try:
        tts = gTTS(text)
        audio_path = os.path.join(audio_dir, 'output.mp3')
        #tts.save(audio_path)
        #subprocess.run(["start", audio_path], shell=True)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/personality", methods=["GET", "POST"])
def personality():
    if request.method == "POST":
        personality_text = request.json.get("personality", "")
        write_file(PERSONALITY, personality_text)
    return jsonify({"personality": read_file(PERSONALITY)})

@app.route('/audio_files/<filename>')
def serve_audio(filename):
    return send_from_directory(audio_dir, filename)

if __name__ == "__main__":
    app.run(debug=True)