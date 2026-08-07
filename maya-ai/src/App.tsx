import { useMemo, useState } from "react";
import Header from "./components/Header";
import LayerSelect from "./components/LayerSelect";
import CategoryStrip from "./components/CategoryStrip";
import ScenarioCard from "./components/ScenarioCard";
import MayaMethod from "./components/MayaMethod";
import ProgressJournal from "./components/ProgressJournal";
import { useProgress } from "./hooks/useProgress";
import { pickScenario } from "./utils/scenarioEngine";
import type { Layer } from "./types";

export default function App() {
  const [layer, setLayer] = useState<Layer>("little");
  const [scenario, setScenario] = useState(() => pickScenario("little"));
  const [completedThisRound, setCompletedThisRound] = useState(false);
  const [journalOpen, setJournalOpen] = useState(false);

  const { journal, streak, recordCompletion, categoryCoverage } = useProgress();

  const handleLayerSelect = (nextLayer: Layer) => {
    if (nextLayer === layer) return;
    setLayer(nextLayer);
    setScenario(pickScenario(nextLayer));
    setCompletedThisRound(false);
  };

  const handleNewScenario = () => {
    setScenario((prev) => pickScenario(layer, prev.id));
    setCompletedThisRound(false);
  };

  const handleComplete = () => {
    recordCompletion(scenario.id, scenario.title, scenario.layer, scenario.categories);
    setCompletedThisRound(true);
  };

  const mayaMethod = useMemo(
    () => <MayaMethod key={scenario.id} scenario={scenario} onComplete={handleComplete} />,
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [scenario]
  );

  return (
    <div className="app-shell">
      <Header streak={streak} onOpenJournal={() => setJournalOpen(true)} />

      <main className="app-main">
        <LayerSelect activeLayer={layer} onSelect={handleLayerSelect} />

        <CategoryStrip activeCategories={scenario.categories} />

        <ScenarioCard scenario={scenario} />

        {mayaMethod}

        {completedThisRound && (
          <div className="completion-panel">
            <p>🎉 Nice work — you ran this one through the full Maya Method.</p>
            <div className="completion-actions">
              <button type="button" className="primary-button" onClick={handleNewScenario}>
                Try a new scenario
              </button>
            </div>
          </div>
        )}
      </main>

      {journalOpen && (
        <ProgressJournal
          journal={journal}
          streak={streak}
          categoryCoverage={categoryCoverage}
          onClose={() => setJournalOpen(false)}
        />
      )}
    </div>
  );
}
