document.addEventListener("DOMContentLoaded", () => {
    const userInputElem = document.getElementById("user-input");
    const chatBox = document.getElementById("chat-box");
    const msgCount = document.getElementById("msg-count");
    const sendButton = document.getElementById("send-button");
    const voiceToggle = document.getElementById("voice-toggle");

    const formatMarkdown = (text) => {
        return text
            .replace(/([a-z])\?(?=[A-Z])/g, '$1?\n')
            .replace(/\*{2,3}\s*(Step\s*\d+:.*?)\s*\*{2,3}/gi, '\n\n**$1**\n\n')
            .replace(/\*{2,3}\s*(Ingredients|Instructions)\s*\*{2,3}/gi, '\n\n### $1\n\n')
            .replace(/(Ingredients|Instructions)(:)?/gi, '\n\n### $1\n\n')
            .replace(/(?:^|\n)[\*\-•‒–—] ?([^*\n]+)/g, '\n• $1')
            .replace(/([a-z0-9])\* ?(?=[a-z])/gi, '$1\n• ')
            .replace(/• /g, '\n• ')
            .replace(/(?<!\*)_([^_\n]+)_(?!\*)/g, '_$1_')
            .replace(/([^\n])(\*\*[^\*]+\*\*:?)/g, '$1\n\n$2\n\n')
            .replace(/(?<!\n)\n?([0-9]+\.)/g, '\n\n$1')
            .replace(/\n{3,}/g, '\n\n')
            .replace(/\.?#{3,}/g, '')
            .trim();
    };

    async function sendMessage() {
        const userInput = userInputElem.value.trim();
        if (!userInput) return;

        appendMessage("user", marked.parse(DOMPurify.sanitize(userInput)));
        userInputElem.value = "";
        sendButton.disabled = true;

        const aiBubble = appendMessage("ai", "");
        let dots = 0;
        const loading = setInterval(() => {
            dots = (dots + 1) % 4;
            aiBubble.textContent = "Thinking" + ".".repeat(dots);
        }, 500);

        const res = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: userInput })
        });

        if (!res.ok) {
            clearInterval(loading);
            aiBubble.textContent = "❌ Error communicating with server.";
            sendButton.disabled = false;
            return;
        }

        clearInterval(loading);
        const reader = res.body.getReader();
        const decoder = new TextDecoder("utf-8");

        let partial = "";
        let fullText = "";
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            partial += decoder.decode(value, { stream: true });
            const matches = [...partial.matchAll(/data: (.*?)\n\n/g)];

            for (const match of matches) {
                const token = match[1];
                fullText += token;

                const formattedMarkdown = formatMarkdown(fullText);
                const htmlOutput = DOMPurify.sanitize(marked.parse(formattedMarkdown));
                aiBubble.innerHTML = htmlOutput;
                attachCopyButton(aiBubble, fullText);
            }

            const lastDoubleNewline = partial.lastIndexOf("\n\n");
            if (lastDoubleNewline !== -1) {
                partial = partial.slice(lastDoubleNewline + 2);
            }
        }

        sendButton.disabled = false;
    }

    function appendMessage(role, html) {
        const div = document.createElement("div");
        div.className = `bubble ${role}`;
        div.innerHTML = html;
        chatBox.appendChild(div);
        scrollChatToBottom();
        msgCount.textContent = parseInt(msgCount.textContent) + 1;
        return div;
    }

    function scrollChatToBottom(force = false) {
        const nearBottom = chatBox.scrollHeight - chatBox.scrollTop - chatBox.clientHeight < 100;
        if (nearBottom || force) {
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    }

    function attachCopyButton(aiBubble, rawText) {
        const oldBtn = aiBubble.querySelector(".copy-btn");
        if (oldBtn) oldBtn.remove();

        const btn = document.createElement("button");
        btn.className = "copy-btn";
        btn.textContent = "📋 Copy";
        btn.setAttribute("aria-label", "Copy to clipboard");

        btn.onclick = async () => {
            try {
                await navigator.clipboard.writeText(rawText.trim());
                btn.textContent = "✅ Copied!";
                setTimeout(() => btn.textContent = "📋 Copy", 2000);
            } catch (err) {
                btn.textContent = "❌ Failed";
                console.error("Copy failed", err);
            }
        };

        aiBubble.style.position = "relative";
        aiBubble.appendChild(btn);
    }

    // === Voice Mode ===
let isListening = false;
let mediaRecorder;
let currentAudio = null;

function startListening() {
    if (!voiceToggle.checked || isListening) return;
    isListening = true;

    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            const audioChunks = [];
            mediaRecorder = new MediaRecorder(stream);

            mediaRecorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks);
                const formData = new FormData();
                formData.append('audio', audioBlob);

                fetch('/transcribe', {
                    method: 'POST',
                    body: formData
                })
                .then(async response => {
                    const data = await response.json();
                    const userText = data.transcribed;
                    const aiText = data.response;

                    // Append user bubble
                    appendMessage("user", marked.parse(DOMPurify.sanitize(userText)));

                    // Simulate streaming AI response like in text chat
                    const aiBubble = appendMessage("ai", "");
                    let fullText = "";
                    const stream = await fetch("/chat", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ message: userText })
                    });

                    if (!stream.ok) {
                        aiBubble.textContent = "❌ Error getting AI response.";
                        return;
                    }

                    const reader = stream.body.getReader();
                    const decoder = new TextDecoder("utf-8");
                    let partial = "";

                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;

                        partial += decoder.decode(value, { stream: true });
                        const matches = [...partial.matchAll(/data: (.*?)\n\n/g)];

                        for (const match of matches) {
                            const token = match[1];
                            fullText += token;

                            const formattedMarkdown = formatMarkdown(fullText);
                            const htmlOutput = DOMPurify.sanitize(marked.parse(formattedMarkdown));
                            aiBubble.innerHTML = htmlOutput;
                            attachCopyButton(aiBubble, fullText);
                        }

                        const lastDoubleNewline = partial.lastIndexOf("\n\n");
                        if (lastDoubleNewline !== -1) {
                            partial = partial.slice(lastDoubleNewline + 2);
                        }
                    }

                    // Play audio after full response
                    const timestamp = Date.now();
                    currentAudio = new Audio(`/audio_files/output.mp3?nocache=${timestamp}`);
                    currentAudio.play();

                    currentAudio.onended = () => {
                        isListening = false;
                        if (voiceToggle.checked) startListening(); // Auto-arm voice mode
                    };
                })
                .catch(err => {
                    console.error("Transcription or AI error:", err);
                    isListening = false;
                });
            };

            mediaRecorder.start();
            setTimeout(() => {
                if (mediaRecorder && mediaRecorder.state !== "inactive") {
                    mediaRecorder.stop();
                }
            }, 5000);
        })
        .catch(err => {
            console.error("Microphone access error:", err);
            alert("Microphone access is required to use voice mode.");
            isListening = false;
        });
}

voiceToggle.addEventListener('change', () => {
    if (voiceToggle.checked) {
        startListening();
    } else {
        isListening = false;
        if (currentAudio) currentAudio.pause();
    }
});


    // === Utility ===
    window.clearNotes = () => {
        const notesArea = document.getElementById("notes-textarea");
        if (notesArea) notesArea.value = "";
    };

    window.clearMemory = () => {
        fetch("/purge", { method: "POST" })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                chatBox.innerHTML = "";
                msgCount.textContent = "0";
            })
            .catch(error => {
                console.error("Memory purge failed:", error);
                alert("Failed to clear memory.");
            });
    };

    window.clearChat = () => {
        chatBox.innerHTML = "";
        msgCount.textContent = "0";
    };

    window.downloadLogs = () => alert("Logs downloading soon.");
    window.toggleDebug = () => alert("Debug toggled.");
    window.toggleDarkMode = () => document.body.classList.toggle("light-mode");

    setInterval(() => {
        const timestampElem = document.getElementById("timestamp");
        if (timestampElem) {
            timestampElem.textContent = new Date().toLocaleTimeString();
        }
    }, 1000);
});
