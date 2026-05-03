{
  "name": "{{ package_name }}",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "packageManager": "bun@1.3.0",
  "engines": {
    "bun": ">=1.3.0 <2"
  },
  "scripts": {
    "dev": "bun --watch src/main.ts",
    "build": "tsc -p tsconfig.build.json",
    "start": "bun dist/main.js",
    "test": "vitest run tests/health.test.ts",
    "typecheck": "tsc -p tsconfig.json --noEmit"
  },
  "dependencies": {
    "@fastify/helmet": "^12.0.1",
    "fastify": "^5.2.1",
    "pino": "^9.6.0",
    "zod": "^3.24.2"
  },
  "devDependencies": {
    "@types/bun": "^1.3.0",
    "@types/node": "^22.13.1",
    "typescript": "^5.7.3",
    "vitest": "^3.0.5"
  }
}
