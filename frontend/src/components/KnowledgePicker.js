import { useEffect, useMemo, useState } from "react";
import api from "@/lib/api";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { BookOpen, Search, CheckCircle2, Clock, Boxes, ChevronRight } from "lucide-react";

// QRU Founder Experience Principle™ — Never ask the founder to remember what the Factory already knows.
// The founder browses/searches Knowledge by TOPIC. Internal record numbers/IDs are never shown.
export function KnowledgePicker({ value, onSelect, verifiedOnly = false, autoSelect = false, testid = "knowledge-picker", label = "Browse Verified Knowledge" }) {
  const [open, setOpen] = useState(false);
  const [krs, setKrs] = useState([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let active = true;
    setLoading(true);
    api.get("/media-studio/knowledge-manufacturing")
      .then((r) => {
        if (!active) return;
        const list = r.data.knowledge_records || [];
        setKrs(list);
        const match = value ? list.find((k) => k.id === value) : null;
        if (match) {
          onSelect(match);
        } else if (autoSelect && !value) {
          const first = list.find((k) => k.verified_external) || list[0];
          if (first) onSelect(first);
        }
      })
      .catch(() => {})
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selected = useMemo(() => krs.find((k) => k.id === value) || (value && value.id ? value : null), [krs, value]);

  const filtered = useMemo(() => {
    let list = krs;
    if (verifiedOnly) list = list.filter((k) => k.verified_external);
    const s = q.trim().toLowerCase();
    if (s) list = list.filter((k) => (k.topic || "").toLowerCase().includes(s));
    return [...list].sort((a, b) => (b.verified_external ? 1 : 0) - (a.verified_external ? 1 : 0));
  }, [krs, q, verifiedOnly]);

  const pick = (k) => { onSelect(k); setOpen(false); };

  return (
    <>
      <button type="button" onClick={() => setOpen(true)} data-testid={`${testid}-trigger`}
        className="w-full text-left border border-navy/15 rounded-md px-3 py-2.5 hover:border-royal transition-colors flex items-center justify-between gap-2 bg-white">
        <span className="flex items-center gap-2 min-w-0">
          <BookOpen className="w-4 h-4 text-royal shrink-0" />
          {selected ? (
            <span className="min-w-0">
              <span className="block text-[12px] font-bold text-navy truncate">{selected.topic}</span>
              <span className="block text-[9px] text-emerald-700 font-semibold">
                {selected.verified_external ? "Verified Knowledge — content inherited automatically" : "Internal draft — stays internal until verified"}
              </span>
            </span>
          ) : (
            <span className="text-[12px] text-muted-foreground">{label}…</span>
          )}
        </span>
        <ChevronRight className="w-4 h-4 text-muted-foreground shrink-0" />
      </button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-lg" data-testid={`${testid}-dialog`}>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-navy">
              <BookOpen className="w-5 h-5 text-royal" /> Browse Verified Knowledge
            </DialogTitle>
            <DialogDescription className="text-xs">Search Verified Knowledge by topic. The Factory inherits its verified content automatically.</DialogDescription>
          </DialogHeader>
          <div className="relative">
            <Search className="w-4 h-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
            <input autoFocus data-testid={`${testid}-search`} value={q} onChange={(e) => setQ(e.target.value)}
              placeholder="Search by topic — e.g. Compound Interest, Photosynthesis…"
              className="w-full border border-navy/15 rounded-md pl-9 pr-3 py-2.5 text-sm focus:border-royal outline-none" />
          </div>
          <p className="text-[10px] text-muted-foreground -mt-1">Pick a topic. The Factory inherits its verified content, examples, definitions and assessment automatically — you never re-enter what is already understood.</p>
          <div className="max-h-[380px] overflow-y-auto space-y-1.5 pr-1">
            {loading ? (
              <p className="text-sm text-muted-foreground py-8 text-center">Loading Knowledge…</p>
            ) : filtered.length === 0 ? (
              <p className="text-sm text-muted-foreground py-8 text-center" data-testid={`${testid}-empty`}>No matching Knowledge. Try another topic.</p>
            ) : filtered.map((k) => (
              <button key={k.id} type="button" onClick={() => pick(k)} data-testid={`${testid}-item-${k.id}`}
                className={`w-full text-left border rounded-md p-3 transition-colors flex items-center justify-between gap-3 ${value === k.id ? "border-royal bg-royal/[0.04]" : "border-navy/10 hover:border-royal/60"}`}>
                <span className="min-w-0">
                  <span className="block text-[13px] font-bold text-navy truncate">{k.topic}</span>
                  <span className="flex items-center gap-1.5 text-[10px] text-muted-foreground mt-0.5">
                    <Boxes className="w-3 h-3" /> {k.asset_count} product{k.asset_count === 1 ? "" : "s"} manufactured
                  </span>
                </span>
                {k.verified_external ? (
                  <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-700 shrink-0"><CheckCircle2 className="w-3.5 h-3.5" /> Verified</span>
                ) : (
                  <span className="flex items-center gap-1 text-[10px] font-bold text-amber-600 shrink-0"><Clock className="w-3.5 h-3.5" /> Draft</span>
                )}
              </button>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
