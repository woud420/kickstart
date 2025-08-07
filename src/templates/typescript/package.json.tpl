{
  "name": "{{SERVICE_NAME}}",
  "version": "0.1.0",
  "description": "{{SERVICE_NAME}} - A TypeScript service",
  "main": "dist/index.js",
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js",
    "test": "jest",
    "test:watch": "jest --watch",
    "lint": "eslint src/**/*.ts",
    "format": "prettier --write src/**/*.ts",
    "check": "tsc --noEmit && npm run lint && npm run test"
  },
  "dependencies": {
    "express": "^4.18.0",
    "cors": "^2.8.5",
    "helmet": "^7.1.0",
    "morgan": "^1.10.0",
    "dotenv": "^16.3.0"
  },
  "devDependencies": {
    "@types/express": "^4.17.0",
    "@types/cors": "^2.8.0",
    "@types/morgan": "^1.9.0",
    "@types/node": "^20.0.0",
    "@types/jest": "^29.5.0",
    "@types/supertest": "^6.0.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "eslint": "^8.0.0",
    "jest": "^29.7.0",
    "supertest": "^7.0.0",
    "ts-jest": "^29.1.0",
    "tsx": "^4.0.0",
    "typescript": "^5.0.0",
    "prettier": "^3.0.0"
  },
  "keywords": [
    "typescript",
    "nodejs",
    "express",
    "api"
  ]
}
