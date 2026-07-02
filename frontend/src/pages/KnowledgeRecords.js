import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { PageHeader, StatusBadge, EmptyState } from "@/components/shared";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { BookOpen, Plus, Search } from "lucide-react";

const CATEGORIES = ["Heart Health", "Brain Health", "Lung Health", "Metabolic Health", "Kidney Health", "Prevention & Wellness", "General", "Research"];

export function KnowledgeCreateDialog({ onCreated, trigger }) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ title: "", category: "General", verified_truth: "" });
  const [saving, setSaving] = useState(false);

  const save = async () => {
    if (!form.title || !form.verified_truth) return toast.error("Title and verified truth are required");
    setSaving(true);
    try {
      const { data } = await api.post("/knowledge-records", form);
      toast.success(`Created ${data.kr_code}`);
      setOpen(false);
      setForm({ title: "", category: "General", verified_truth: "" });
      onCreated?.(data);
    } catch (e) {
      toast.error("Failed to create record");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="rounded-md">
        <DialogHeader><DialogTitle className="font-heading">New Knowledge Record™</DialogTitle></DialogHeader>
        <div className="space-y-4 py-2">
          <div>
            <label className="text-sm font-medium">Title</label>
            <input data-testid="kr-title-input" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="mt-1 w-full px-3 py-2 rounded-sm border outline-none focus:border-primary" />
          </div>
          <div>
            <label className="text-sm font-medium">Category</label>
            <Select value={form.category} onValueChange={(v) => setForm({ ...form, category: v })}>
              <SelectTrigger data-testid="kr-category-input" className="mt-1 rounded-sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CATEGORIES.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm font-medium">Verified Truth</label>
            <textarea data-testid="kr-truth-input" rows={4} value={form.verified_truth} onChange={(e) => setForm({ ...form, verified_truth: e.target.value })}
              className="mt-1 w-full px-3 py-2 rounded-sm border outline-none focus:border-primary resize-none" />
          </div>
        </div>
        <DialogFooter>
          <button data-testid="kr-save-btn" onClick={save} disabled={saving}
            className="bg-primary text-primary-foreground px-4 py-2 rounded-sm text-sm font-medium hover:bg-primary/90 disabled:opacity-60">
            {saving ? "Saving…" : "Create Record"}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function KnowledgeRecords() {
  const [records, setRecords] = useState([]);
  const [q, setQ] = useState("");
  const [cat, setCat] = useState("");
  const navigate = useNavigate();

  const load = () => {
    const params = {};
    if (q) params.q = q;
    if (cat) params.category = cat;
    api.get("/knowledge-records", { params }).then((r) => setRecords(r.data)).catch(() => {});
  };

  useEffect(() => { load(); }, [q, cat]);

  return (
    <div>
      <PageHeader
        overline="QRU Knowledge Database™"
        title="Knowledge Records"
        description="The single source of truth. Every record is researched, verified, and translated into understanding."
        actions={
          <KnowledgeCreateDialog onCreated={load} trigger={
            <button data-testid="kr-new-btn" className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-sm text-sm font-medium hover:bg-primary/90 transition-colors">
              <Plus className="w-4 h-4" /> New Record
            </button>
          } />
        }
      />

      <div className="flex flex-col sm:flex-row gap-3 mb-5">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input data-testid="kr-search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search records…"
            className="w-full pl-9 pr-3 py-2 text-sm border rounded-sm bg-card outline-none focus:border-primary" />
        </div>
        <select data-testid="kr-filter-category" value={cat} onChange={(e) => setCat(e.target.value)}
          className="px-3 py-2 text-sm border rounded-sm bg-card outline-none focus:border-primary">
          <option value="">All categories</option>
          {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
        </select>
      </div>

      {records.length === 0 ? (
        <EmptyState icon={BookOpen} title="No knowledge records" description="Create your first record or issue a command in the console." />
      ) : (
        <div className="bg-card border rounded-md overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40 text-left">
                <th className="px-4 py-3 font-medium text-muted-foreground overline">Code</th>
                <th className="px-4 py-3 font-medium text-muted-foreground overline">Title</th>
                <th className="px-4 py-3 font-medium text-muted-foreground overline hidden md:table-cell">Category</th>
                <th className="px-4 py-3 font-medium text-muted-foreground overline">Status</th>
                <th className="px-4 py-3 font-medium text-muted-foreground overline hidden sm:table-cell">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {records.map((r) => (
                <tr key={r.id} data-testid={`kr-row-${r.id}`} onClick={() => navigate(`/knowledge/${r.id}`)}
                  className="border-b last:border-0 hover:bg-muted/40 cursor-pointer transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{r.kr_code}</td>
                  <td className="px-4 py-3 font-medium max-w-md">{r.title}</td>
                  <td className="px-4 py-3 text-muted-foreground hidden md:table-cell">{r.category}</td>
                  <td className="px-4 py-3"><StatusBadge status={r.verification_status} /></td>
                  <td className="px-4 py-3 hidden sm:table-cell">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                        <div className="h-full bg-primary" style={{ width: `${r.confidence_score}%` }} />
                      </div>
                      <span className="text-xs text-muted-foreground">{r.confidence_score}%</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
