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
    "dev": "wrangler dev",
    "deploy": "wrangler deploy",
    "test": "vitest run",
    "typecheck": "tsc -p tsconfig.json --noEmit",
    "lint": "eslint .",
    "lint:fix": "eslint . --fix",
    "format": "prettier --write .",
    "format:check": "prettier --check ."
  },
  "devDependencies": {
    "@cloudflare/workers-types": "^4.20260405.1",
    "@eslint/js": "^9.18.0",
    "@typescript/native": "npm:typescript@{{ typescript_version }}",
    "@types/bun": "^1.3.0",
    "eslint": "^9.18.0",
    "prettier": "^3.4.2",
    "typescript": "npm:@typescript/typescript6@{{ typescript_compat_version }}",
    "typescript-eslint": "^8.20.0",
    "vitest": "^3.0.0",
    "wrangler": "^4.80.0"
  }
}
