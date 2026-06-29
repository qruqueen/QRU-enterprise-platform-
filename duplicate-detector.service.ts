import { Injectable } from "@nestjs/common";
import { ClassificationResult } from "./classifier.service";

export interface DuplicateCandidate { knowledgeRecordId: string; title: string; similarityScore: number; }

@Injectable()
export class DuplicateDetectorService {
  async findDuplicates(_classification: ClassificationResult): Promise<string[]> { return []; }
  async analyzeSimilarity(): Promise<DuplicateCandidate[]> { return []; }
}
