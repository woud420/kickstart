# {{service_name}}

TypeScript CLI scaffold with oclif-backed commands, Bun package management, and an agent-friendly modular layout.

## Development

```bash
make dev
make test
make check
make build
```

## Project Structure

```text
bin/
├── dev.js         # oclif development entrypoint
└── run.js         # oclif production entrypoint
src/
├── base-command.ts  # Shared oclif command base
├── commands/      # oclif command adapters
├── config/        # Configuration loading
├── clients/       # External API/client boundaries
├── model/         # DTOs and typed data boundaries
├── operations/    # Command use cases
├── output/        # Human and machine output formatting
└── error/         # Error types and exit codes
tests/
└── cli-smoke.test.ts
```

Add oclif command adapters in `src/commands`, put use-case behavior in `src/operations`, and keep transport-specific code in `src/clients`.
