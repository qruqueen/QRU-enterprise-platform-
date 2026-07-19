import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Landmark, ShieldCheck, GraduationCap, ScrollText, Lock, Loader2 } from "lucide-react";
import { UKRCompliance } from "@/components/UKRCompliance";

const ICONS = { constitution: ScrollText, qbos: ShieldCheck, qeds: GraduationCap };

export default function GovernanceCenter() {
  const [docs, setDocs] = useState([]);
  const [active, setActive] = useState("constitution");
  const [content, setContent] = useState({});
  const [loading, setLoading] = useState(true);

  const endpoints = {
    constitution: "/governance/constitution",
    qbos: "/qbos/constitution",
    qeds: "/qeds/constitution",
  };

  useEffect(() => {
    api.get("/governance/overview").then(({ data }) => setDocs(data.documents)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (content[active]) return;
    api.get(endpoints[active]).then(({ data }) => setContent((c) => ({ ...c, [active]: data }))).catch(() => {});
  }, [active]);

  if (loading) return <div className="p-8 flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="w-4 h-4 animate-spin" /> Loading Governance Center…</div>;

  const doc = content[active];
  const body = doc?.constitution || {};

  return (
    <div className="space-y-6" data-testid="governance-page">
      <div>
        <h1 className="font-heading text-3xl font-bold text-navy flex items-center gap-2">
          <Landmark className="w-7 h-7 text-gold" /> QRU Governance Center™
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Version-controlled, read-only constitutions governing every product, workflow and AI agent.
        </p>
      </div>

      <UKRCompliance />

      <div className="flex flex-wrap gap-2" data-testid="governance-tabs">
        {docs.map((d) => {
          const Icon = ICONS[d.key] || ScrollText;
          return (
            <button key={d.key} data-testid={`gov-tab-${d.key}`} onClick={() => setActive(d.key)}
              className={`flex items-center gap-2 px-3 py-2 rounded-sm text-sm font-semibold border ${active === d.key ? "bg-navy text-white border-navy" : "bg-card text-navy hover:bg-muted"}`}>
              <Icon className="w-4 h-4" /> {d.name} <span className="text-xs opacity-70">v{d.version}</span>
            </button>
          );
        })}
      </div>

      <div className="bg-card border rounded-sm p-6" data-testid="governance-content">
        {!doc && <div className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="w-4 h-4 animate-spin" /> Loading…</div>}
        {doc && (
          <>
            <div className="flex items-center gap-2 mb-1">
              <h2 className="font-heading text-xl font-bold text-navy">{body.title}</h2>
              <span className="flex items-center gap-1 text-[11px] text-muted-foreground border rounded-full px-2 py-0.5"><Lock className="w-3 h-3" /> Read-only · v{body.version}</span>
            </div>
            {body.effective_date && <p className="text-xs text-muted-foreground mb-4">Effective {body.effective_date} · Ratified by Founder & CEO</p>}
            {(body.preamble || body.purpose || body.philosophy) && (
              <p className="text-sm text-navy/90 mb-4 leading-relaxed">{body.preamble || body.purpose || body.philosophy}</p>
            )}

            {/* Constitution articles */}
            {body.articles && (
              <div className="space-y-3">
                {body.articles.map((a) => (
                  <div key={a.article} className="border-l-2 border-gold/60 pl-3">
                    <p className="text-sm font-semibold text-navy">Article {a.article} — {a.title}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{a.text}</p>
                  </div>
                ))}
              </div>
            )}

            {/* QBOS / QEDS structured sections */}
            {!body.articles && (
              <div className="grid sm:grid-cols-2 gap-3">
                {Object.entries(body).filter(([k, v]) =>
                  !["version", "title", "effective_date", "preamble", "purpose", "philosophy"].includes(k) &&
                  (typeof v === "string" || Array.isArray(v))).map(([k, v]) => (
                  <div key={k} className="border rounded-sm p-3">
                    <p className="text-xs font-semibold text-navy uppercase tracking-wide">{k.replace(/_/g, " ")}</p>
                    {Array.isArray(v)
                      ? <p className="text-xs text-muted-foreground mt-1">{v.join(" · ")}</p>
                      : <p className="text-xs text-muted-foreground mt-1">{v}</p>}
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
