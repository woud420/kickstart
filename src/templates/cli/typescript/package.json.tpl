{
  "name": "{{ package_name }}",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "packageManager": "bun@{{ bun_version }}",
  "bin": {
    "{{ package_name }}": "./bin/run.js"
  },
  "engines": {
    "node": ">=20",
    "bun": ">={{ bun_version }} <2"
  },
  "scripts": {
    "dev": "node ./bin/dev.js check",
    "build": "tsc -p tsconfig.build.json",
    "start": "node ./bin/run.js check",
    "test": "vitest run tests/cli-smoke.test.ts",
    "typecheck": "tsc -p tsconfig.json --noEmit",
    "lint": "eslint .",
    "lint:fix": "eslint . --fix",
    "format": "prettier --write .",
    "format:check": "prettier --check ."
  },
  "dependencies": {
    "@oclif/core": "^4.0.0"
  },
  "devDependencies": {
    "@eslint/js": "^9.18.0",
    "@oclif/test": "^4.0.0",
    "@types/bun": "^1.3.0",
    "@types/node": "^22.13.1",
    "eslint": "^9.18.0",
    "prettier": "^3.4.2",
    "tsx": "^4.20.0",
    "typescript": "^5.7.3",
    "typescript-eslint": "^8.20.0",
    "vitest": "^3.0.5"
  },
  "oclif": {
    "bin": "{{ package_name }}",
    "dirname": "{{ package_name }}",
    "commands": "./dist/commands",
    "topicSeparator": " "
  }
}
