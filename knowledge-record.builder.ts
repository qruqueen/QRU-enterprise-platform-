import { Injectable } from "@nestjs/common";
import { KnowledgeRecord, KnowledgeStatus } from "../knowledge/entities/knowledge-record.entity";
import { ClassificationResult } from "./classifier.service";
import { ExtractionResult } from "./extractor.service";

export interface BuildKnowledgeRecordRequest { extracted: ExtractionResult; classification: ClassificationResult; duplicates: string[]; }

@Injectable()
export class KnowledgeRecordBuilder {
  async build(request: BuildKnowledgeRecordRequest): Promise<KnowledgeRecord> {
    const now = new Date();
    const record = new KnowledgeRecord();
    record.id = `KR-${crypto.randomUUID()}`;
    record.version = 1;
    record.status = KnowledgeStatus.DRAFT;
    record.title = request.extracted.concepts[0] ?? "Untitled Knowledge Record";
    record.question = `What is ${record.title}?`;
    record.simpleAnswer = request.extracted.normalizedText.substring(0, 250);
    record.detailedExplanation = request.extracted.normalizedText;
    record.qruTranslation = request.extracted.normalizedText.substring(0, 250);
    record.examples = request.extracted.examples;
    record.vocabulary = request.extracted.vocabulary;
    record.tags = request.classification.tags;
    record.references = request.extracted.references;
    record.confidence = request.classification.confidence;
    record.createdAt = now;
    record.updatedAt = now;
    void request.duplicates;
    return record;
  }
}
