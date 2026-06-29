# QRU Enterprise Platform™

Knowledge Manufacturing Operating System for QRU.

## EPI-002 — First Running Build

```bash
npm install
npm run build
npm run test
npm run start:dev
```

Health check:

```text
GET http://localhost:3000/health
```

AI Intake test:

```text
POST http://localhost:3000/ai/intake
```

```json
{
  "sourceType": "text",
  "content": "Forex is the global currency market where currencies are exchanged."
}
```

Recommended commit:

```text
feat(epi-002): initial running QRU platform
```
