# {{service_name}}

Rust CLI scaffold with clap-backed commands and an agent-friendly modular layout.

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
├── main.rs        # Process entrypoint only
├── cli/           # clap command types and dispatch
├── config/        # Configuration loading
├── clients/       # External API/client boundaries
├── model/         # DTOs and typed data boundaries
├── operations/    # Command use cases
├── output/        # Human and machine output formatting
└── error/         # Error types and exit codes
tests/
└── cli_smoke.rs
```

Keep `src/main.rs` small. Add clap command adapters in `src/cli`, put use-case behavior in `src/operations`, and keep transport-specific code in `src/clients`.
