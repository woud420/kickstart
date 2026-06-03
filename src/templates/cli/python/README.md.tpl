# {{service_name}}

Python CLI scaffold with Typer-backed commands and an agent-friendly modular layout.

## Development

```bash
make dev
make test
make check
make build
```

## Project Structure

```text
src/
├── main.py        # Process entrypoint only
├── cli/           # Typer app and command adapters
│   └── commands/  # Typer command functions
├── config/        # Configuration loading
├── clients/       # External API/client boundaries
├── model/         # DTOs and typed data boundaries
├── operations/    # Command use cases
├── output/        # Human and machine output formatting
└── error/         # Error types and exit codes
tests/
└── test_cli_smoke.py
```

Keep `src/main.py` small. Add Typer command adapters in `src/cli/commands`, put use-case behavior in `src/operations`, and keep transport-specific code in `src/clients`.
