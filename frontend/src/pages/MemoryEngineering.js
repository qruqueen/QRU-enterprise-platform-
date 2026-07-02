import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import { Loader2, Brain, Sparkles, Music2, Users, Repeat, MessageSquare, Baby, ChevronRight } from "lucide-react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";

const STATUS_STYLE = {
  manufactured: { bg: "hsl(var(--success) / 0.12)", color: "hsl(var(--success))", label: "Memory Ready" },
  manufacturing: { bg: "hsl(var(--primary) / 0.12)", color: "hsl(var(--primary))", label: "Engineering…" },
  failed: { bg: "hsl(var(--destructive) / 0.12)", color: "hsl(var(--destructive))", label: "Failed" },
  not_started: { bg: "hsl(var(--muted))", color: "hsl(var(--muted-foreground))", label: "Not Started" },
};

function Asset({ icon: Icon, label, children }) {
  return (
    <div className="bg-card border rounded-xl p-4" data-testid={`memory-asset-${label}`}>
      <p className="overline text-primary mb-2 flex items-center gap-1.5"><Icon className="w-3.5 h-3.5" />{label}</p>
      {children}
    </div>
  );
}

export default function MemoryEngineering() {
  const [records, setRecords] = useState([]);
  const [characters, setCharacters] = useState([]);
  const [sel, setSel] = useState(null);
  const [assets, setAssets] = useState(null);
  const [status, setStatus] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get("/memory/records").then((r) => setRecords(r.data.records));
    api.get("/memory/characters").then((r) => setCharacters(r.data.characters));
  }, []);

  const loadMemory = useCallback(async (kr) => {
    setSel(kr); setAssets(null);
    const { data } = await api.get(`/memory/${kr.id}`);
    setStatus(data.memory_status);
    setAssets(data.memory_assets);
  }, []);

  const manufacture = async () => {
    if (!sel) return;
    setBusy(true);
    await api.post(`/memory/manufacture/${sel.id}`);
    toast.info("Memory Engineering™ started…");
    setStatus("manufacturing");
    const poll = setInterval(async () => {
      const { data } = await api.get(`/memory/${sel.id}`);
      setStatus(data.memory_status);
      if (data.memory_status === "manufactured" || data.memory_status === "failed") {
        clearInterval(poll);
        setAssets(data.memory_assets);
        setBusy(false);
        setRecords((rs) => rs.map((r) => r.id === sel.id ? { ...r, memory_status: data.memory_status } : r));
        toast[data.memory_status === "manufactured" ? "success" : "error"](
          data.memory_status === "manufactured" ? "Memory assets manufactured 🧠" : "Memory engineering failed.");
      }
    }, 3000);
  };

  return (
    <div>
      <PageHeader overline="Memory Engineering™ · Enterprise Mode" title="Memory Engineering"
        description="QRU doesn't only teach — it helps people remember. Manufacture reusable memory assets from verified understanding." />

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Record list */}
        <div className="lg:col-span-1">
          <p className="overline text-primary mb-3">Verified Records</p>
          <div className="space-y-2" data-testid="memory-records">
            {records.map((r) => {
              const st = STATUS_STYLE[r.memory_status || "not_started"] || STATUS_STYLE.not_started;
              return (
                <button key={r.id} data-testid={`memory-record-${r.id}`} onClick={() => loadMemory(r)}
                  className={`w-full text-left bg-card border rounded-xl p-3 hover:border-primary transition-colors ${sel?.id === r.id ? "border-primary" : "border-border"}`}>
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium line-clamp-1">{r.title}</p>
                    <ChevronRight className="w-4 h-4 text-muted-foreground shrink-0" />
                  </div>
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-[10px] text-muted-foreground">{r.kr_code}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full font-medium" style={{ background: st.bg, color: st.color }}>{st.label}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Detail */}
        <div className="lg:col-span-2">
          {!sel ? (
            <div className="bg-card border rounded-2xl p-12 text-center text-muted-foreground">
              <Brain className="w-10 h-10 mx-auto mb-3" strokeWidth={1.5} />
              <p className="font-heading">Select a verified record to engineer its memory assets.</p>
            </div>
          ) : (
            <div>
              <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
                <div>
                  <p className="text-xs text-muted-foreground">{sel.kr_code}</p>
                  <h2 className="font-heading text-xl font-bold">{sel.title}</h2>
                </div>
                <button data-testid="memory-manufacture-btn" onClick={manufacture} disabled={busy || status === "manufacturing"}
                  className="px-5 py-2 rounded-md text-white text-sm font-medium flex items-center gap-2 disabled:opacity-60" style={{ background: "hsl(var(--royal))" }}>
                  {(busy || status === "manufacturing") ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                  {assets ? "Re-engineer Memory" : "Manufacture Memory Assets™"}
                </button>
              </div>

              {status === "manufacturing" && <div className="text-center py-16 text-muted-foreground"><Sparkles className="w-8 h-8 mx-auto mb-2 animate-pulse text-primary" /><p>Memory Engineering™ is composing hooks, chants, and character scripts…</p></div>}

              {assets && status !== "manufacturing" && (
                <div className="space-y-4" data-testid="memory-assets">
                  <div className="rounded-2xl p-6 text-white" style={{ background: "linear-gradient(135deg, hsl(var(--royal)), hsl(var(--navy)))" }}>
                    <p className="overline mb-2" style={{ color: "hsl(var(--gold))" }}>QRU Memory Hook™ (5-15s)</p>
                    <p className="font-heading text-xl font-semibold leading-snug">{assets.memory_hook}</p>
                    <p className="text-xs text-white/70 mt-3">Rhythm: {assets.memory_rhythm}</p>
                  </div>

                  <div className="grid sm:grid-cols-2 gap-4">
                    <Asset icon={Brain} label="Memory Sentence™"><p className="text-sm">{assets.memory_sentence}</p></Asset>
                    <Asset icon={Repeat} label="One-Line Repeat™"><p className="text-sm">{assets.one_line_repeat}</p></Asset>
                    <Asset icon={Music2} label="Memory Chant™"><p className="text-sm whitespace-pre-wrap">{assets.memory_chant}</p></Asset>
                    <Asset icon={MessageSquare} label="Call & Response™">
                      <div className="space-y-1.5">{(assets.call_and_response || []).map((c, i) => (
                        <div key={i} className="text-sm"><span className="font-medium text-primary">Call:</span> {c.call}<br /><span className="font-medium" style={{ color: "hsl(var(--gold))" }}>Response:</span> {c.response}</div>
                      ))}</div>
                    </Asset>
                  </div>

                  <Asset icon={Music2} label="Educational Lyrics™">
                    <p className="text-sm"><b>Chorus</b><br /><span className="whitespace-pre-wrap">{assets.educational_lyrics?.chorus}</span></p>
                    <p className="text-sm mt-2"><b>Verse</b><br /><span className="whitespace-pre-wrap">{assets.educational_lyrics?.verse}</span></p>
                  </Asset>

                  <Asset icon={Users} label="Character Scripts™">
                    <div className="space-y-2">{(assets.character_scripts || []).map((s, i) => (
                      <div key={i} className="border-l-2 pl-3" style={{ borderColor: "hsl(var(--gold))" }}>
                        <p className="text-xs font-semibold text-primary">{s.character}</p>
                        <p className="text-sm italic">"{s.script}"</p>
                      </div>
                    ))}</div>
                  </Asset>

                  <Asset icon={MessageSquare} label="Character Dialogue™">
                    <div className="space-y-1">{(assets.character_dialogue || []).map((s, i) => (
                      <p key={i} className="text-sm"><span className="font-semibold text-primary">{s.character}:</span> {s.line}</p>
                    ))}</div>
                  </Asset>

                  <Asset icon={Baby} label="Legacy Learners™ — Adaptive Versions">
                    <div className="grid sm:grid-cols-2 gap-3 text-sm">
                      {["child", "teen", "adult", "professional"].map((k) => (
                        <div key={k}><p className="text-xs font-semibold capitalize text-muted-foreground">{k}</p><p>{assets.legacy_learners?.[k]}</p></div>
                      ))}
                    </div>
                  </Asset>

                  <div className="grid sm:grid-cols-2 gap-4">
                    <Asset icon={Music2} label="Music Prompt (for future rendering)"><p className="text-xs text-muted-foreground">{assets.music_prompt}</p></Asset>
                    <Asset icon={Music2} label="Instrumental Prompt"><p className="text-xs text-muted-foreground">{assets.instrumental_prompt}</p></Asset>
                  </div>
                </div>
              )}

              {!assets && status !== "manufacturing" && (
                <div className="bg-card border rounded-2xl p-12 text-center text-muted-foreground">
                  <p>No memory assets yet. Click <b>Manufacture Memory Assets™</b> to engineer them.</p>
                </div>
              )}
            </div>
          )}

          {/* Character voices reference */}
          <div className="mt-8">
            <p className="overline text-primary mb-3">QRU Character Voices™</p>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3" data-testid="character-voices">
              {characters.map((c) => (
                <div key={c.name} className="bg-card border rounded-xl p-3">
                  <p className="text-sm font-heading font-semibold text-primary">{c.name}</p>
                  <p className="text-[11px] text-muted-foreground">{c.role}</p>
                  <div className="flex flex-wrap gap-1 mt-1.5">{c.traits.map((t) => <span key={t} className="text-[10px] px-1.5 py-0.5 rounded-full bg-muted">{t}</span>)}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
