import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge } from "@/components/qru";
import { toast } from "sonner";
import { Loader2, Image as ImageIcon, Sparkles, ShieldCheck, CheckCircle2, RotateCcw, Ban, Award, Wand2, Link as LinkIcon, Store, BookUp, Headphones } from "lucide-react";

const BACKEND = process.env.REACT_APP_BACKEND_URL || "";

const STATE_TONE = {
  DRAFT_CONCEPT: "slate", UNDER_REVIEW: "blue", REVISION_REQUIRED: "amber",
  APPROVED_DESIGN: "emerald", GOLD_MASTER: "gold", RETIRED_SUPERSEDED: "rose",
};
const NEXT_ACTIONS = [
  { state: "UNDER_REVIEW", label: "Send to Review", icon: ShieldCheck },
  { state: "REVISION_REQUIRED", label: "Request Revision", icon: RotateCcw },
  { state: "APPROVED_DESIGN", label: "Approve Design", icon: CheckCircle2 },
  { state: "GOLD_MASTER", label: "Certify Gold Master", icon: Award },
  { state: "RETIRED_SUPERSEDED", label: "Retire", icon: Ban },
];

export default function CoverStudio() {
  const [form, setForm] = useState({
    title: "The Science of Understanding",
    subtitle: "What We Keep Mistaking for Understanding — and What It Actually Is",
    series: "QRU Foundations", edition: "Consumer Edition", trim: "kdp_ebook",
    concept_notes: "A luminous human head profile made of interlocking gears becoming clear glass — real comprehension emerging from mechanism",
    concepts: 2, mode: "ai",
  });
  const [busy, setBusy] = useState(false);
  const [covers, setCovers] = useState([]);
  const [states, setStates] = useState([]);
  const [products, setProducts] = useState([]);
  const [attachFor, setAttachFor] = useState(null);
  const [selProduct, setSelProduct] = useState("");
  const [attaching, setAttaching] = useState(false);
  const [attachResult, setAttachResult] = useState({});
  const [pubBusy, setPubBusy] = useState(null);
  const [kdpResult, setKdpResult] = useState({});
  const [audioResult, setAudioResult] = useState({});
  const [storeDone, setStoreDone] = useState({});
  const [voice, setVoice] = useState("onyx");

  const load = () => api.get("/publishing/covers").then((r) => { setCovers(r.data.covers); setStates(r.data.states); }).catch(() => {});
  const loadProducts = () => api.get("/publishing/attachable-products").then((r) => setProducts(r.data.products || [])).catch(() => {});
  useEffect(() => { load(); loadProducts(); }, []);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const attachCover = async (cid) => {
    if (!selProduct) return toast.error("Choose a product to attach the cover to.");
    setAttaching(true);
    try {
      const { data } = await api.post(`/publishing/cover/${cid}/attach`, { product_id: selProduct });
      setAttachResult((r) => ({ ...r, [cid]: data }));
      toast.success(data.note || "Cover attached and deliverable re-rendered.");
      setAttachFor(null); setSelProduct(""); loadProducts();
    } catch (e) { toast.error(e.response?.data?.detail || "Attach failed."); }
    finally { setAttaching(false); }
  };

  const publishStore = async (pid) => {
    setPubBusy(`store-${pid}`);
    try {
      const { data } = await api.post(`/publishing/product/${pid}/publish-store`);
      if (data.ok) { toast.success(data.message); setStoreDone((s) => ({ ...s, [pid]: true })); }
      else toast.warning(data.message);
    } catch (e) { toast.error(e.response?.data?.detail || "Publish failed."); }
    finally { setPubBusy(null); }
  };

  const exportKdp = async (cid, pid) => {
    setPubBusy(`kdp-${pid}`);
    try {
      const { data } = await api.post(`/publishing/product/${pid}/kdp-package`);
      if (data.ok) { setKdpResult((r) => ({ ...r, [cid]: data })); toast.success(data.message); }
      else toast.warning(data.message);
    } catch (e) { toast.error(e.response?.data?.detail || "KDP export failed."); }
    finally { setPubBusy(null); }
  };

  const makeAudiobook = async (cid, pid) => {
    setPubBusy(`audio-${pid}`);
    setAudioResult((r) => ({ ...r, [cid]: { status: "RENDERING" } }));
    try {
      const { data } = await api.post(`/publishing/product/${pid}/audiobook`, { voice });
      if (!data.ok) { toast.warning(data.message); setAudioResult((r) => ({ ...r, [cid]: null })); setPubBusy(null); return; }
      toast.info(data.message);
      const started = Date.now();
      const poll = setInterval(async () => {
        if (Date.now() - started > 8 * 60 * 1000) {
          clearInterval(poll); setPubBusy(null);
          setAudioResult((r) => ({ ...r, [cid]: null }));
          toast.error("Audiobook is taking longer than expected — please try again.");
          return;
        }
        try {
          const { data: st } = await api.get(`/publishing/product/${pid}/audiobook-status`);
          if (st.status === "READY") {
            clearInterval(poll); setPubBusy(null);
            setAudioResult((r) => ({ ...r, [cid]: { status: "READY", download_url: st.url, audiobook: st } }));
            toast.success("Audiobook edition is ready.");
          } else if (st.status === "FAILED") {
            clearInterval(poll); setPubBusy(null);
            setAudioResult((r) => ({ ...r, [cid]: null }));
            toast.error(st.error || "Audiobook narration failed.");
          }
        } catch (_) { /* keep polling through transient 502s */ }
      }, 5000);
    } catch (e) { toast.error(e.response?.data?.detail || "Audiobook failed."); setAudioResult((r) => ({ ...r, [cid]: null })); setPubBusy(null); }
  };

  const generate = async () => {
    if (!form.title.trim()) return toast.error("Enter a title.");
    setBusy(true);
    try {
      const { data } = await api.post("/publishing/cover/generate", form);
      if (data.ok) toast.success(`${data.concepts.length} draft concept(s) generated. Human approval required.`);
      else toast.error(data.note || "Generation unavailable — try spec-only or upload a manual asset.");
      load();
    } catch (e) { toast.error(e.response?.data?.detail || "Cover generation failed."); }
    finally { setBusy(false); }
  };

  const transition = async (cid, state) => {
    try { await api.post(`/publishing/cover/${cid}/state`, { state }); toast.success(`State → ${state.replace(/_/g, " ")}`); load(); }
    catch (e) { toast.error(e.response?.data?.detail || "State change blocked."); }
  };

  return (
    <div data-testid="cover-studio-page">
      <PageHeader
        overline="QRU Cover & Visual Identity Standard™ · QRU-CON-0002"
        title="Cover Studio"
        description="A governed cover-production environment — not text over a background. Generate original concepts in the QRU design family, then move each through Draft → Review → Approved → Gold Master with full provenance. AI is a governed tool; every cover requires human approval."
        actions={<VerifiedBadge label="Provenance tracked · Human approval always" testid="cover-badge" />}
      />

      <div className="grid lg:grid-cols-3 gap-5">
        {/* Brief */}
        <Panel title="Cover Brief" icon={Sparkles} accent="royal" testid="cover-brief">
          <div className="space-y-2.5">
            {[["title", "Title"], ["subtitle", "Subtitle"], ["series", "Series"], ["edition", "Edition"]].map(([k, label]) => (
              <div key={k}>
                <label className="text-[10px] font-bold uppercase tracking-wide text-navy">{label}</label>
                <input data-testid={`cover-${k}`} value={form[k]} onChange={(e) => set(k, e.target.value)} className="w-full mt-0.5 border rounded-sm p-2 text-sm" />
              </div>
            ))}
            <div>
              <label className="text-[10px] font-bold uppercase tracking-wide text-navy">Trim / format</label>
              <select data-testid="cover-trim" value={form.trim} onChange={(e) => set("trim", e.target.value)} className="w-full mt-0.5 border rounded-sm p-2 text-sm">
                <option value="kdp_ebook">eBook / KDP (2:3)</option>
                <option value="us_trade_6x9">US Trade 6×9</option>
                <option value="square_1x1">Square (podcast/social)</option>
                <option value="video_16x9">Video thumbnail 16:9</option>
                <option value="reel_9x16">Reel 9:16</option>
              </select>
            </div>
            <div>
              <label className="text-[10px] font-bold uppercase tracking-wide text-navy">Visual concept (no manuscript)</label>
              <textarea data-testid="cover-notes" value={form.concept_notes} onChange={(e) => set("concept_notes", e.target.value)} rows={3} className="w-full mt-0.5 border rounded-sm p-2 text-sm" />
            </div>
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <label className="text-[10px] font-bold uppercase tracking-wide text-navy">Concepts</label>
                <select data-testid="cover-count" value={form.concepts} onChange={(e) => set("concepts", Number(e.target.value))} className="w-full mt-0.5 border rounded-sm p-2 text-sm">
                  {[1, 2, 3].map((n) => <option key={n} value={n}>{n}</option>)}
                </select>
              </div>
              <div className="flex-1">
                <label className="text-[10px] font-bold uppercase tracking-wide text-navy">Mode</label>
                <select data-testid="cover-mode" value={form.mode} onChange={(e) => set("mode", e.target.value)} className="w-full mt-0.5 border rounded-sm p-2 text-sm">
                  <option value="ai">AI concepts (governed)</option>
                  <option value="spec_only">Spec-only / manual asset</option>
                </select>
              </div>
            </div>
            <button onClick={generate} disabled={busy} data-testid="cover-generate"
              className="w-full inline-flex items-center justify-center gap-2 bg-navy text-white px-4 py-2.5 rounded-sm font-bold disabled:opacity-50 hover:bg-navy/90 transition-colors">
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />} {busy ? "Manufacturing concepts…" : "Generate Concepts"}
            </button>
            <p className="text-[10px] text-muted-foreground">Draft concepts require human approval before becoming an Approved Design or Gold Master. Provider outage falls back to spec-only — publishing is never blocked.</p>
          </div>
        </Panel>

        {/* Gallery */}
        <div className="lg:col-span-2">
          <Panel title="Cover Concepts & Production States" icon={ImageIcon} accent="gold" testid="cover-gallery">
            {covers.length === 0 ? (
              <p className="text-sm text-muted-foreground py-8 text-center">No covers yet. Generate your first governed concept.</p>
            ) : (
              <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-3">
                {covers.map((c) => (
                  <div key={c.id} className="border rounded-md overflow-hidden border-navy/10" data-testid={`cover-item-${c.id}`}>
                    {c.file_url ? <img src={`${BACKEND}${c.file_url}`} alt={c.title} className="w-full h-56 object-cover bg-navy/5" />
                      : <div className="w-full h-56 grid place-items-center bg-navy/[0.04] text-[11px] text-muted-foreground text-center px-3">Spec-only concept<br />(attach a manual/licensed asset)</div>}
                    <div className="p-2.5">
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <p className="text-[11px] font-bold text-navy truncate">{c.title}</p>
                        <StatusChip status={c.state.replace(/_/g, " ")} tone={STATE_TONE[c.state] || "slate"} />
                      </div>
                      <p className="text-[9px] text-muted-foreground">{c.provenance?.provider || "manual"} · {c.provenance?.model || "—"} · v{c.provenance?.version || "—"}</p>
                      <div className="flex flex-wrap gap-1 mt-2">
                        {NEXT_ACTIONS.filter((a) => a.state !== c.state).map((a) => {
                          const Ic = a.icon;
                          return (
                            <button key={a.state} onClick={() => transition(c.id, a.state)} data-testid={`cover-state-${c.id}-${a.state}`}
                              className="text-[9px] inline-flex items-center gap-1 px-1.5 py-0.5 rounded border border-navy/15 text-navy hover:border-royal hover:text-royal transition-colors">
                              <Ic className="w-2.5 h-2.5" /> {a.label}
                            </button>
                          );
                        })}
                      </div>

                      {/* Attach to Product — only governed (APPROVED/GOLD) covers can bind to a deliverable */}
                      {(c.state === "APPROVED_DESIGN" || c.state === "GOLD_MASTER") && c.file_url && (
                        <div className="mt-2 pt-2 border-t border-navy/10" data-testid={`cover-attach-block-${c.id}`}>
                          {attachFor === c.id ? (
                            <div className="space-y-1.5">
                              <select data-testid={`cover-attach-select-${c.id}`} value={selProduct} onChange={(e) => setSelProduct(e.target.value)}
                                className="w-full border rounded-sm p-1.5 text-[11px]">
                                <option value="">Select a product…</option>
                                {products.map((p) => <option key={p.id} value={p.id}>{p.title || p.product_code || p.id} · {p.product_type}</option>)}
                              </select>
                              <div className="flex gap-1.5">
                                <button onClick={() => attachCover(c.id)} disabled={attaching} data-testid={`cover-attach-confirm-${c.id}`}
                                  className="flex-1 inline-flex items-center justify-center gap-1 bg-navy text-white text-[10px] px-2 py-1.5 rounded-sm font-bold disabled:opacity-50">
                                  {attaching ? <Loader2 className="w-3 h-3 animate-spin" /> : <LinkIcon className="w-3 h-3" />} Attach & Render
                                </button>
                                <button onClick={() => { setAttachFor(null); setSelProduct(""); }} className="text-[10px] px-2 py-1.5 rounded-sm border border-navy/15 text-navy">Cancel</button>
                              </div>
                            </div>
                          ) : (
                            <button onClick={() => { setAttachFor(c.id); setSelProduct(""); }} data-testid={`cover-attach-${c.id}`}
                              className="w-full inline-flex items-center justify-center gap-1 text-[10px] px-2 py-1.5 rounded-sm border border-emerald-300 text-emerald-800 bg-emerald-50 hover:bg-emerald-100 font-bold transition-colors">
                              <LinkIcon className="w-3 h-3" /> Attach to Product
                            </button>
                          )}
                          {attachResult[c.id] && (
                            <div className="mt-1.5 space-y-1.5" data-testid={`cover-attach-result-${c.id}`}>
                              <div className="text-[9px] text-emerald-800">
                                ✓ Attached to <b>{attachResult[c.id].product_title}</b>.
                                {attachResult[c.id].download_url && (
                                  <a href={`${BACKEND}${attachResult[c.id].download_url}`} target="_blank" rel="noreferrer" className="text-royal underline ml-1" data-testid={`cover-attach-download-${c.id}`}>Download deliverable →</a>
                                )}
                              </div>
                              <div className="flex flex-wrap gap-1.5">
                                <button onClick={() => publishStore(attachResult[c.id].product_id)} disabled={pubBusy === `store-${attachResult[c.id].product_id}`}
                                  data-testid={`cover-publish-store-${c.id}`}
                                  className="text-[10px] px-2 py-1 rounded-sm border border-emerald-300 bg-emerald-50 text-emerald-800 font-bold inline-flex items-center gap-1 disabled:opacity-50 hover:bg-emerald-100">
                                  {pubBusy === `store-${attachResult[c.id].product_id}` ? <Loader2 className="w-3 h-3 animate-spin" /> : <Store className="w-3 h-3" />} Add to QRU Store
                                </button>
                                {storeDone[attachResult[c.id].product_id] && (
                                  <a href="/store" data-testid={`cover-store-link-${c.id}`} className="text-[10px] px-2 py-1 text-emerald-700 font-bold underline inline-flex items-center">✓ Live — View in Store →</a>
                                )}
                                <button onClick={() => exportKdp(c.id, attachResult[c.id].product_id)} disabled={pubBusy === `kdp-${attachResult[c.id].product_id}`}
                                  data-testid={`cover-export-kdp-${c.id}`}
                                  className="text-[10px] px-2 py-1 rounded-sm border border-navy/20 bg-white text-navy font-bold inline-flex items-center gap-1 disabled:opacity-50 hover:border-royal">
                                  {pubBusy === `kdp-${attachResult[c.id].product_id}` ? <Loader2 className="w-3 h-3 animate-spin" /> : <BookUp className="w-3 h-3" />} KDP-Ready Export
                                </button>
                                <span className="inline-flex items-center gap-1">
                                  <select value={voice} onChange={(e) => setVoice(e.target.value)} data-testid={`cover-audio-voice-${c.id}`}
                                    className="text-[10px] border border-navy/20 rounded-sm px-1 py-1 text-navy bg-white">
                                    {["onyx", "sage", "nova", "shimmer", "fable"].map((v) => <option key={v} value={v}>{v}</option>)}
                                  </select>
                                  <button onClick={() => makeAudiobook(c.id, attachResult[c.id].product_id)} disabled={pubBusy === `audio-${attachResult[c.id].product_id}`}
                                    data-testid={`cover-audiobook-${c.id}`}
                                    className="text-[10px] px-2 py-1 rounded-sm border border-royal/40 bg-royal/[0.06] text-royal font-bold inline-flex items-center gap-1 disabled:opacity-50 hover:bg-royal/10">
                                    {pubBusy === `audio-${attachResult[c.id].product_id}` ? <Loader2 className="w-3 h-3 animate-spin" /> : <Headphones className="w-3 h-3" />} Create Audiobook
                                  </button>
                                </span>
                              </div>
                              {kdpResult[c.id] && (
                                <div className="text-[9px] text-navy/80 border border-navy/10 rounded-sm p-1.5" data-testid={`cover-kdp-result-${c.id}`}>
                                  <a href={`${BACKEND}${kdpResult[c.id].download_url}`} target="_blank" rel="noreferrer" className="text-royal underline font-bold" data-testid={`cover-kdp-download-${c.id}`}>Download KDP package (.zip) →</a>
                                  <span className="block mt-0.5">Includes: {kdpResult[c.id].contents.join(", ")}. Upload once at kdp.amazon.com — QRU never fakes an "on Amazon" state.</span>
                                </div>
                              )}
                              {audioResult[c.id] && audioResult[c.id].status === "RENDERING" && (
                                <div className="text-[9px] text-royal border border-royal/20 rounded-sm p-1.5 inline-flex items-center gap-1.5" data-testid={`cover-audiobook-rendering-${c.id}`}>
                                  <Loader2 className="w-3 h-3 animate-spin" /> Narrating audiobook in the background…
                                </div>
                              )}
                              {audioResult[c.id] && audioResult[c.id].status === "READY" && (
                                <div className="text-[9px] text-navy/80 border border-royal/20 rounded-sm p-1.5" data-testid={`cover-audiobook-result-${c.id}`}>
                                  <a href={`${BACKEND}${audioResult[c.id].download_url}`} target="_blank" rel="noreferrer" className="text-royal underline font-bold" data-testid={`cover-audiobook-download-${c.id}`}>▶ Listen / download audiobook (.mp3) →</a>
                                  <span className="block mt-0.5">Voice: {audioResult[c.id].audiobook.voice} · ~{Math.max(1, Math.round((audioResult[c.id].audiobook.est_seconds || 0) / 60))} min · narrated from the {audioResult[c.id].audiobook.narrated_from === "book" ? "book content" : "verified Knowledge Record"}.</span>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}
