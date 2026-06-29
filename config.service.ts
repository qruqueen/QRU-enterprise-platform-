import { Injectable } from "@nestjs/common";

@Injectable()
export class ConfigurationService {
  getPort(): number { return Number(process.env.PORT ?? 3000); }
  getApplicationVersion(): string { return process.env.APP_VERSION ?? "0.1.0-alpha"; }
  getDatabaseUrl(): string | undefined { return process.env.DATABASE_URL; }
  isProduction(): boolean { return process.env.NODE_ENV === "production"; }
}
