import { useEffect, useState } from "react";
import api from "@/lib/api";
import { toast } from "sonner";
import { HardDriveDownload, Loader2, Copy, Check, Github, Database, KeyRound, Server, LifeBuoy, ShieldCheck, Globe, Boxes } from "lucide-react";

function CopyBtn({ text }) {
  const [done, setDone] = useState(false);
  const copy = async () => {
    try { await navigator.clipboard.writeText(text); setDone(true); toast.success("Copied"); setTimeout(() => setDone(false), 1500); }
    catch { toast.error("Copy failed"); }
  };
  return (
    <button data-testid="copy-btn" onClick={copy} className="shrink-0 text-xs px-2 py-1 rounded-sm border border-border hover:border-primary flex items-center gap-1">
      {done ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />} {done ? "Copied" : "Copy"}
    </button>
  );
}

function Cmd({ label, cmd }) {
  return (
    <div className="rounded-sm border border-border bg-muted/40 p-2.5">
      {label && <p className="text-[11px] text-muted-foreground mb-1">{label}</p>}
      <div className="flex items-center gap-2">
        <code className="text-xs text-navy font-mono break-all flex-1">{cmd}</code>
        <CopyBtn text={cmd} />
      </div>
    </div>
  );
}

function Section({ icon: Icon, title, children }) {
  return (
    <div className="bg-card border rounded-md p-5">
      <p className="overline text-primary mb-3 flex items-center gap-2"><Icon className="w-4 h-4" /> {title}</p>
      {children}
    </div>
  );
}

export default function PortabilityCenter() {
  const [d, setD] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { api.get("/portability/overview").then(({ data }) => setD(data)).catch(() => {}).finally(() => setLoading(false)); }, []);

  if (loading) return <div className="p-8 flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="w-4 h-4 animate-spin" /> Loading Portability Center…</div>;
  if (!d) return <div className="p-8 text-sm text-muted-foreground">Unable to load Portability Center.</div>;

  return (
    <div className="space-y-6" data-testid="portability-page">
      <div>
        <h1 className="font-heading text-3xl font-bold text-navy flex items-center gap-2">
          <HardDriveDownload className="w-7 h-7 text-gold" /> QRU Portability Center™
        </h1>
        <p className="text-sm text-muted-foreground mt-1 max-w-3xl">
          Everything required to export, back up, and redeploy QRU Factory. This page exists so QRU can always be recovered.
          <span className="font-semibold text-navy"> {d.version.app} · v{d.version.release} · {d.version.stack}</span>
        </p>
      </div>

      <div className="grid lg:grid-cols-2 gap-5">
        <Section icon={Github} title="GitHub Repository">
          <p className="text-sm text-foreground/80">{d.github.status}</p>
          <ul className="list-disc pl-4 mt-2 text-sm text-foreground/70 space-y-0.5">
            {d.github.includes.map((x) => <li key={x}>{x}</li>)}
          </ul>
          <p className="text-xs text-muted-foreground mt-2">Last export date: {d.github.last_export_date}</p>
        </Section>

        <Section icon={Globe} title="Domain Information">
          <Cmd label="Backend URL (REACT_APP_BACKEND_URL)" cmd={d.domain.backend_url} />
          <p className="text-xs text-muted-foreground mt-2">{d.domain.note}</p>
        </Section>

        <Section icon={KeyRound} title="Environment Variables & API Keys (no secrets shown)">
          <div className="space-y-1.5">
            {d.environment_variables.map((e) => (
              <div key={e.key} className="flex items-center justify-between text-sm border-b border-border/60 py-1">
                <div><span className="font-mono text-navy">{e.key}</span><span className="text-xs text-muted-foreground ml-2">{e.purpose}</span></div>
                <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${e.configured ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-red-50 text-red-700 border border-red-200"}`}>{e.masked}</span>
              </div>
            ))}
          </div>
        </Section>

        <Section icon={Server} title="LLM Provider Configuration">
          <p className="text-sm text-foreground/80">Provider: <span className="font-semibold text-navy">{d.llm_provider.current_provider}</span> · Model: <span className="font-mono">{d.llm_provider.current_model}</span></p>
          <p className="text-xs text-muted-foreground mt-1">{d.llm_provider.note}</p>
          <div className="flex flex-wrap gap-1.5 mt-2">
            {d.llm_provider.capabilities.map((c) => <span key={c} className="text-[10px] bg-muted px-1.5 py-0.5 rounded-sm">{c}</span>)}
          </div>
        </Section>
      </div>

      <Section icon={Database} title={`MongoDB Collections (${d.mongo_collections.count})`}>
        <p className="text-xs text-muted-foreground mb-2">{d.mongo_collections.note}</p>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-1.5">
          {d.mongo_collections.collections.map((c) => (
            <div key={c.name} className="flex items-center justify-between text-xs bg-muted/40 rounded-sm px-2 py-1">
              <span className="font-mono truncate">{c.name}</span>
              <span className="text-muted-foreground ml-1">{c.documents}</span>
            </div>
          ))}
        </div>
      </Section>

      <div className="grid lg:grid-cols-2 gap-5">
        <Section icon={ShieldCheck} title="Backup Checklist">
          <ul className="space-y-1.5">{d.backup_checklist.map((x, i) => <li key={i} className="text-sm text-foreground/80 flex gap-2"><span className="text-gold">{i + 1}.</span> {x}</li>)}</ul>
        </Section>
        <Section icon={LifeBuoy} title="Disaster Recovery Checklist">
          <ul className="space-y-1.5">{d.disaster_recovery_checklist.map((x, i) => <li key={i} className="text-sm text-foreground/80 flex gap-2"><span className="text-gold">{i + 1}.</span> {x}</li>)}</ul>
        </Section>
      </div>

      <Section icon={HardDriveDownload} title="Backup & Restore Commands">
        <div className="space-y-2">{d.command_templates.map((c, i) => <Cmd key={i} label={c.label} cmd={c.cmd} />)}</div>
      </Section>

      <Section icon={Server} title="Restore Procedure">
        <div className="space-y-2">{d.restore_procedure.map((s, i) => (
          <div key={i}><p className="text-sm font-medium text-navy mb-1">{s.step}</p><Cmd cmd={s.cmd} /></div>
        ))}</div>
      </Section>

      <div className="grid lg:grid-cols-2 gap-5">
        <Section icon={Boxes} title="Deployment Targets">
          <div className="space-y-2">{d.deployment_targets.map((t) => (
            <div key={t.target} className="text-sm"><span className="font-medium text-navy">{t.target}</span><p className="text-xs text-muted-foreground">{t.notes}</p></div>
          ))}</div>
        </Section>
        <Section icon={Server} title="Third-Party Services">
          <div className="space-y-2">{d.third_party_services.map((t) => (
            <div key={t.name} className="text-sm"><span className="font-medium text-navy">{t.name}</span> <span className="text-xs text-muted-foreground">· {t.role}</span><p className="text-xs text-foreground/70">{t.portable}</p></div>
          ))}</div>
        </Section>
      </div>
    </div>
  );
}
