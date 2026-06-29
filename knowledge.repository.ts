import { Injectable } from "@nestjs/common";
import { KnowledgeRecord, KnowledgeStatus } from "../entities/knowledge-record.entity";

@Injectable()
export class KnowledgeRepository {
  private readonly records = new Map<string, KnowledgeRecord>();
  async create(record: KnowledgeRecord): Promise<KnowledgeRecord> { this.records.set(record.id, record); return record; }
  async findById(id: string): Promise<KnowledgeRecord | null> { return this.records.get(id) ?? null; }
  async update(record: KnowledgeRecord): Promise<KnowledgeRecord> { record.updatedAt = new Date(); this.records.set(record.id, record); return record; }
  async archive(id: string): Promise<void> { const record = this.records.get(id); if (record) { record.status = KnowledgeStatus.ARCHIVED; record.updatedAt = new Date(); this.records.set(id, record); } }
  async search(query: string): Promise<KnowledgeRecord[]> { const q = query.toLowerCase(); return [...this.records.values()].filter((r) => r.title.toLowerCase().includes(q) || r.tags.some((t) => t.toLowerCase().includes(q))); }
  async list(): Promise<KnowledgeRecord[]> { return [...this.records.values()]; }
}
