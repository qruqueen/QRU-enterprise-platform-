import { useAuth } from "@/context/AuthContext";
import { useMusic, MUSIC_MODES } from "@/context/MusicContext";
import { PageHeader } from "@/components/shared";
import { Slider } from "@/components/ui/slider";
import { User, ShieldCheck, Sparkles, Music, Volume2 } from "lucide-react";

export default function Settings() {
  const { user } = useAuth();
  const { mode, setMode, volume, setVolume } = useMusic();

  return (
    <div>
      <PageHeader overline="Settings" title="Enterprise Settings" description="Your profile, the QRU operating configuration, and Focus Audio for concentration, learning & reflection." />

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="bg-card border rounded-md p-6">
          <div className="flex items-center gap-2 mb-4"><User className="w-4 h-4 text-primary" /><h3 className="font-heading font-semibold">Profile</h3></div>
          <dl className="text-sm space-y-3">
            <div className="flex justify-between"><dt className="text-muted-foreground">Name</dt><dd className="font-medium">{user?.name}</dd></div>
            <div className="flex justify-between"><dt className="text-muted-foreground">Email</dt><dd className="font-medium">{user?.email}</dd></div>
            <div className="flex justify-between"><dt className="text-muted-foreground">Role</dt><dd><span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-sm font-medium">{user?.role}</span></dd></div>
          </dl>
        </div>

        <div className="bg-card border rounded-md p-6">
          <div className="flex items-center gap-2 mb-4"><Sparkles className="w-4 h-4 text-primary" /><h3 className="font-heading font-semibold">AI Configuration</h3></div>
          <dl className="text-sm space-y-3">
            <div className="flex justify-between"><dt className="text-muted-foreground">Command & Manufacturing Model</dt><dd className="font-medium">GPT-5.5</dd></div>
            <div className="flex justify-between"><dt className="text-muted-foreground">Translation Engine™</dt><dd className="font-medium text-success">Active</dd></div>
            <div className="flex justify-between"><dt className="text-muted-foreground">Human Approval</dt><dd className="font-medium text-success">Required for publication</dd></div>
          </dl>
        </div>

        {/* Focus Audio */}
        <div className="bg-card border rounded-md p-6 lg:col-span-2">
          <div className="flex items-center gap-2 mb-1"><Music className="w-4 h-4 text-gold" /><h3 className="font-heading font-semibold">QRU Focus Audio</h3></div>
          <p className="text-sm text-muted-foreground mb-4">Optional ambient audio to improve concentration, learning, and reflection — never to distract. Muted by default. (Placeholder audio; licensed QRU frequency collections can be added later.)</p>
          <div className="flex flex-wrap gap-2">
            {MUSIC_MODES.map((m) => (
              <button key={m} data-testid={`settings-music-${m.toLowerCase()}`} onClick={() => setMode(m)}
                className={`text-sm px-3 py-1.5 rounded-sm border transition-colors ${mode === m ? "bg-primary text-primary-foreground border-primary" : "hover:border-primary"}`}>
                {m}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-3 mt-5 max-w-sm">
            <Volume2 className="w-4 h-4 text-muted-foreground" />
            <Slider value={[volume * 100]} max={100} step={1} onValueChange={(v) => setVolume(v[0] / 100)} className="flex-1" />
            <span className="text-xs text-muted-foreground w-10 text-right">{Math.round(volume * 100)}%</span>
          </div>
        </div>

        <div className="bg-card border rounded-md p-6 lg:col-span-2">
          <div className="flex items-center gap-2 mb-4"><ShieldCheck className="w-4 h-4 text-primary" /><h3 className="font-heading font-semibold">QRU Philosophy</h3></div>
          <p className="text-sm text-muted-foreground leading-relaxed max-w-3xl">
            AI exists to assist humans. Humans remain responsible for truth, ethics, governance, and final approval.
            No product is published without human approval. QRU does not simplify the truth — QRU simplifies the path to understanding the truth.
          </p>
        </div>

        <div className="rounded-md p-6 lg:col-span-2 flex items-center gap-4 text-white" style={{ background: "hsl(var(--navy))" }}>
          <img src="/qru-shield-light.png" alt="QRU" className="w-12 h-12 object-contain shrink-0" />
          <div>
            <p className="font-heading font-bold">QRU FACTORY™ · The Understanding Operating System</p>
            <p className="text-white/50 text-sm">Quest for Real Understanding · Manufacturing understanding from verified knowledge.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
