interface HeaderProps {
  streak: number;
  onOpenJournal: () => void;
}

export default function Header({ streak, onOpenJournal }: HeaderProps) {
  return (
    <header className="app-header">
      <div className="brand">
        <span className="brand-mark" aria-hidden="true">
          🧭
        </span>
        <div>
          <p className="brand-name">Maya AI™</p>
          <p className="brand-tagline">Ascend Financial Literacy Series™</p>
        </div>
      </div>
      <div className="header-actions">
        {streak > 0 && (
          <span className="streak-badge" title="Days in a row you've worked through a scenario">
            🔥 {streak}-day streak
          </span>
        )}
        <button type="button" className="ghost-button" onClick={onOpenJournal}>
          📓 Journal
        </button>
      </div>
    </header>
  );
}
