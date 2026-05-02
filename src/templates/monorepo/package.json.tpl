{
  "name": "{{ monorepo_name }}",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "packageManager": "bun@1.3.0",
  "engines": {
    "bun": ">=1.3.0 <2"
  },
  "workspaces": {
    "packages": [
      "apps/*",
      "packages/*",
      "services/*"
    ]
  },
  "scripts": {
    "dev": "turbo run dev --parallel",
    "build": "turbo run build",
    "test": "turbo run test",
    "typecheck": "turbo run typecheck",
    "lint": "turbo run lint",
    "format": "prettier --write .",
    "ci": "turbo run typecheck test lint",
    "clean": "turbo run clean"
  },
  "devDependencies": {
    "@types/bun": "^1.3.0",
    "eslint": "^9.0.0",
    "prettier": "^3.0.0",
    "turbo": "^2.0.0",
    "typescript": "^5.0.0",
    "vitest": "^3.0.0"
  }
}
