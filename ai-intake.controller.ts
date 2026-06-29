import { Body, Controller, HttpCode, HttpStatus, Post } from "@nestjs/common";
import { AIIntakeService } from "./ai-intake.service";
import { AIIntakeDto } from "./dto/ai-intake.dto";

@Controller("ai/intake")
export class AIIntakeController {
  constructor(private readonly aiIntakeService: AIIntakeService) {}
  @Post()
  @HttpCode(HttpStatus.CREATED)
  async createDraftKnowledgeRecord(@Body() request: AIIntakeDto) { return this.aiIntakeService.intake(request); }
}
