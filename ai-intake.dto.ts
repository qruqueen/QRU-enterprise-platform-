export class AIIntakeDto {
  sourceType!: "text" | "markdown" | "pdf" | "transcript";
  content!: string;
}
