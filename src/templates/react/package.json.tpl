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
    "dev": "vite --host 0.0.0.0",
    "build": "tsc -b && vite build",
    "preview": "vite preview --host 0.0.0.0",
    "test": "vitest run tests/App.test.tsx",
    "typecheck": "tsc -b --noEmit",
    "lint": "eslint .",
    "lint:fix": "eslint . --fix",
    "format": "prettier --write .",
    "format:check": "prettier --check ."
  },
  "dependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  },
  "devDependencies": {
    "@eslint/js": "^9.18.0",
    "@types/bun": "^1.3.0",
    "@types/react": "^18.0.0",
    "@types/react-dom": "^18.0.0",
    "@vitejs/plugin-react": "^4.0.0",
    "eslint": "^9.18.0",
    "eslint-plugin-react-hooks": "^5.1.0",
    "prettier": "^3.4.2",
    "typescript": "^5.0.0",
    "typescript-eslint": "^8.20.0",
    "vite": "^5.0.0",
    "vitest": "^3.0.0"
  }
}
