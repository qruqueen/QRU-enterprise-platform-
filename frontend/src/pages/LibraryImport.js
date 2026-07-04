import { useState, useRef } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { toast } from "sonner";
import { FolderUp, Loader2, FileText, CheckCircle2, Copy, AlertTriangle, Upload, Sprout } from "lucide-react";

const STATUS = {
  new: { icon: CheckCircle2, cls: "text-emerald-600", label: "New" },
  imported: { icon: CheckCircle2, cls: "text-emerald-600", label: "Imported" },
  duplicate: { icon: Copy, cls: "text-amber-600", label: "Duplicate" },
  empty: { icon: AlertTriangle, cls: "text-red-500", label: "Empty" },
  unsupported: { icon: AlertTriangle, cls: "text-red-500", label: "Unsupported" },
  skipped: { icon: AlertTriangle, cls: "text-muted-foreground", label: "Skipped" },
};

export default function LibraryImport() {
  const fileRef = useRef();
  const [files, setFiles] = useState([]);
  const [report, setReport] = useState(null);
  const [sel, setSel] = useState({});
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);

  const pick = (e) => {
    const f = Array.from(e.target.files || []);
    setFiles(f); setReport(null); setResult(null); setSel({});
  };

  const analyze = async () => {
    if (files.length === 0) return toast.error("Choose one or more documents first");
    setBusy(true); setResult(null);
    try {
      const fd = new FormData();
      files.forEach((f) => fd.append("files", f));
      const { data } = await api.post("/library-import/analyze", fd, { headers: { "Content-Type": "multipart/form-data" } });
      setReport(data);
      const pre = {};
      data.report.forEach((r) => { if (r.status === "new") pre[r.filename] = true; });
      setSel(pre);
      toast.success(`Analyzed ${data.report.length} file(s): ${data.new_count} new, ${data.duplicate_count} duplicate`);
    } catch (e) { toast.error(e?.response?.data?.detail || "Analysis failed"); }
    finally { setBusy(false); }
  };

  const commit = async () => {
    const chosen = Object.keys(sel).filter((k) => sel[k]);
    if (chosen.length === 0) return toast.error("Select at least one new record to import");
    setBusy(true);
    try {
      const fd = new FormData();
      files.forEach((f) => fd.append("files", f));
      fd.append("selected", chosen.join("||"));
      const { data } = await api.post("/library-import/commit", fd, { headers: { "Content-Type": "multipart/form-data" } });
      setResult(data); setReport({ report: data.report, new_count: 0, duplicate_count: data.duplicate_count });
      toast.success(`Imported ${data.created_count} Knowledge Record(s)`);
    } catch (e) { toast.error(e?.response?.data?.detail || "Import failed"); }
    finally { setBusy(false); }
  };

  const newCount = report ? report.report.filter((r) => r.status === "new").length : 0;
  const selCount = Object.values(sel).filter(Boolean).length;

  return (
    <div>
      <PageHeader
        overline="Bulk Library Import™ · Knowledge-First"
        title="Import a Folder of Documents"
        description="Upload many documents at once. QRU extracts the text verbatim (no AI, no hallucination), detects duplicates, assigns Knowledge Record IDs, and files each one into the Promotion Pipeline™ for structuring."
      />

      {/* Upload zone */}
      <div className="bg-card border rounded-md p-5 mb-4" data-testid="import-upload">
        <input ref={fileRef} type="file" multiple accept=".txt,.md,.markdown,.docx,.pdf" onChange={pick} className="hidden" data-testid="import-file-input" />
        <div className="flex flex-col sm:flex-row sm:items-center gap-3">
          <button onClick={() => fileRef.current?.click()} data-testid="import-choose"
            className="inline-flex items-center gap-2 border px-4 py-2 rounded-sm hover:border-primary text-sm">
            <FolderUp className="w-4 h-4" /> Choose Documents
          </button>
          <span className="text-sm text-muted-foreground flex-1">{files.length ? `${files.length} file(s) selected` : "Supported: .txt, .md, .docx, .pdf"}</span>
          <button onClick={analyze} disabled={busy || files.length === 0} data-testid="import-analyze"
            className="inline-flex items-center gap-2 bg-navy text-white px-4 py-2 rounded-sm disabled:opacity-60 text-sm">
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />} Analyze
          </button>
        </div>
      </div>

      {/* Report */}
      {report && (
        <div className="bg-card border rounded-md p-5" data-testid="import-report">
          <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
            <p className="font-heading font-semibold text-navy">Import Report — {newCount} new · {report.report.filter((r) => r.status === "duplicate").length} duplicate</p>
            {!result && newCount > 0 && (
              <button onClick={commit} disabled={busy || selCount === 0} data-testid="import-commit"
                className="inline-flex items-center gap-2 bg-emerald-600 text-white px-4 py-2 rounded-sm disabled:opacity-60 text-sm">
                {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sprout className="w-4 h-4" />} Import Selected ({selCount})
              </button>
            )}
          </div>

          <div className="space-y-1.5">
            {report.report.map((r, i) => {
              const st = STATUS[r.status] || STATUS.skipped;
              const Icon = st.icon;
              const selectable = r.status === "new" && !result;
              return (
                <div key={i} className="flex items-start gap-2 border rounded-sm px-3 py-2 text-sm" data-testid={`import-row-${i}`}>
                  {selectable ? (
                    <input type="checkbox" checked={!!sel[r.filename]} onChange={(e) => setSel({ ...sel, [r.filename]: e.target.checked })} className="mt-1" data-testid={`import-check-${i}`} />
                  ) : <span className="w-4" />}
                  <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${st.cls}`} />
                  <div className="min-w-0 flex-1">
                    <p className="text-navy font-medium truncate">{r.title || r.filename}
                      {r.kr_code && <span className="ml-2 text-[11px] text-emerald-700">{r.kr_code}</span>}
                    </p>
                    <p className="text-[11px] text-muted-foreground truncate">{r.filename}{r.chars ? ` · ${r.chars.toLocaleString()} chars` : ""}</p>
                    {r.reason && <p className="text-[11px] text-amber-700">{r.reason}</p>}
                    {r.preview && !result && <p className="text-[11px] text-muted-foreground mt-1 line-clamp-2">{r.preview}</p>}
                  </div>
                  <span className={`text-[11px] shrink-0 ${st.cls}`}>{st.label}</span>
                </div>
              );
            })}
          </div>

          {result && (
            <div className="mt-3 p-3 bg-emerald-50 border border-emerald-200 rounded-sm text-sm text-emerald-800" data-testid="import-result">
              Imported {result.created_count} Knowledge Record(s). Open the <a href="/promotion-pipeline" className="underline font-medium">Promotion Pipeline™</a> to structure and verify them before manufacturing.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
