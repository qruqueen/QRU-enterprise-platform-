import { HealthService } from "./health.service";

describe("HealthService", () => {
  it("returns healthy status", () => {
    const result = new HealthService().getHealth();
    expect(result.status).toBe("healthy");
    expect(result.application).toBe("QRU Enterprise Platform™");
  });
});
