import { Injectable } from "@nestjs/common";

@Injectable()
export class HealthService {
  getHealth() {
    return {
      status: "healthy",
      application: "QRU Enterprise Platform™",
      version: process.env.APP_VERSION ?? "0.1.0-alpha",
      architecture: "EAB-001",
      timestamp: new Date().toISOString(),
    };
  }
}
