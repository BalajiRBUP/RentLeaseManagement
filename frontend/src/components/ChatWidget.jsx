import { useState, useRef, useEffect } from "react";
import { askChatbot } from "../api/client";
import "../styles/chatWidget.css";

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "bot",
      text: "Hi! Ask me anything about your agreements, lease schedules, postings or vendors.",
    },
  ]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, open]);

  const send = async () => {
    const question = input.trim();
    if (!question || loading) return;

    setMessages((m) => [...m, { role: "user", text: question }]);
    setInput("");
    setLoading(true);

    try {
      const res = await askChatbot(question);
      setMessages((m) => [
        ...m,
        { role: "bot", text: res.answer, sql: res.sql, rows: res.rows },
      ]);
    } catch (err) {
      const detail = err?.response?.data?.detail || "Something went wrong answering that.";
      setMessages((m) => [...m, { role: "bot", text: detail, error: true }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="chat-widget-root">
      {open && (
        <div className="chat-panel">
          <div className="chat-panel-header">
            <span>Ask AI</span>
            <button
              type="button"
              className="chat-close-btn"
              onClick={() => setOpen(false)}
              aria-label="Close chat"
            >
              ✕
            </button>
          </div>

          <div className="chat-messages">
            {messages.map((m, i) => (
              <div key={i} className={`chat-bubble chat-bubble-${m.role}${m.error ? " chat-bubble-error" : ""}`}>
                <div>{m.text}</div>
                {m.rows && m.rows.length > 0 && (
                  <div className="chat-result-table-wrap">
                    <table className="chat-result-table">
                      <thead>
                        <tr>
                          {Object.keys(m.rows[0]).map((col) => (
                            <th key={col}>{col}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {m.rows.slice(0, 10).map((row, ri) => (
                          <tr key={ri}>
                            {Object.keys(m.rows[0]).map((col) => (
                              <td key={col}>{String(row[col] ?? "")}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ))}
            {loading && <div className="chat-bubble chat-bubble-bot chat-bubble-loading">Thinking…</div>}
            <div ref={bottomRef} />
          </div>

          <div className="chat-input-row">
            <textarea
              rows={1}
              value={input}
              placeholder="e.g. What agreements expire in the next 90 days?"
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button type="button" onClick={send} disabled={loading || !input.trim()}>
              Send
            </button>
          </div>
        </div>
      )}

      <button
        type="button"
        className="chat-fab"
        onClick={() => setOpen((o) => !o)}
        title="Ask AI about your data"
      >
        {open ? "✕" : "💬"}
      </button>
    </div>
  );
}
