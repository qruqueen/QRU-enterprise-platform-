import { Injectable } from "@nestjs/common";
import { KnowledgeRepository } from "../knowledge/repositories/knowledge.repository";
import { ClassifierService } from "./classifier.service";
import { DuplicateDetectorService } from "./duplicate-detector.service";
import { ExtractorService } from "./extractor.service";
import { KnowledgeRecordBuilder } from "./knowledge-record.builder";

export interface AIIntakeRequest { sourceType: "text" | "markdown" | "pdf" | "transcript"; content: string; }
export interface AIIntakeResult { knowledgeRecordId: string; status: "Draft"; confidence: number; duplicateCandidates: string[]; nextAction: "Verification"; }

@Injectable()
export class AIIntakeService {
  constructor(private readonly extractor: ExtractorService, private readonly classifier: ClassifierService, private readonly duplicateDetector: DuplicateDetectorService, private readonly builder: KnowledgeRecordBuilder, private readonly repository: KnowledgeRepository) {}
  async intake(request: AIIntakeRequest): Promise<AIIntakeResult> {
    const extracted = await this.extractor.extract(request);
    const classification = await this.classifier.classify(extracted);
    const duplicates = await this.duplicateDetector.findDuplicates(classification);
    const knowledgeRecord = await this.builder.build({ extracted, classification, duplicates });
    const savedRecord = await this.repository.create(knowledgeRecord);
    return { knowledgeRecordId: savedRecord.id, status: "Draft", confidence: savedRecord.confidence, duplicateCandidates: duplicates, nextAction: "Verification" };
  }
}
