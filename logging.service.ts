import { Injectable, Logger } from "@nestjs/common";
import { EnterpriseLogContext, EnterpriseLogger } from "./logger.interface";

@Injectable()
export class LoggingService implements EnterpriseLogger {
  private readonly logger = new Logger("QRU");
  info(message: string, context?: EnterpriseLogContext): void { this.logger.log(this.format(message, context)); }
  warn(message: string, context?: EnterpriseLogContext): void { this.logger.warn(this.format(message, context)); }
  error(message: string, error?: unknown, context?: EnterpriseLogContext): void { this.logger.error(this.format(message, context), error instanceof Error ? error.stack : undefined); }
  audit(message: string, context?: EnterpriseLogContext): void { this.logger.log(this.format(`AUDIT: ${message}`, context)); }
  security(message: string, context?: EnterpriseLogContext): void { this.logger.warn(this.format(`SECURITY: ${message}`, context)); }
  private format(message: string, context?: EnterpriseLogContext): string { return JSON.stringify({ timestamp: new Date().toISOString(), message, ...context }); }
}
