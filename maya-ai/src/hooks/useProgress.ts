import { useCallback, useEffect, useState } from "react";
import type { CategoryId, Layer } from "../types";

export interface JournalEntry {
  scenarioId: string;
  title: string;
  layer: Layer;
  categories: CategoryId[];
  completedAt: string;
}

export interface ProgressState {
  journal: JournalEntry[];
  streak: number;
  lastCompletedDate: string | null;
}

const STORAGE_KEY = "maya-ai:progress:v1";

const EMPTY_STATE: ProgressState = {
  journal: [],
  streak: 0,
  lastCompletedDate: null,
};

function loadState(): ProgressState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return EMPTY_STATE;
    const parsed = JSON.parse(raw) as ProgressState;
    return { ...EMPTY_STATE, ...parsed };
  } catch {
    return EMPTY_STATE;
  }
}

function dayKey(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function isYesterday(lastKey: string, todayKey: string): boolean {
  const last = new Date(lastKey);
  const today = new Date(todayKey);
  const diffDays = Math.round((today.getTime() - last.getTime()) / 86_400_000);
  return diffDays === 1;
}

export function useProgress() {
  const [state, setState] = useState<ProgressState>(loadState);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }, [state]);

  const recordCompletion = useCallback(
    (scenarioId: string, title: string, layer: Layer, categories: CategoryId[]) => {
      setState((prev) => {
        const today = dayKey(new Date());
        let nextStreak = prev.streak;
        if (prev.lastCompletedDate === today) {
          nextStreak = prev.streak || 1;
        } else if (prev.lastCompletedDate && isYesterday(prev.lastCompletedDate, today)) {
          nextStreak = prev.streak + 1;
        } else {
          nextStreak = 1;
        }
        const entry: JournalEntry = {
          scenarioId,
          title,
          layer,
          categories,
          completedAt: new Date().toISOString(),
        };
        return {
          journal: [entry, ...prev.journal].slice(0, 200),
          streak: nextStreak,
          lastCompletedDate: today,
        };
      });
    },
    []
  );

  const categoryCoverage = useCallback(
    (layer?: Layer) => {
      const coverage = new Map<CategoryId, number>();
      for (const entry of state.journal) {
        if (layer && entry.layer !== layer) continue;
        for (const c of entry.categories) {
          coverage.set(c, (coverage.get(c) ?? 0) + 1);
        }
      }
      return coverage;
    },
    [state.journal]
  );

  const clearProgress = useCallback(() => setState(EMPTY_STATE), []);

  return { ...state, recordCompletion, categoryCoverage, clearProgress };
}
