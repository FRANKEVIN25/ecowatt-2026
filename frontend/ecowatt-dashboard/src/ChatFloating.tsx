import { useState } from "react";
import { Bot, X } from "lucide-react";
import ChatPanel from "./ChatPanel";

export default function ChatFloating() {
  const [open, setOpen] = useState(false);

  return (
    <>
      {open && (
        <div className="chat-floating-panel">
          <button
            className="chat-floating-close"
            onClick={() => setOpen(false)}
            aria-label="Cerrar chat"
          >
            <X size={16} />
          </button>
          <ChatPanel />
        </div>
      )}
      <button
        className="chat-floating-button"
        onClick={() => setOpen((v) => !v)}
        aria-label="Abrir asistente EcoWatt"
      >
        <Bot size={24} />
      </button>
    </>
  );
}
