{
  "name": "{{ package_name }}",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "packageManager": "bun@{{ bun_version }}",
  "engines": {
    "bun": ">={{ bun_version }} <2"
  },
  "scripts": {
    "dev": "bun --watch src/main.ts",
    "build": "tsc -p tsconfig.build.json",
    "start": "bun dist/main.js",
    "test": "vitest run tests/health.test.ts",
    "typecheck": "tsc -p tsconfig.json --noEmit",
    "lint": "eslint .",
    "lint:fix": "eslint . --fix",
    "format": "prettier --write .",
    "format:check": "prettier --check ."
  },
  "dependencies": {
    "@hono/node-server": "^1.13.7",
    "@hono/zod-validator": "^0.4.2",
    "hono": "^4.6.13",
{% if database == "postgres" %}
    "pg": "^8.13.1",
{% endif %}
    "pino": "^9.6.0",
    "zod": "^3.24.2"
  },
  "devDependencies": {
    "@eslint/js": "^9.18.0",
    "@types/bun": "^1.3.0",
    "@types/node": "^22.13.1",
{% if database == "postgres" %}
    "@types/pg": "^8.11.11",
{% endif %}
    "eslint": "^9.18.0",
    "prettier": "^3.4.2",
    "typescript": "^5.7.3",
    "typescript-eslint": "^8.20.0",
    "vitest": "^3.0.5"
  }
}
