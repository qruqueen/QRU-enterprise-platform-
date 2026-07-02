import { useMusic, MUSIC_MODES } from "@/context/MusicContext";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Slider } from "@/components/ui/slider";
import { Music, Volume2, VolumeX } from "lucide-react";

export default function MusicControl() {
  const { mode, setMode, volume, setVolume } = useMusic();
  const playing = mode !== "Off";

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          data-testid="music-control-btn"
          className={`relative p-2 rounded-sm hover:bg-muted transition-colors ${playing ? "text-gold" : "text-muted-foreground"}`}
          title="QRU Focus Audio"
        >
          <Music className="w-5 h-5" />
          {playing && <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-gold animate-pulse" />}
        </button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-64 rounded-md" data-testid="music-panel">
        <p className="overline text-primary mb-1">QRU Focus Audio</p>
        <p className="text-xs text-muted-foreground mb-3">For concentration, learning & reflection.</p>
        <div className="grid grid-cols-2 gap-1.5">
          {MUSIC_MODES.map((m) => (
            <button
              key={m}
              data-testid={`music-mode-${m.toLowerCase()}`}
              onClick={() => setMode(m)}
              className={`text-xs px-2 py-1.5 rounded-sm border transition-colors ${
                mode === m ? "bg-primary text-primary-foreground border-primary" : "hover:border-primary"
              }`}
            >
              {m}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2 mt-4">
          <button onClick={() => setVolume(volume > 0 ? 0 : 0.25)} data-testid="music-mute">
            {volume > 0 ? <Volume2 className="w-4 h-4 text-muted-foreground" /> : <VolumeX className="w-4 h-4 text-muted-foreground" />}
          </button>
          <Slider value={[volume * 100]} max={100} step={1} onValueChange={(v) => setVolume(v[0] / 100)} className="flex-1" />
        </div>
      </PopoverContent>
    </Popover>
  );
}
