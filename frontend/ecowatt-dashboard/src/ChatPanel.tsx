import { useEffect, useRef, useState } from "react";
import { Bot, Loader2, Send, Sparkles } from "lucide-react";

const API_BASE = "http://127.0.0.1:8000/api";

type ChatMessage = {
  role: "user" | "assistant";
  text: string;
};

const SUGGESTIONS = [
  "¿Qué consume más en mi casa?",
  "¿Cómo puedo ahorrar energía?",
  "¿Por qué subió mi consumo?",
];

export default function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      text: "Hola, soy el asistente de EcoWatt. Pregúntame sobre tu consumo eléctrico actual.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage(pregunta: string) {
    if (!pregunta.trim() || loading) return;

    setMessages((prev) => [...prev, { role: "user", text: pregunta }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pregunta }),
      });

      if (!res.ok) {
        throw new Error("Error del servidor");
      }

      const data = await res.json();
      setMessages((prev) => [...prev, { role: "assistant", text: data.respuesta }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "No pude conectarme al asistente en este momento. Intenta de nuevo en unos segundos.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <article className="glass-panel chat-panel">
      <div className="panel-heading">
        <div className="flex items-center gap-3">
          <div className="ai-avatar">
            <Bot size={20} />
          </div>
          <div>
            <p className="eyebrow">EcoWatt AI · Gemini</p>
            <h3 className="panel-title">Asistente de consumo</h3>
          </div>
        </div>
      </div>

      <div ref={scrollRef} className="chat-scroll">
        {messages.map((msg, i) => (
          <div key={i} className={`chat-row chat-row-${msg.role}`}>
            <div className={`chat-bubble chat-bubble-${msg.role}`}>{msg.text}</div>
          </div>
        ))}
        {loading && (
          <div className="chat-row chat-row-assistant">
            <div className="chat-bubble chat-bubble-assistant chat-bubble-loading">
              <Loader2 size={14} className="animate-spin" />
              Pensando...
            </div>
          </div>
        )}
      </div>

      <div className="chat-suggestions">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => sendMessage(s)}
            disabled={loading}
            className="chat-suggestion"
          >
            <Sparkles size={12} />
            {s}
          </button>
        ))}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          sendMessage(input);
        }}
        className="chat-input-row"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Pregúntale a EcoWatt..."
          disabled={loading}
          className="chat-input"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="chat-send"
          aria-label="Enviar"
        >
          <Send size={16} />
        </button>
      </form>
    </article>
  );
}
