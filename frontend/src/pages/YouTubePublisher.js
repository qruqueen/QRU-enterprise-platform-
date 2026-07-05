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

  const [progress, setProgress] = useState(0);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);

  const loadPubs = () => api.get("/youtube/publications").then((r) => setPubs(r.data.publications)).catch(() => {});
  useEffect(() => {
    api.get("/youtube/status").then((r) => {
      setStatus(r.data);
      if (r.data.connected) {
        api.get("/youtube/playlists").then((p) => setPlaylists(p.data.playlists)).catch(() => {});
      }
    }).catch(() => setStatus(false));
    api.get("/founder-inbox").then((r) => setProducts((r.data.products || []).slice(0, 200))).catch(() => {});
    loadPubs();
  }, []);

  const onSelectProduct = (id) => {
    setProductId(id);
    const p = products.find((x) => x.id === id);
    if (p && !title) setTitle(p.title || "");
  };

  const publish = async () => {
    if (!videoFile) return toast.error("Choose an MP4 video file first.");
    if (!title && !productId) return toast.error("Add a title or link a product.");
    setBusy(true); setProgress(0); setResult(null);
    try {
      const videoUploadId = await chunkedUpload(videoFile, "video", setProgress);
      let thumbUploadId = null;
      if (thumbFile) thumbUploadId = await chunkedUpload(thumbFile, "thumbnail");
      const { data } = await api.post("/youtube/publish", {
        video_upload_id: videoUploadId,
        thumbnail_upload_id: thumbUploadId,
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
                <div className="grid sm:grid-cols-2 gap-4">
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

                {busy && progress > 0 && (
                  <div>
                    <div className="h-2 rounded-full bg-muted overflow-hidden"><div className="h-full bg-royal transition-[width]" style={{ width: `${progress}%` }} /></div>
                    <p className="text-[11px] text-muted-foreground mt-1">Uploading to QRU… {progress}% (then QRU uploads to YouTube)</p>
                  </div>
                )}

                <button onClick={publish} disabled={busy || !videoFile} data-testid="yt-publish"
                  className="w-full inline-flex items-center justify-center gap-2 bg-navy text-white py-3 rounded-sm font-bold disabled:opacity-50 hover:bg-navy/90 transition-colors">
                  {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <UploadCloud className="w-4 h-4" />} Publish to YouTube
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
