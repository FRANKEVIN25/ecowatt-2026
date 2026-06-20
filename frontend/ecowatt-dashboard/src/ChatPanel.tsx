import { useState, useRef, useEffect } from "react";
import { MessageCircle, Send, Loader2 } from "lucide-react";

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
    <article className="rounded-lg border border-grid bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-slate-600">Asistente EcoWatt</p>
          <h2 className="text-xl font-semibold">Consulta tu consumo</h2>
        </div>
        <MessageCircle className="h-5 w-5 text-energy" aria-hidden="true" />
      </div>

      <div
        ref={scrollRef}
        className="mb-4 h-72 space-y-3 overflow-y-auto rounded-lg bg-panel p-3"
      >
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                msg.role === "user"
                  ? "bg-energy text-white"
                  : "border border-grid bg-white text-ink"
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="flex items-center gap-2 rounded-lg border border-grid bg-white px-3 py-2 text-sm text-slate-500">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Pensando...
            </div>
          </div>
        )}
      </div>

      <div className="mb-3 flex flex-wrap gap-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => sendMessage(s)}
            disabled={loading}
            className="rounded-full border border-grid bg-panel px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:border-energy hover:text-energy disabled:opacity-50"
          >
            {s}
          </button>
        ))}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          sendMessage(input);
        }}
        className="flex items-center gap-2"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Pregúntale a EcoWatt..."
          disabled={loading}
          className="flex-1 rounded-lg border border-grid px-3 py-2 text-sm outline-none focus:border-energy disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="flex items-center justify-center rounded-lg bg-energy p-2.5 text-white transition hover:opacity-90 disabled:opacity-40"
        >
          <Send className="h-4 w-4" aria-hidden="true" />
        </button>
      </form>
    </article>
  );
}