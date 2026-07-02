import { createContext, useContext, useEffect, useRef, useState } from "react";

const MusicContext = createContext(null);

// QRU music categories. Placeholder synthesis via Web Audio — swap for licensed
// audio/frequency collections later by replacing startEngine() with <audio src>.
export const MUSIC_MODES = ["Off", "Focus", "Calm", "Nature", "Orchestra", "Lo-Fi", "Solfeggio", "Instrumental"];

// Chord/frequency recipe per mode (Hz). Nature uses filtered noise instead.
const RECIPES = {
  Focus: [110, 164.81, 220],
  Calm: [130.81, 196, 261.63],
  Orchestra: [130.81, 164.81, 196, 261.63],
  "Lo-Fi": [98, 146.83, 174.61],
  Solfeggio: [396, 528, 639],
  Instrumental: [146.83, 220, 293.66],
};

export function MusicProvider({ children }) {
  const [mode, setMode] = useState(() => localStorage.getItem("qru_music_mode") || "Off");
  const [volume, setVolume] = useState(() => parseFloat(localStorage.getItem("qru_music_vol") ?? "0.25"));
  const ctxRef = useRef(null);
  const nodesRef = useRef([]);
  const masterRef = useRef(null);

  const stopEngine = () => {
    nodesRef.current.forEach((n) => { try { n.stop?.(); n.disconnect?.(); } catch {} });
    nodesRef.current = [];
  };

  const startEngine = (m) => {
    stopEngine();
    if (m === "Off" || !ctxRef.current) return;
    const ctx = ctxRef.current;
    const master = masterRef.current;

    if (m === "Nature") {
      // gentle filtered noise (rain/wind-like)
      const bufferSize = 2 * ctx.sampleRate;
      const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
      const data = buffer.getChannelData(0);
      for (let i = 0; i < bufferSize; i++) data[i] = (Math.random() * 2 - 1) * 0.5;
      const noise = ctx.createBufferSource();
      noise.buffer = buffer;
      noise.loop = true;
      const filter = ctx.createBiquadFilter();
      filter.type = "lowpass";
      filter.frequency.value = 800;
      noise.connect(filter);
      filter.connect(master);
      noise.start();
      nodesRef.current = [noise, filter];
      return;
    }

    const freqs = RECIPES[m] || RECIPES.Calm;
    freqs.forEach((f, i) => {
      const osc = ctx.createOscillator();
      osc.type = m === "Lo-Fi" ? "triangle" : m === "Orchestra" ? "sawtooth" : "sine";
      osc.frequency.value = f;
      const g = ctx.createGain();
      g.gain.value = 0.12 / (i + 1);
      // subtle slow LFO for a living pad
      const lfo = ctx.createOscillator();
      lfo.frequency.value = 0.08 + i * 0.03;
      const lfoGain = ctx.createGain();
      lfoGain.gain.value = 0.04;
      lfo.connect(lfoGain);
      lfoGain.connect(g.gain);
      osc.connect(g);
      g.connect(master);
      osc.start();
      lfo.start();
      nodesRef.current.push(osc, g, lfo, lfoGain);
    });
  };

  const ensureCtx = () => {
    if (!ctxRef.current) {
      const AC = window.AudioContext || window.webkitAudioContext;
      const ctx = new AC();
      const master = ctx.createGain();
      master.gain.value = volume;
      master.connect(ctx.destination);
      ctxRef.current = ctx;
      masterRef.current = master;
    }
    if (ctxRef.current.state === "suspended") ctxRef.current.resume();
  };

  const changeMode = (m) => {
    setMode(m);
    localStorage.setItem("qru_music_mode", m);
    if (m !== "Off") ensureCtx();
    startEngine(m);
  };

  const changeVolume = (v) => {
    setVolume(v);
    localStorage.setItem("qru_music_vol", String(v));
    if (masterRef.current) masterRef.current.gain.value = v;
  };

  useEffect(() => () => stopEngine(), []);

  return (
    <MusicContext.Provider value={{ mode, setMode: changeMode, volume, setVolume: changeVolume, modes: MUSIC_MODES }}>
      {children}
    </MusicContext.Provider>
  );
}

export const useMusic = () => useContext(MusicContext);
