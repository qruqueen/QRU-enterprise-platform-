import { useEffect, useState, useRef } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import {
  Upload, Loader2, Search, Download, Archive, ShieldCheck, Star, Link2, History,
  FileImage, FileText, Music, Video, Package, Sparkles,
} from "lucide-react";

const BACKEND = process.env.REACT_APP_BACKEND_URL;
const abs = (u) => (u ? (u.startsWith("http") ? u : `${BACKEND}${u}`) : null);

const SOURCE_STYLE = {
  "Protected Master": "bg-purple-50 text-purple-700 border-purple-200",
  "Founder Imported": "bg-amber-50 text-amber-700 border-amber-200",
  "Approved Production Asset": "bg-emerald-50 text-emerald-700 border-emerald-200",
  "Factory Draft": "bg-slate-50 text-slate-600 border-slate-200",
  "Superseded": "bg-orange-50 text-orange-700 border-orange-200",
  "Archived": "bg-gray-100 text-gray-500 border-gray-200",
};

function typeIcon(t) {
  if (/audio|music|narration/i.test(t)) return Music;
  if (/video/i.test(t)) return Video;
  if (/pdf|template|powerpoint/i.test(t)) return FileText;
  if (/image|cover|poster|icon|logo|shield|seal|character|png|background|diagram|infographic|graphic/i.test(t)) return FileImage;
  return Package;
}

export default function AssetVault() {
  const [meta, setMeta] = useState(null);
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ q: "", asset_type: "", source: "", approval_status: "" });
  const [showUpload, setShowUpload] = useState(false);
  const [detail, setDetail] = useState(null);

  const loadMeta = () => api.get("/vault/meta").then((r) => setMeta(r.data));
  const load = () => {
    setLoading(true);
    const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v));
    api.get("/vault/assets", { params }).then((r) => setAssets(r.data.assets)).finally(() => setLoading(false));
  };
  useEffect(() => { loadMeta(); }, []);
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [filters]);

  return (
    <div className="animate-fade-up" data-testid="asset-vault-page">
      <PageHeader overline="Creative Studio™ · Reusable Inventory" title="QRU Asset Vault™"
        description="Store, protect, and reuse approved QRU assets so the factory never regenerates or overwrites your strongest work. Founder-imported and approved assets are reused by default."
        actions={<button data-testid="vault-upload-btn" onClick={() => setShowUpload(true)}
          className="inline-flex items-center gap-2 bg-navy text-white px-4 py-2 rounded-sm text-sm font-medium hover:bg-navy/90">
          <Upload className="w-4 h-4" /> Import Asset</button>} />

      {/* Filters */}
      <div className="flex flex-wrap gap-2 mb-5">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input data-testid="vault-search" value={filters.q} onChange={(e) => setFilters({ ...filters, q: e.target.value })}
            placeholder="Search assets…" className="w-full pl-9 pr-3 py-2 text-sm border rounded-sm bg-card" />
        </div>
        <select data-testid="vault-filter-type" value={filters.asset_type} onChange={(e) => setFilters({ ...filters, asset_type: e.target.value })} className="text-sm border rounded-sm px-2 bg-card">
          <option value="">All types</option>
          {meta?.asset_types.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <select data-testid="vault-filter-source" value={filters.source} onChange={(e) => setFilters({ ...filters, source: e.target.value })} className="text-sm border rounded-sm px-2 bg-card">
          <option value="">All classifications</option>
          {meta?.sources.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select data-testid="vault-filter-status" value={filters.approval_status} onChange={(e) => setFilters({ ...filters, approval_status: e.target.value })} className="text-sm border rounded-sm px-2 bg-card">
          <option value="">All statuses</option>
          {meta?.approval_statuses.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {loading ? (
        <div className="flex justify-center py-16"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>
      ) : assets.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground" data-testid="vault-empty">
          <Archive className="w-10 h-10 mx-auto mb-3 opacity-40" />
          <p>No assets yet. Import your existing QRU covers, logos, characters, and posters to reuse them across the factory.</p>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4" data-testid="vault-grid">
          {assets.map((a) => {
            const Icon = typeIcon(a.asset_type);
            return (
              <button key={a.id} onClick={() => setDetail(a)} data-testid={`vault-card-${a.asset_code}`}
                className="text-left bg-card border rounded-xl overflow-hidden hover:shadow-md transition-shadow">
                <div className="aspect-[4/3] bg-navy/5 flex items-center justify-center overflow-hidden">
                  {a.file?.previewable && /image|png|jpg|jpeg|webp|gif|svg/i.test(a.file.ext)
                    ? <img src={abs(a.file.url)} alt={a.name} className="w-full h-full object-cover" />
                    : <Icon className="w-10 h-10 text-navy/40" />}
                </div>
                <div className="p-3">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] text-muted-foreground">{a.asset_code} · v{a.version}</span>
                    {a.source === "Protected Master" && <ShieldCheck className="w-3.5 h-3.5 text-purple-600" />}
                    {a.source === "Founder Imported" && <Star className="w-3.5 h-3.5 text-amber-500 fill-amber-500" />}
                  </div>
                  <p className="text-sm font-medium truncate mt-0.5">{a.name}</p>
                  <p className="text-xs text-muted-foreground">{a.asset_type}</p>
                  <span className={`inline-block mt-2 text-[10px] px-1.5 py-0.5 rounded-full border ${SOURCE_STYLE[a.source] || ""}`}>{a.source}</span>
                </div>
              </button>
            );
          })}
        </div>
      )}

      {showUpload && meta && <UploadDialog meta={meta} onClose={() => setShowUpload(false)} onDone={() => { setShowUpload(false); load(); }} />}
      {detail && <DetailDialog asset={detail} meta={meta} onClose={() => setDetail(null)} onChange={(a) => { setDetail(a); load(); }} />}
    </div>
  );
}

