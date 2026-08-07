import type { Layer, Scenario } from "../../types";
import little from "./little.json";
import teen from "./teen.json";
import next from "./next.json";

const ALL_SCENARIOS = [...little, ...teen, ...next] as Scenario[];

export const scenariosForLayer = (layer: Layer): Scenario[] =>
  ALL_SCENARIOS.filter((s) => s.layer === layer);

export const scenarioById = (id: string): Scenario | undefined =>
  ALL_SCENARIOS.find((s) => s.id === id);

export default ALL_SCENARIOS;
