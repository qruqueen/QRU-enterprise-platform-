import { Module } from "@nestjs/common";
import { AIIntakeModule } from "./ai-intake/ai-intake.module";
import { ConfigurationModule } from "./config/config.module";
import { HealthModule } from "./health/health.module";
import { KnowledgeModule } from "./knowledge/knowledge.module";
import { LoggingModule } from "./logging/logging.module";

@Module({
  imports: [ConfigurationModule, LoggingModule, HealthModule, KnowledgeModule, AIIntakeModule],
})
export class AppModule {}
