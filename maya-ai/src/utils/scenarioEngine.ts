import type { Layer, Scenario } from "../types";
import { scenariosForLayer } from "../data/scenarios";

/** Picks a random scenario for the layer, avoiding the given id when other options exist. */
export function pickScenario(layer: Layer, excludeId?: string): Scenario {
  const pool = scenariosForLayer(layer);
  const candidates = excludeId && pool.length > 1 ? pool.filter((s) => s.id !== excludeId) : pool;
  const index = Math.floor(Math.random() * candidates.length);
  return candidates[index];
}
