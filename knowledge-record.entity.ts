export enum KnowledgeStatus {
  DRAFT = "Draft",
  RESEARCH = "Research",
  VERIFICATION = "Verification",
  APPROVED = "Approved",
  MANUFACTURING = "Manufacturing",
  PUBLISHED = "Published",
  ARCHIVED = "Archived",
}

export class KnowledgeRecord {
  id!: string;
  version!: number;
  status!: KnowledgeStatus;
  title!: string;
  question!: string;
  simpleAnswer!: string;
  detailedExplanation!: string;
  qruTranslation!: string;
  examples: string[] = [];
  vocabulary: string[] = [];
  tags: string[] = [];
  references: string[] = [];
  confidence!: number;
  createdAt!: Date;
  updatedAt!: Date;
}
