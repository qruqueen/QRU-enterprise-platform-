import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Send, Sparkles, CornerDownRight, Boxes } from "lucide-react";

const SUGGESTIONS = [
  "Create a Knowledge Record about how the human liver detoxifies the body",
  "Start research on the benefits of strength training for longevity",
  "Create a Manufacturing Order for a poster and quiz about hydration for students",
  "What is the QRU manufacturing workflow?",
];

export default function CommandCenter() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    api.get("/command/history").then((r) => {
      setMessages(r.data.map((m) => ({ role: m.role, text: m.message, created: m.created })));
    }).catch(() => {});
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = async (text) => {
    const msg = text ?? input;
    if (!msg.trim() || loading) return;
    setMessages((m) => [...m, { role: "user", text: msg }]);
    setInput("");
    setLoading(true);
    try {
      const { data } = await api.post("/command", { message: msg });
      setMessages((m) => [...m, { role: "assistant", text: data.reply, created: data.created }]);
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", text: "Command failed. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  const createdLink = (created) => {
    if (!created) return null;
    const path = created.type === "ManufacturingOrder" ? "/manufacturing" : "/knowledge";
    return (
      <Link to={path} className="inline-flex items-center gap-1.5 mt-2 text-xs text-primary font-medium hover:underline">
        <CornerDownRight className="w-3 h-3" />
        {created.code} · {created.title}
      </Link>
    );
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <PageHeader
        overline="QRU Command Console"
        title="Operate by Command"
        description="Issue natural-language commands. The Chief Executive Agent™ interprets and triggers enterprise workflows automatically."
      />

      <div className="flex-1 bg-card border rounded-md flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto p-6 space-y-5" data-testid="command-messages">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <div className="w-12 h-12 rounded-md bg-primary/10 text-primary flex items-center justify-center mb-4">
                <Boxes className="w-6 h-6" />
              </div>
              <h3 className="font-heading text-lg font-semibold">Command the enterprise</h3>
              <p className="text-muted-foreground text-sm mt-1 max-w-md">
                Try one of these to see QRU manufacture understanding:
              </p>
              <div className="grid sm:grid-cols-2 gap-2 mt-5 max-w-2xl">
                {SUGGESTIONS.map((s, i) => (
                  <button
                    key={i}
                    data-testid={`command-suggestion-${i}`}
                    onClick={() => send(s)}
                    className="text-left text-sm border rounded-sm px-3 py-2.5 hover:border-primary hover:bg-muted/50 transition-colors"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[80%] ${m.role === "user" ? "" : "flex gap-3"}`}>
                {m.role === "assistant" && (
                  <div className="w-7 h-7 rounded-sm bg-primary/10 text-primary flex items-center justify-center shrink-0">
                    <Sparkles className="w-4 h-4" />
                  </div>
                )}
                <div
                  className={`rounded-md px-4 py-2.5 text-sm ${
                    m.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"
                  }`}
                >
                  <p className="whitespace-pre-wrap leading-relaxed">{m.text}</p>
                  {m.role === "assistant" && createdLink(m.created)}
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex gap-3">
              <div className="w-7 h-7 rounded-sm bg-primary/10 text-primary flex items-center justify-center">
                <Sparkles className="w-4 h-4 animate-pulse" />
              </div>
              <div className="bg-muted rounded-md px-4 py-3 text-sm text-muted-foreground">Processing command…</div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        <form
          onSubmit={(e) => { e.preventDefault(); send(); }}
          className="border-t p-4 flex gap-2"
        >
          <input
            data-testid="command-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="e.g. Create a Knowledge Record about how vaccines work…"
            className="flex-1 px-4 py-2.5 rounded-sm border bg-background outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors text-sm"
          />
          <button
            data-testid="command-send"
            type="submit"
            disabled={loading}
            className="bg-primary text-primary-foreground px-4 rounded-sm hover:bg-primary/90 transition-colors disabled:opacity-60"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
