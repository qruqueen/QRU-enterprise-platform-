import { CATEGORIES, LAYERS, type CategoryId } from "../types";
import type { JournalEntry } from "../hooks/useProgress";

interface ProgressJournalProps {
  journal: JournalEntry[];
  streak: number;
  categoryCoverage: (layer?: JournalEntry["layer"]) => Map<CategoryId, number>;
  onClose: () => void;
}

export default function ProgressJournal({ journal, streak, categoryCoverage, onClose }: ProgressJournalProps) {
  const overallCoverage = categoryCoverage();
  const coveredCount = CATEGORIES.filter((c) => (overallCoverage.get(c.id) ?? 0) > 0).length;

  return (
    <div className="journal-overlay" role="dialog" aria-modal="true" aria-label="Progress journal">
      <div className="journal-panel">
        <div className="journal-header">
          <h2>Your Financial Thinking Journal</h2>
          <button type="button" className="ghost-button" onClick={onClose} aria-label="Close journal">
            ✕
          </button>
        </div>

        <div className="journal-summary">
          <div className="journal-stat">
            <span className="journal-stat-value">{journal.length}</span>
            <span className="journal-stat-label">Scenarios completed</span>
          </div>
          <div className="journal-stat">
            <span className="journal-stat-value">{streak}</span>
            <span className="journal-stat-label">Day streak</span>
          </div>
          <div className="journal-stat">
            <span className="journal-stat-value">{coveredCount}/8</span>
            <span className="journal-stat-label">Categories explored</span>
          </div>
        </div>

        <h3 className="journal-subheading">Category coverage by layer</h3>
        <div className="journal-coverage-grid">
          {LAYERS.map((layer) => {
            const coverage = categoryCoverage(layer.id);
            return (
              <div key={layer.id} className="journal-coverage-layer">
                <p className="journal-coverage-layer-name">{layer.name}</p>
                <ul className="journal-coverage-list">
                  {CATEGORIES.map((category) => {
                    const count = coverage.get(category.id) ?? 0;
                    return (
                      <li
                        key={category.id}
                        className={`journal-coverage-item${count > 0 ? " journal-coverage-item--seen" : ""}`}
                      >
                        <span aria-hidden="true">{category.emoji}</span>
                        <span className="journal-coverage-item-name">{category.name}</span>
                        <span className="journal-coverage-item-count">{count}</span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            );
          })}
        </div>

        <h3 className="journal-subheading">Recent scenarios</h3>
        {journal.length === 0 ? (
          <p className="journal-empty">No scenarios completed yet — finish one to start your journal.</p>
        ) : (
          <ul className="journal-entries">
            {journal.slice(0, 25).map((entry, i) => (
              <li key={`${entry.scenarioId}-${entry.completedAt}-${i}`} className="journal-entry">
                <div>
                  <p className="journal-entry-title">{entry.title}</p>
                  <p className="journal-entry-meta">
                    {LAYERS.find((l) => l.id === entry.layer)?.name} ·{" "}
                    {new Date(entry.completedAt).toLocaleDateString()}
                  </p>
                </div>
                <div className="journal-entry-categories">
                  {entry.categories.map((c) => (
                    <span key={c} aria-hidden="true">
                      {CATEGORIES.find((cat) => cat.id === c)?.emoji}
                    </span>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
