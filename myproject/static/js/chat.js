/*
 * Shared chat UI for the AI tools (flashcards "Echo" and the evaluation
 * assistant). Each page calls initChat(config) on DOMContentLoaded; the
 * config supplies everything page-specific:
 *
 *   streamUrl   POST endpoint that streams the assistant reply
 *   markdown    render assistant messages as markdown (needs marked.js)
 *   thinking    show a "thinking" bubble while waiting for the first byte
 *   stripPattern  regex removed from the displayed assistant text
 *   canSend()   return false to block sending (e.g. no active session)
 *   onChunk(chunk, fullText)        called per streamed chunk
 *   onComplete(fullText, bubble)    called after the stream finishes
 *
 * initChat assigns window.sendMessage / window.appendMessage so the
 * templates' inline onclick handlers keep working.
 */

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function initChat(config) {
    const messagesDiv = () => document.getElementById(config.messagesId || "messages");
    const inputEl = () => document.getElementById(config.inputId || "messageInput");

    function renderMarkdown(text) {
        if (!config.markdown || typeof marked === "undefined") {
            return null; // caller falls back to safe plain-text rendering
        }
        return marked.parse(text, { gfm: true });
    }

    function setPlainText(el, text) {
        el.replaceChildren();
        for (const paragraph of text.split(/\n+/)) {
            const p = document.createElement("p");
            p.textContent = paragraph;
            el.appendChild(p);
        }
    }

    function setAssistantContent(el, text) {
        const html = renderMarkdown(text);
        if (html === null) {
            setPlainText(el, text);
        } else {
            el.innerHTML = html;
        }
        if (config.decorateAssistant) config.decorateAssistant(el);
    }

    function appendMessage(sender, text) {
        const container = messagesDiv();
        const div = document.createElement("div");
        div.classList.add("message", sender);
        if (sender === "assistant" && text) {
            setAssistantContent(div, text);
        } else if (text) {
            setPlainText(div, text);
        }
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
        return div;
    }

    function showThinkingBubble() {
        if (!config.thinking) return;
        const container = messagesDiv();
        const div = document.createElement("div");
        div.className = "message assistant thinking-bubble";
        div.id = "ai-thinking-bubble";
        div.innerHTML = '<span class="spinner"></span> <span>Echo is thinking...</span>';
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    }

    function removeThinkingBubble() {
        document.getElementById("ai-thinking-bubble")?.remove();
    }

    async function sendMessage() {
        const input = inputEl();
        const text = input.value.trim();
        if (!text) return;
        if (config.canSend && !config.canSend()) return;

        appendMessage("user", text);
        input.value = "";
        showThinkingBubble();

        try {
            const response = await fetch(config.streamUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie("csrftoken")
                },
                body: JSON.stringify({ message: text })
            });

            if (!response.ok || !response.body) {
                removeThinkingBubble();
                appendMessage("assistant", "⚠️ Error: Failed to stream response.");
                return;
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let fullText = "";

            removeThinkingBubble();
            const assistantBubble = appendMessage("assistant", "");

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                fullText += chunk;
                if (config.onChunk) config.onChunk(chunk, fullText);

                let displayText = config.stripPattern
                    ? fullText.replace(config.stripPattern, "").trim()
                    : fullText;
                setAssistantContent(assistantBubble, displayText);
                const container = messagesDiv();
                container.scrollTop = container.scrollHeight;
            }

            if (config.onComplete) await config.onComplete(fullText, assistantBubble);

        } catch (err) {
            removeThinkingBubble();
            appendMessage("assistant", "⚠️ Network error. See console.");
            console.error("Network error:", err);
        }
    }

    // Expose for inline onclick handlers in the templates
    window.sendMessage = sendMessage;
    window.appendMessage = appendMessage;

    return { sendMessage, appendMessage };
}
