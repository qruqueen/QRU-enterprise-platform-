import { Module } from "@nestjs/common";
import { KnowledgeRepository } from "./repositories/knowledge.repository";

@Module({ providers: [KnowledgeRepository], exports: [KnowledgeRepository] })
export class KnowledgeModule {}