function UploadDialog({ meta, onClose, onDone }) {
  const [form, setForm] = useState({ name: "", asset_type: "Cover", source: "Founder Imported",
    approval_status: "Founder Approved", product_family: "", knowledge_record_id: "", character: "", notes: "" });
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const fileRef = useRef();

  const submit = async () => {
    if (!file || !form.name) { toast.error("Add a file and a name"); return; }
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      Object.entries(form).forEach(([k, v]) => v && fd.append(k, v));
      await api.post("/vault/upload", fd, { headers: { "Content-Type": "multipart/form-data" } });
      toast.success("Asset imported to the Vault™");
      onDone();
    } catch (e) { toast.error(e?.response?.data?.detail || "Upload failed"); }
    finally { setBusy(false); }
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent data-testid="vault-upload-dialog">
        <DialogHeader><DialogTitle className="font-heading">Founder Asset Import™</DialogTitle></DialogHeader>
        <div className="space-y-3">
          <button onClick={() => fileRef.current?.click()} data-testid="vault-file-select"
            className="w-full border-2 border-dashed rounded-lg p-6 text-center hover:border-primary text-sm text-muted-foreground">
            {file ? <span className="text-foreground font-medium">{file.name}</span> : <><Upload className="w-6 h-6 mx-auto mb-1" />Choose a file (image, PDF, PPTX, audio, video…)</>}
          </button>
          <input ref={fileRef} type="file" className="hidden" onChange={(e) => setFile(e.target.files[0])} />
          <input data-testid="vault-name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Asset name *" className="w-full px-3 py-2 text-sm border rounded-sm" />
          <div className="grid grid-cols-2 gap-2">
            <select data-testid="vault-type" value={form.asset_type} onChange={(e) => setForm({ ...form, asset_type: e.target.value })} className="text-sm border rounded-sm px-2 py-2">
              {meta.asset_types.map((t) => <option key={t}>{t}</option>)}
            </select>
            <select data-testid="vault-source" value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value })} className="text-sm border rounded-sm px-2 py-2">
              {meta.sources.filter((s) => s !== "Superseded" && s !== "Archived").map((s) => <option key={s}>{s}</option>)}
            </select>
            <input value={form.product_family} onChange={(e) => setForm({ ...form, product_family: e.target.value })} placeholder="Product family" className="px-3 py-2 text-sm border rounded-sm" />
            <input value={form.character} onChange={(e) => setForm({ ...form, character: e.target.value })} placeholder="Character (optional)" className="px-3 py-2 text-sm border rounded-sm" />
          </div>
          <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} placeholder="Usage notes (optional)" rows={2} className="w-full px-3 py-2 text-sm border rounded-sm" />
          <p className="text-[11px] text-muted-foreground">Founder-imported assets default to <b>“Do not recreate or replace without permission”</b> and are reused as the preferred source.</p>
        </div>
        <DialogFooter>
          <button onClick={onClose} className="text-sm px-3 py-2">Cancel</button>
          <button data-testid="vault-upload-submit" onClick={submit} disabled={busy} className="inline-flex items-center gap-1.5 bg-navy text-white text-sm px-4 py-2 rounded-sm disabled:opacity-60">
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />} Import</button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function DetailDialog({ asset, meta, onClose, onChange }) {
  const [busy, setBusy] = useState("");
  const verRef = useRef();

  const patch = async (updates, label) => {
    setBusy(label); try { const r = await api.patch(`/vault/${asset.id}`, updates); toast.success("Updated"); onChange(r.data); }
    catch (e) { toast.error("Failed"); } finally { setBusy(""); }
  };
  const newVersion = async (f) => {
    if (!f) return; setBusy("version");
    try { const fd = new FormData(); fd.append("file", f); fd.append("reason", "Founder new version");
      const r = await api.post(`/vault/${asset.id}/new-version`, fd, { headers: { "Content-Type": "multipart/form-data" } });
      toast.success(`New version v${r.data.version} saved — original preserved`); onChange(r.data);
    } catch (e) { toast.error("Failed"); } finally { setBusy(""); }
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="vault-detail-dialog">
        <DialogHeader>
          <DialogTitle className="font-heading">{asset.name}</DialogTitle>
          <p className="text-xs text-muted-foreground">{asset.asset_code} · {asset.asset_type} · v{asset.version}</p>
        </DialogHeader>
        <div className="grid sm:grid-cols-[220px_1fr] gap-4">
          <div className="rounded-lg overflow-hidden border bg-navy/5 flex items-center justify-center min-h-[180px]">
            {asset.file?.previewable && /image|png|jpg|jpeg|webp|gif|svg/i.test(asset.file.ext)
              ? <img src={abs(asset.file.url)} alt={asset.name} className="w-full object-contain" />
              : <FileText className="w-12 h-12 text-navy/30" />}
          </div>
          <div className="text-sm space-y-1.5">
            <Row k="Classification (Source)" v={asset.source} />
            <Row k="Replacement rule" v={asset.replacement_rule} />
            <Row k="Approval status" v={asset.approval_status} />
            <Row k="Product family" v={asset.product_family || "—"} />
            <Row k="Character" v={asset.character || "—"} />
            <Row k="Knowledge Record" v={asset.knowledge_record_id || "—"} />
            <Row k="Related products" v={(asset.related_products || []).length} />
            <Row k="Uploaded" v={new Date(asset.upload_date).toLocaleDateString()} />
            {asset.usage_notes && <Row k="Notes" v={asset.usage_notes} />}
          </div>
        </div>

        <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t">
          <a data-testid="vault-download" href={`${abs(asset.file.url)}?download=1&name=${encodeURIComponent(asset.name)}`}
            className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-sm border hover:border-primary"><Download className="w-4 h-4" /> Download</a>
          <button data-testid="vault-mark-founder" onClick={() => patch({ approval_status: "Founder Approved" }, "founder")} disabled={busy === "founder"}
            className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-sm border hover:border-primary"><Star className="w-4 h-4" /> Founder Approved</button>
          <button data-testid="vault-mark-protected" onClick={() => patch({ source: "Protected Master" }, "protected")} disabled={busy === "protected"}
            className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-sm border hover:border-primary"><ShieldCheck className="w-4 h-4" /> Protected Master</button>
          <button data-testid="vault-new-version" onClick={() => verRef.current?.click()} disabled={busy === "version"}
            className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-sm border hover:border-primary">
            {busy === "version" ? <Loader2 className="w-4 h-4 animate-spin" /> : <History className="w-4 h-4" />} New Version</button>
          <input ref={verRef} type="file" className="hidden" onChange={(e) => newVersion(e.target.files[0])} />
          <button data-testid="vault-archive" onClick={() => patch({ archived: true }, "archive")} disabled={busy === "archive"}
            className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-sm border hover:border-destructive text-destructive ml-auto"><Archive className="w-4 h-4" /> Archive</button>
        </div>

        {(asset.version_history || []).length > 1 && (
          <div className="mt-3 pt-3 border-t" data-testid="vault-version-history">
            <p className="overline text-primary mb-2 flex items-center gap-1.5"><History className="w-3.5 h-3.5" /> Version History</p>
            <div className="space-y-1">
              {asset.version_history.slice().reverse().map((v) => (
                <div key={v.version} className="flex items-center gap-2 text-xs">
                  <span className="font-medium">v{v.version}</span>
                  <span className="text-muted-foreground flex-1 truncate">{v.reason} · {v.approval_status}</span>
                  <a href={abs(v.file.url)} target="_blank" rel="noreferrer" className="text-primary">view</a>
                </div>
              ))}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

const Row = ({ k, v }) => (
  <div className="flex gap-2"><span className="text-muted-foreground w-40 shrink-0">{k}</span><span className="flex-1">{v}</span></div>
);
