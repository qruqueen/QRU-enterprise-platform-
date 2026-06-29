import { Injectable } from "@nestjs/common";
import { ExtractionResult } from "./extractor.service";

export interface ClassificationResult { domain: string; category: string; tags: string[]; suggestedKnowledgeMasterFile: string | null; suggestedProducts: string[]; relatedKnowledgeRecords: string[]; confidence: number; }

@Injectable()
export class ClassifierService {
  async classify(extraction: ExtractionResult): Promise<ClassificationResult> {
    const text = extraction.normalizedText.toLowerCase();
    const isForex = text.includes("forex") || text.includes("currency") || text.includes("exchange rate");
    return { domain: isForex ? "Finance" : "Unclassified", category: isForex ? "Forex Fundamentals" : "General", tags: extraction.concepts, suggestedKnowledgeMasterFile: isForex ? "KMF-FX-001" : null, suggestedProducts: isForex ? ["Consumer Book", "Workbook", "Teacher Guide"] : [], relatedKnowledgeRecords: [], confidence: isForex ? 0.82 : 0.5 };
  }
}
