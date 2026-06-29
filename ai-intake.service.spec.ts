import { Test, TestingModule } from "@nestjs/testing";
import { KnowledgeRepository } from "../knowledge/repositories/knowledge.repository";
import { AIIntakeService } from "./ai-intake.service";
import { ClassifierService } from "./classifier.service";
import { DuplicateDetectorService } from "./duplicate-detector.service";
import { ExtractorService } from "./extractor.service";
import { KnowledgeRecordBuilder } from "./knowledge-record.builder";

describe("AIIntakeService", () => {
  let service: AIIntakeService;
  const extractor = { extract: jest.fn() };
  const classifier = { classify: jest.fn() };
  const duplicateDetector = { findDuplicates: jest.fn() };
  const builder = { build: jest.fn() };
  const repository = { create: jest.fn() };

  beforeEach(async () => {
    jest.clearAllMocks();
    const module: TestingModule = await Test.createTestingModule({ providers: [AIIntakeService, { provide: ExtractorService, useValue: extractor }, { provide: ClassifierService, useValue: classifier }, { provide: DuplicateDetectorService, useValue: duplicateDetector }, { provide: KnowledgeRecordBuilder, useValue: builder }, { provide: KnowledgeRepository, useValue: repository }] }).compile();
    service = module.get(AIIntakeService);
  });

  it("should be defined", () => { expect(service).toBeDefined(); });

  it("should orchestrate AI intake workflow", async () => {
    extractor.extract.mockResolvedValue({ concepts: ["Forex"], claims: [], definitions: [], vocabulary: [], examples: [], references: [], normalizedText: "Forex is the global currency market." });
    classifier.classify.mockResolvedValue({ domain: "Finance", category: "Forex Fundamentals", tags: ["Forex"], suggestedKnowledgeMasterFile: "KMF-FX-001", suggestedProducts: ["Consumer Book"], relatedKnowledgeRecords: [], confidence: 0.9 });
    duplicateDetector.findDuplicates.mockResolvedValue([]);
    builder.build.mockResolvedValue({ id: "KR-000001", confidence: 0.9 });
    repository.create.mockResolvedValue({ id: "KR-000001", confidence: 0.9 });
    const result = await service.intake({ sourceType: "text", content: "Forex is the global currency market." });
    expect(result.knowledgeRecordId).toBe("KR-000001");
    expect(result.status).toBe("Draft");
    expect(result.nextAction).toBe("Verification");
    expect(extractor.extract).toHaveBeenCalledTimes(1);
    expect(classifier.classify).toHaveBeenCalledTimes(1);
    expect(duplicateDetector.findDuplicates).toHaveBeenCalledTimes(1);
    expect(builder.build).toHaveBeenCalledTimes(1);
    expect(repository.create).toHaveBeenCalledTimes(1);
  });
});
