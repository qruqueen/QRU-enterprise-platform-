import { Module } from "@nestjs/common";
import { ConfigurationModule } from "../config/config.module";
import { KnowledgeModule } from "../knowledge/knowledge.module";
import { LoggingModule } from "../logging/logging.module";
import { AIIntakeController } from "./ai-intake.controller";
import { AIIntakeService } from "./ai-intake.service";
import { ClassifierService } from "./classifier.service";
import { DuplicateDetectorService } from "./duplicate-detector.service";
import { ExtractorService } from "./extractor.service";
import { KnowledgeRecordBuilder } from "./knowledge-record.builder";

@Module({ imports: [ConfigurationModule, LoggingModule, KnowledgeModule], controllers: [AIIntakeController], providers: [AIIntakeService, ExtractorService, ClassifierService, DuplicateDetectorService, KnowledgeRecordBuilder], exports: [AIIntakeService] })
export class AIIntakeModule {}
