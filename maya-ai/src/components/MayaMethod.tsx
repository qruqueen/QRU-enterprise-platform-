import { useEffect, useState } from "react";
import { MAYA_METHOD_QUESTIONS, type Scenario } from "../types";

interface MayaMethodProps {
  scenario: Scenario;
  onComplete: () => void;
}

export default function MayaMethod({ scenario, onComplete }: MayaMethodProps) {
  const [step, setStep] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [notes, setNotes] = useState<string[]>(["", "", "", "", ""]);
  const [finished, setFinished] = useState(false);

  useEffect(() => {
    setStep(0);
    setRevealed(false);
    setNotes(["", "", "", "", ""]);
    setFinished(false);
  }, [scenario.id]);

  const isLastStep = step === MAYA_METHOD_QUESTIONS.length - 1;

  const handleNoteChange = (value: string) => {
    setNotes((prev) => {
      const next = [...prev];
      next[step] = value;
      return next;
    });
  };

  const goNext = () => {
    if (isLastStep) {
      setFinished(true);
      onComplete();
      return;
    }
    setStep((s) => s + 1);
    setRevealed(false);
  };

  return (
    <section className="maya-method" aria-label="The Maya Method">
      <div className="method-progress" role="progressbar" aria-valuemin={1} aria-valuemax={5} aria-valuenow={step + 1}>
        {MAYA_METHOD_QUESTIONS.map((_, i) => (
          <span
            key={i}
            className={`method-dot${i === step ? " method-dot--active" : ""}${i < step ? " method-dot--done" : ""}`}
          />
        ))}
      </div>

      <p className="method-step-label">
        Question {step + 1} of {MAYA_METHOD_QUESTIONS.length}
      </p>
      <h3 className="method-question">{MAYA_METHOD_QUESTIONS[step]}</h3>

      <label className="method-notes-label" htmlFor="method-notes">
        Your thinking (optional)
      </label>
      <textarea
        id="method-notes"
        className="method-notes"
        placeholder="Jot down what you think before Maya weighs in…"
        value={notes[step]}
        onChange={(e) => handleNoteChange(e.target.value)}
        rows={2}
      />

      {!revealed ? (
        <button type="button" className="primary-button" onClick={() => setRevealed(true)}>
          Reveal Maya's thinking
        </button>
      ) : (
        <div className="method-guidance" role="status">
          <span className="method-guidance-badge" aria-hidden="true">
            🧭 Maya
          </span>
          <p>{scenario.method_guidance[step]}</p>
        </div>
      )}

      <button
        type="button"
        className="primary-button primary-button--next"
        onClick={goNext}
        disabled={!revealed || finished}
      >
        {finished ? "Completed ✓" : isLastStep ? "Finish scenario" : "Next question"}
      </button>
    </section>
  );
}
