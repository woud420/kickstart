{
  "name": "{{ package_name }}",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "packageManager": "bun@{{ bun_version }}",
  "engines": {
    "bun": ">={{ bun_version }} <2"
  },
  "workspaces": {
    "packages": [
      "apps/*",
      "packages/*"
    ]
  },
  "scripts": {
    "dev": "make dev",
    "build": "make build",
    "test": "make test",
    "typecheck": "make typecheck",
    "check": "make check",
    "lint": "make docs-check",
    "format": "prettier --write .",
    "ci": "make check",
    "clean": "find . -name node_modules -type d -prune -exec rm -rf {} +"
  },
  "devDependencies": {
    "@types/bun": "^1.3.0",
    "prettier": "^3.0.0",
    "turbo": "^2.0.0",
    "typescript": "^5.0.0"
  }
}
