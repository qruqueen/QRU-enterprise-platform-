import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { BookOpenCheck, Loader2, HelpCircle, ArrowRight } from "lucide-react";

const FIELD_GROUPS = [
  { title: "Purpose", fields: [["mission", "Mission Statement"], ["purpose", "Purpose"], ["why_exists", "Why This Department Exists"]] },
  { title: "Scope", fields: [["problems_solved", "Problems It Solves"], ["responsibilities", "Responsibilities"], ["daily_activities", "Daily Activities"]] },
  { title: "Flow", fields: [["inputs", "Inputs"], ["outputs", "Outputs"], ["workflow", "Typical Workflow"], ["use_cases", "Example Use Cases"]] },
  { title: "People & Success", fields: [["ai_agents", "AI Agents Assigned"], ["people", "People Responsible"], ["related", "Related Departments"], ["kpis", "Enterprise KPIs"], ["treasure_standard", "Treasure Standard™ Requirements"], ["future", "Future Expansion Opportunities"]] },
];

function Field({ label, value }) {
  if (!value) return null;
  return (
    <div className="mb-3">
      <p className="text-[11px] font-semibold tracking-wide text-gold uppercase mb-1">{label}</p>
      {Array.isArray(value) ? (
        <ul className="list-disc pl-4 space-y-0.5 text-sm text-foreground/80">
          {value.map((v, i) => <li key={i}>{v}</li>)}
        </ul>
      ) : (
        <p className="text-sm text-foreground/80">{value}</p>
      )}
    </div>
  );
}

export default function EnterpriseBlueprint() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(null);

  useEffect(() => {
    api.get("/departments").then(({ data }) => setData(data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="w-4 h-4 animate-spin" /> Loading Enterprise Blueprint…</div>;
  if (!data) return <div className="p-8 text-sm text-muted-foreground">Unable to load the Enterprise Blueprint.</div>;

  return (
    <div className="space-y-8" data-testid="blueprint-page">
      <div>
        <h1 className="font-heading text-3xl font-bold text-navy flex items-center gap-2">
          <BookOpenCheck className="w-7 h-7 text-gold" /> QRU Enterprise Blueprint™
        </h1>
        <p className="text-sm text-muted-foreground mt-1 max-w-3xl">
          The canonical Operations Manual. Every department answers ONE clear Primary Question — the
          <span className="font-semibold text-navy"> One Question Test™</span>. If a department cannot state its question clearly, it is not yet defined.
        </p>
      </div>

      <div className="rounded-md border border-gold/40 bg-gold/5 p-4 flex items-start gap-3" data-testid="one-question-rule">
        <HelpCircle className="w-5 h-5 text-gold shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold text-navy text-sm">{data.one_question_rule.name}</p>
          <p className="text-sm text-foreground/70">{data.one_question_rule.rule}</p>
        </div>
      </div>

      {data.sections.map((section) => {
        const depts = data.departments.filter((d) => d.section === section);
        if (!depts.length) return null;
        return (
          <div key={section}>
            <p className="overline text-muted-foreground mb-3 text-xs font-semibold tracking-widest uppercase">{section}</p>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {depts.map((d) => (
                <button
                  key={d.key}
                  data-testid={`dept-card-${d.key}`}
                  onClick={() => setOpen(d)}
                  className="text-left rounded-md border border-border bg-card p-4 hover:border-gold hover:shadow-md transition-all group"
                >
                  <p className="font-heading font-semibold text-navy text-[15px]">{d.name}</p>
                  <div className="mt-2 flex items-start gap-1.5">
                    <HelpCircle className="w-3.5 h-3.5 text-gold shrink-0 mt-0.5" />
                    <p className="text-sm italic text-foreground/70">"{d.question}"</p>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2 line-clamp-2">{d.mission}</p>
                  <span className="mt-3 inline-flex items-center gap-1 text-xs text-primary font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                    View full profile <ArrowRight className="w-3 h-3" />
                  </span>
                </button>
              ))}
            </div>
          </div>
        );
      })}

      <Dialog open={!!open} onOpenChange={(v) => !v && setOpen(null)}>
        <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto" data-testid="dept-profile-dialog">
          {open && (
            <>
              <DialogHeader>
                <p className="overline text-gold text-[10px] font-semibold tracking-widest uppercase">{open.section} · Department Profile</p>
                <DialogTitle className="font-heading text-2xl text-navy">{open.name}</DialogTitle>
                <div className="flex items-start gap-2 mt-1 rounded-sm bg-navy/5 p-2.5">
                  <HelpCircle className="w-4 h-4 text-gold shrink-0 mt-0.5" />
                  <p className="text-sm"><span className="font-semibold text-navy">Primary Question:</span> <span className="italic">"{open.question}"</span></p>
                </div>
              </DialogHeader>
              <div className="grid sm:grid-cols-2 gap-x-8 mt-2">
                {FIELD_GROUPS.map((g, gi) => (
                  <div key={gi}>
                    {g.fields.map(([key, label]) => <Field key={key} label={label} value={open[key]} />)}
                  </div>
                ))}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
