import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge } from "@/components/qru";
import { toast } from "sonner";
import {
  Loader2, Youtube, UploadCloud, CheckCircle2, ExternalLink, Film, Image as ImageIcon,
  AlertTriangle, ListVideo, Plug, Lock,
} from "lucide-react";

const CHUNK = 5 * 1024 * 1024; // 5 MB — bypasses proxy body limits

async function chunkedUpload(file, kind, onProgress) {
  const { data } = await api.post("/youtube/upload/init", { filename: file.name, kind });
  const uploadId = data.upload_id;
  let sent = 0;
  for (let start = 0; start < file.size; start += CHUNK) {
    const blob = file.slice(start, start + CHUNK);
    const buf = await blob.arrayBuffer();
    await api.post(`/youtube/upload/chunk?upload_id=${encodeURIComponent(uploadId)}`, buf, {
      headers: { "Content-Type": "application/octet-stream" },
    });
    sent += blob.size;
    onProgress && onProgress(Math.round((sent / file.size) * 100));
  }
  return uploadId;
}

export default function YouTubePublisher() {
  const nav = useNavigate();
  const [status, setStatus] = useState(null);
  const [playlists, setPlaylists] = useState([]);
  const [pubs, setPubs] = useState([]);
  const [products, setProducts] = useState([]);

  const [productId, setProductId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [tags, setTags] = useState("");
  const [privacy, setPrivacy] = useState("private");
  const [playlistId, setPlaylistId] = useState("");
  const [videoFile, setVideoFile] = useState(null);
  const [thumbFile, setThumbFile] = useState(null);
  const [factoryAssets, setFactoryAssets] = useState([]);
  const [factoryAssetId, setFactoryAssetId] = useState("");
  const [source, setSource] = useState("factory"); // "factory" | "manual"

  const [progress, setProgress] = useState(0);
  const [busy, setBusy] = useState(false);
  const [backfilling, setBackfilling] = useState(false);
  const [result, setResult] = useState(null);

  const loadPubs = () => api.get("/youtube/publications").then((r) => setPubs(r.data.publications)).catch(() => {});
  const loadFactoryAssets = () => api.get("/youtube/factory-assets").then((r) => {
    const list = (r.data.assets || []).filter((a) => a.file_available && !a.is_draft_preview);
    setFactoryAssets(list);
    return list;
  }).catch(() => []);
  const runBackfill = async () => {
    setBackfilling(true);
    toast.info("Rendering videos in the background… this can take a few minutes. You can keep working.");
    try {
      await api.post("/video/backfill", {});
      let done = false, guard = 0;
      while (!done && guard < 120) {
        guard += 1;
        await new Promise((r) => setTimeout(r, 4000));
        const { data } = await api.get("/video/backfill/status");
        const job = data.job || {};
        const s = data.summary || {};
        if (job.running) {
          toast.info(`Rendering… ${job.done || 0}/${job.total || 0} done${job.current_title ? ` — ${job.current_title}` : ""}.`);
        }
        done = !job.running;
        if (done) {
          toast.success(`Videos ready — ${s.book_trailers_ok || 0}/${s.book_trailers_total || 0} trailers, ${s.script_videos_ok || 0}/${s.script_videos_total || 0} script videos.`);
        }
      }
      const list = await loadFactoryAssets();
      if ((list || []).length > 0) setSource("factory");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not start rendering. Please try again.");
      await loadFactoryAssets();
    } finally {
      setBackfilling(false);
    }
  };
  useEffect(() => {
    api.get("/youtube/status").then((r) => {
      setStatus(r.data);
      if (r.data.connected) {
        api.get("/youtube/playlists").then((p) => setPlaylists(p.data.playlists)).catch(() => {});
      }
    }).catch(() => setStatus(false));
    api.get("/founder-inbox").then((r) => setProducts((r.data.products || []).slice(0, 200))).catch(() => {});
    loadFactoryAssets().then((list) => { if ((list || []).length === 0) setSource("manual"); });
    loadPubs();
  }, []);

  const onSelectFactoryAsset = (id) => {
    setFactoryAssetId(id);
    const a = factoryAssets.find((x) => x.qru_asset_id === id);
    if (a) { setTitle(a.title || ""); setVideoFile(null); }
  };

  const onSelectProduct = (id) => {
    setProductId(id);
    const p = products.find((x) => x.id === id);
    if (p && !title) setTitle(p.title || "");
  };

  const publish = async () => {
    if (source === "factory") {
      if (!factoryAssetId) return toast.error("Select a Factory-manufactured video.");
    } else if (!videoFile) {
      return toast.error("Choose an MP4 video file first.");
    }
    setBusy(true); setProgress(0); setResult(null);
    try {
      let videoUploadId = null, thumbUploadId = null;
      if (source === "manual") {
        videoUploadId = await chunkedUpload(videoFile, "video", setProgress);
        if (thumbFile) thumbUploadId = await chunkedUpload(thumbFile, "thumbnail");
      }
      const { data } = await api.post("/youtube/publish", {
        video_upload_id: videoUploadId,
        thumbnail_upload_id: thumbUploadId,
        factory_asset_id: source === "factory" ? factoryAssetId : null,
        product_id: productId || null,
        title: title || null,
        description: description || null,
        tags: tags ? tags.split(",").map((t) => t.trim()).filter(Boolean) : null,
        privacy,
        playlist_id: playlistId || null,
      });
      setResult(data);
      toast.success(`Published to YouTube — Video ID ${data.video_id}`);
      setVideoFile(null); setThumbFile(null); setProgress(0);
      loadPubs();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Publish failed");
    } finally { setBusy(false); }
  };

  if (status === null) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;

  return (
    <div>
      <PageHeader
        overline="QRU YouTube Publisher™ · MO-006 · Founder Upload Mode"
        title="YouTube Studio"
        description="Provide the finished MP4 — QRU applies the manufactured title, description, tags, thumbnail and playlist, uploads it to your channel via the YouTube Data API, and returns a real Video ID. Videos publish Private by default; make them Public after your own QC."
        actions={<VerifiedBadge label="Real Publishing · Treasure Standard™" testid="yt-badge" />}
      />

      {/* Connection status */}
      {!status || !status.connected ? (
        <div className="qru-card p-6 mb-6 border-amber-200 bg-amber-50" data-testid="yt-not-connected">
          <p className="font-heading font-bold text-navy flex items-center gap-2 mb-1"><AlertTriangle className="w-4 h-4 text-amber-600" /> YouTube not connected</p>
          <p className="text-sm text-muted-foreground mb-3">{(status && status.reason) || "Connect your YouTube channel first."}</p>
          <button onClick={() => nav("/connectors")} data-testid="yt-goto-connectors"
            className="text-sm inline-flex items-center gap-2 bg-navy text-white px-4 py-2 rounded-sm font-semibold"><Plug className="w-4 h-4" /> Go to Publishing Connectors™</button>
        </div>
      ) : (
        <div className="flex items-center gap-2 mb-6 text-sm" data-testid="yt-connected">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span className="text-navy font-medium">Connected as <b>{status.account}</b></span>
          <StatusChip status={status.can_upload ? "Ready to Publish" : "Needs Authorization"} />
        </div>
      )}

      {status && status.connected && (
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Composer */}
          <div className="lg:col-span-2">
            <Panel title="Compose & Upload" icon={Film} accent="royal" testid="yt-composer">
              <div className="space-y-4">
                {/* Source: Factory asset (no re-upload) vs manual (external) */}
                <div className="flex gap-2" data-testid="yt-source-toggle">
                  <button onClick={() => setSource("factory")} data-testid="yt-source-factory"
                    className={`flex-1 text-left border rounded-md p-3 transition-colors ${source === "factory" ? "border-royal ring-2 ring-royal/30 bg-royal/[0.04]" : "border-navy/15 hover:border-royal/40"}`}>
                    <p className="text-sm font-bold text-navy flex items-center gap-1.5"><Film className="w-4 h-4 text-royal" /> Factory-manufactured video</p>
                    <p className="text-[11px] text-muted-foreground mt-0.5">The Factory already owns the MP4 — no re-upload. Metadata, captions & thumbnail auto-populated.</p>
                  </button>
                  <button onClick={() => setSource("manual")} data-testid="yt-source-manual"
                    className={`flex-1 text-left border rounded-md p-3 transition-colors ${source === "manual" ? "border-royal ring-2 ring-royal/30 bg-royal/[0.04]" : "border-navy/15 hover:border-royal/40"}`}>
                    <p className="text-sm font-bold text-navy flex items-center gap-1.5"><UploadCloud className="w-4 h-4 text-royal" /> External video (manual upload)</p>
                    <p className="text-[11px] text-muted-foreground mt-0.5">Browse and upload a video created outside the Factory.</p>
                  </button>
                </div>

                {source === "factory" && (
                  <div data-testid="yt-factory-picker">
                    <div className="flex items-center justify-between gap-2">
                      <label className="text-xs font-bold text-navy uppercase tracking-wide">Select a Factory-owned video</label>
                      <button onClick={runBackfill} disabled={backfilling} data-testid="yt-render-missing"
                        className="text-[11px] font-semibold text-royal border border-royal/30 rounded-full px-3 py-1 hover:bg-royal/[0.06] disabled:opacity-50">
                        {backfilling ? "Rendering…" : "Generate missing videos"}
                      </button>
                    </div>
                    {factoryAssets.length === 0 ? (
                      <p className="text-[12px] text-amber-700 mt-1">No Factory videos yet. Click <span className="font-semibold">Generate missing videos</span> to render trailers for your published books and MP4s for your video scripts — they'll appear here automatically.</p>
                    ) : (
                      <select data-testid="yt-factory-asset" value={factoryAssetId} onChange={(e) => onSelectFactoryAsset(e.target.value)} className="w-full mt-1 border rounded-sm p-2 text-sm">
                        <option value="">— Choose a manufactured video —</option>
                        {factoryAssets.map((a) => (
                          <option key={a.qru_asset_id} value={a.qru_asset_id}>
                            {a.title} · {a.duration_seconds}s · {a.gold_master_certified ? "Gold Master" : a.production_status}
                          </option>
                        ))}
                      </select>
                    )}
                    {factoryAssetId && <p className="text-[11px] text-emerald-700 mt-1 flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> The Factory owns this video — MP4, thumbnail, captions & metadata will be sent automatically.</p>}
                  </div>
                )}

                <div>
                  <label className="text-xs font-bold text-navy uppercase tracking-wide">Link a manufactured product (optional — auto-fills metadata)</label>
                  <select data-testid="yt-product" value={productId} onChange={(e) => onSelectProduct(e.target.value)} className="w-full mt-1 border rounded-sm p-2 text-sm">
                    <option value="">— None (manual) —</option>
                    {products.map((p) => <option key={p.id} value={p.id}>{p.product_code} — {p.title}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-bold text-navy uppercase tracking-wide">Title</label>
                  <input data-testid="yt-title" value={title} onChange={(e) => setTitle(e.target.value)} maxLength={100} className="w-full mt-1 border rounded-sm p-2 text-sm" placeholder="Video title (max 100 chars)" />
                </div>
                <div>
                  <label className="text-xs font-bold text-navy uppercase tracking-wide">Description</label>
                  <textarea data-testid="yt-description" value={description} onChange={(e) => setDescription(e.target.value)} rows={4} className="w-full mt-1 border rounded-sm p-2 text-sm" placeholder="Description (auto-filled from the product if linked)" />
                </div>
                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-bold text-navy uppercase tracking-wide">Tags (comma-separated)</label>
                    <input data-testid="yt-tags" value={tags} onChange={(e) => setTags(e.target.value)} className="w-full mt-1 border rounded-sm p-2 text-sm" placeholder="education, science, qru" />
                  </div>
                  <div>
                    <label className="text-xs font-bold text-navy uppercase tracking-wide flex items-center gap-1"><Lock className="w-3 h-3" /> Visibility</label>
                    <select data-testid="yt-privacy" value={privacy} onChange={(e) => setPrivacy(e.target.value)} className="w-full mt-1 border rounded-sm p-2 text-sm">
                      <option value="private">Private (default)</option>
                      <option value="unlisted">Unlisted</option>
                      <option value="public">Public</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="text-xs font-bold text-navy uppercase tracking-wide flex items-center gap-1"><ListVideo className="w-3.5 h-3.5" /> Playlist (optional)</label>
                  <select data-testid="yt-playlist" value={playlistId} onChange={(e) => setPlaylistId(e.target.value)} className="w-full mt-1 border rounded-sm p-2 text-sm">
                    <option value="">— None —</option>
                    {playlists.map((pl) => <option key={pl.id} value={pl.id}>{pl.title}</option>)}
                  </select>
                </div>
                {source === "manual" && (
                <div className="grid sm:grid-cols-2 gap-4" data-testid="yt-manual-files">
                  <div>
                    <label className="text-xs font-bold text-navy uppercase tracking-wide flex items-center gap-1"><Film className="w-3.5 h-3.5" /> Video file (MP4)</label>
                    <input data-testid="yt-video-file" type="file" accept="video/mp4,video/quicktime,video/webm" onChange={(e) => setVideoFile(e.target.files?.[0] || null)} className="w-full mt-1 text-xs" />
                    {videoFile && <p className="text-[11px] text-muted-foreground mt-1">{videoFile.name} · {(videoFile.size / 1048576).toFixed(1)} MB</p>}
                  </div>
                  <div>
                    <label className="text-xs font-bold text-navy uppercase tracking-wide flex items-center gap-1"><ImageIcon className="w-3.5 h-3.5" /> Thumbnail (optional)</label>
                    <input data-testid="yt-thumb-file" type="file" accept="image/jpeg,image/png" onChange={(e) => setThumbFile(e.target.files?.[0] || null)} className="w-full mt-1 text-xs" />
                  </div>
                </div>
                )}

                {busy && progress > 0 && (
                  <div>
                    <div className="h-2 rounded-full bg-muted overflow-hidden"><div className="h-full bg-royal transition-[width]" style={{ width: `${progress}%` }} /></div>
                    <p className="text-[11px] text-muted-foreground mt-1">Uploading to QRU… {progress}% (then QRU uploads to YouTube)</p>
                  </div>
                )}

                <button onClick={publish} disabled={busy || (source === "factory" ? !factoryAssetId : !videoFile)} data-testid="yt-publish"
                  className="w-full inline-flex items-center justify-center gap-2 bg-navy text-white py-3 rounded-sm font-bold disabled:opacity-50 hover:bg-navy/90 transition-colors">
                  {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <UploadCloud className="w-4 h-4" />} {source === "factory" ? "Publish Factory video to YouTube" : "Publish to YouTube"}
                </button>

                {result && (
                  <div className="border border-emerald-200 bg-emerald-50 rounded-md p-4" data-testid="yt-result">
                    <p className="font-heading font-bold text-navy flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-emerald-600" /> Published — real Video ID</p>
                    <p className="text-sm text-navy mt-1 font-mono">{result.video_id} · {result.privacy}</p>
                    <div className="flex gap-3 mt-2">
                      <a href={result.url} target="_blank" rel="noreferrer" className="text-xs text-royal inline-flex items-center gap-1 font-semibold"><ExternalLink className="w-3 h-3" /> Watch</a>
                      <a href={result.studio_url} target="_blank" rel="noreferrer" className="text-xs text-royal inline-flex items-center gap-1 font-semibold"><ExternalLink className="w-3 h-3" /> Edit in YouTube Studio</a>
                    </div>
                  </div>
                )}
              </div>
            </Panel>
          </div>

          {/* History */}
          <div>
            <Panel title="Publication History" icon={Youtube} accent="gold" testid="yt-history">
              {pubs.length === 0 ? (
                <p className="text-sm text-muted-foreground">No videos published yet. Your real YouTube publications will appear here with their Video IDs.</p>
              ) : (
                <div className="space-y-2">
                  {pubs.map((p) => (
                    <a key={p.id} href={p.url} target="_blank" rel="noreferrer" data-testid={`yt-pub-${p.video_id}`}
                      className="block border rounded-sm p-2.5 hover:border-navy transition-colors">
                      <p className="text-sm font-medium text-navy truncate">{p.title}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[10px] font-mono text-muted-foreground">{p.video_id}</span>
                        <StatusChip status={p.privacy === "public" ? "Published" : p.privacy === "unlisted" ? "Draft" : "Private"} tone={p.privacy === "public" ? "emerald" : "slate"} />
                      </div>
                    </a>
                  ))}
                </div>
              )}
            </Panel>
          </div>
        </div>
      )}
    </div>
  );
}
