import type { Scenario } from "../types";

interface ScenarioCardProps {
  scenario: Scenario;
}

export default function ScenarioCard({ scenario }: ScenarioCardProps) {
  return (
    <section className="scenario-card" aria-label="Today's scenario">
      <p className="scenario-eyebrow">Scenario</p>
      <h2 className="scenario-title">{scenario.title}</h2>
      <p className="scenario-prompt">{scenario.prompt}</p>
    </section>
  );
}
