import { Logger } from "@nestjs/common";
import { NestFactory } from "@nestjs/core";
import { AppModule } from "./app.module";

async function bootstrap(): Promise<void> {
  const app = await NestFactory.create(AppModule, { bufferLogs: true });
  const port = process.env.PORT ?? 3000;
  await app.listen(port);
  Logger.log(`QRU Enterprise Platform™ running on http://localhost:${port}`, "Bootstrap");
}

bootstrap().catch((error) => {
  Logger.error(error, "Application failed to start");
  process.exit(1);
});
