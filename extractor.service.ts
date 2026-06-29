import { Injectable } from "@nestjs/common";
import { AIIntakeRequest } from "./ai-intake.service";

export interface ExtractionResult { concepts: string[]; claims: string[]; definitions: string[]; vocabulary: string[]; examples: string[]; references: string[]; normalizedText: string; }

@Injectable()
export class ExtractorService {
  async extract(request: AIIntakeRequest): Promise<ExtractionResult> {
    const normalized = request.content.trim();
    return { normalizedText: normalized, concepts: this.extractConcepts(normalized), claims: [], definitions: [], vocabulary: [], examples: [], references: [] };
  }
  private extractConcepts(text: string): string[] { const words = text.split(/\s+/).map((word) => word.replace(/[^a-zA-Z]/g, "")).filter((word) => word.length > 5); return [...new Set(words)].slice(0, 10); }
}
