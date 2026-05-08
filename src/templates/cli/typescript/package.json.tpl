{
  "name": "{{ package_name }}",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "packageManager": "bun@1.3.0",
  "bin": {
    "{{ package_name }}": "./bin/run.js"
  },
  "engines": {
    "node": ">=20",
    "bun": ">=1.3.0 <2"
  },
  "scripts": {
    "dev": "node ./bin/dev.js check",
    "build": "tsc -p tsconfig.build.json",
    "start": "node ./bin/run.js check",
    "test": "vitest run tests/cli-smoke.test.ts",
    "typecheck": "tsc -p tsconfig.json --noEmit"
  },
  "dependencies": {
    "@oclif/core": "^4.0.0"
  },
  "devDependencies": {
    "@oclif/test": "^4.0.0",
    "@types/bun": "^1.3.0",
    "@types/node": "^22.13.1",
    "tsx": "^4.20.0",
    "typescript": "^5.7.3",
    "vitest": "^3.0.5"
  },
  "oclif": {
    "bin": "{{ package_name }}",
    "dirname": "{{ package_name }}",
    "commands": "./dist/commands",
    "topicSeparator": " "
  }
}
