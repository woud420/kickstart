# CLI Framework Research

Checked: 2026-05-07

## Bottom Line

Yes, TypeScript CLIs should follow oclif by default.

Python has similar pieces, but not one exact oclif-equivalent that should be the default for every project. The practical default should be Typer, because it gives agents a type-hint-driven command surface, subcommands, generated help, completion support, packaging guidance, and direct CLI test helpers while staying close to normal Python functions. Click is the mature lower-level layer underneath Typer and should remain the fallback when a project needs lower-level command loading or custom behavior. Python plugin application frameworks such as cliff and Cement are real analogues to oclif's app/plugin model, but they are heavier and should be explicit profiles, not the default.

Rust should use clap derive. The current modular Rust CLI direction is structurally right, but a custom parser is the wrong default. clap is the ecosystem standard for production Rust CLIs, and `assert_cmd` gives the generated project the CLI smoke test shape agents expect.

The improvement is therefore: keep the same conceptual boundaries across Rust, Python, and TypeScript, but make the command layer framework-backed and idiomatic per language.

## Evidence From Official Docs

### TypeScript: Use oclif

oclif describes itself as a Node.js framework for CLIs, with a generator that creates a TypeScript project and command files under `src/commands`. It supports command classes, flags, arguments, hooks, plugins, command discovery strategies, a base command class, JSON output, autocompletion, installers, and testing helpers.

Sources:

- [oclif introduction](https://oclif.io/docs/introduction/)
- [oclif commands](https://oclif.io/docs/commands/)
- [oclif features](https://oclif.io/docs/features/)
- [oclif command discovery strategies](https://oclif.io/docs/command_discovery_strategies/)
- [oclif custom base class](https://oclif.io/docs/base_class/)
- [oclif ESM guide](https://oclif.io/docs/esm/)
- [oclif testing](https://oclif.io/docs/testing/)

Recommendation:

- Make oclif the default TypeScript CLI framework.
- Use `src/commands/**` as the TypeScript command adapter layer instead of forcing those files into `src/cli`.
- Keep shared application boundaries under `src/config`, `src/clients`, `src/model`, `src/operations`, `src/output`, and `src/error`.
- Generated oclif commands should parse framework flags/args and call operations. They should not contain product logic.
- Use an oclif base command for global flags, config loading, output mode, and shared error handling.

### Python: Use Typer By Default, Keep Click Close

Typer is built around Python type hints and supports command functions, command groups, automatic help, terminal completion, packaging, and tests with `typer.testing.CliRunner`. Its docs also state that Typer is based on Click. Click's own docs emphasize composable command groups, arbitrary nesting, automatic help generation, lazy subcommand loading, and direct test helpers.

Sources:

- [Typer homepage](https://typer.tiangolo.com/)
- [Typer subcommands](https://typer.tiangolo.com/tutorial/subcommands/)
- [Typer testing](https://typer.tiangolo.com/tutorial/testing/)
- [Typer packaging](https://typer.tiangolo.com/tutorial/package/)
- [Click homepage](https://click.palletsprojects.com/en/stable/)
- [Click complex applications](https://click.palletsprojects.com/en/stable/complex/)
- [Click testing](https://click.palletsprojects.com/en/stable/testing/)

Recommendation:

- Make Typer the default Python CLI framework.
- Use `src/cli/app.py` and `src/cli/commands/*.py` for the command adapter layer.
- Use `typer.testing.CliRunner` for generated smoke tests.
- Keep Click as the lower-level option when a CLI needs custom command loading or sharper control over contexts.
- Do not default to a fully plugin-oriented Python framework unless the user requests plugin distribution, interactive shells, or command packs.

### Python App/Plugin Profiles: cliff And Cement

cliff is a Python framework for multi-level command programs. Its docs describe plugin-loaded subcommands, output formatters, command managers, command hooks, and entry-point registration. Cement is a broader Python application framework focused on CLIs, with handlers for config, arguments, logging, plugins, output, templates, controllers, hooks, and extensions.

Sources:

- [cliff overview](https://docs.openstack.org/cliff/latest/)
- [cliff introduction](https://docs.openstack.org/cliff/latest/user/introduction.html)
- [cliff demo application](https://docs.openstack.org/cliff/latest/user/demoapp.html)
- [Cement developer guide](https://docs.builtoncement.com/)
- [Cement application plugins](https://docs.builtoncement.com/core-foundation/plugins)

Recommendation:

- Add these only as later explicit profiles, for example `--cli-framework cliff` or `--profile plugin-app`.
- Use cliff when Python command plugins and output formatters are first-class requirements.
- Use Cement only for larger Python CLI applications that need a full app framework, not for ordinary generated CLIs.

### Rust: Use clap Derive

clap's official docs describe it as a command-line argument parser for Rust and point directly to derive and builder APIs. The current crate docs call out polished CLI behavior, help generation, suggested fixes, colored output, shell completions, and parse performance. `assert_cmd` exists specifically to simplify integration testing of CLIs by finding a crate binary and asserting on exit status, stdout, and stderr.

Sources:

- [clap crate docs](https://docs.rs/clap/latest/clap/)
- [assert_cmd crate docs](https://docs.rs/assert_cmd/latest/assert_cmd/)

Recommendation:

- Make clap derive the default Rust CLI framework.
- Keep `src/main.rs` thin.
- Put `#[derive(Parser, Subcommand, Args)]` types in `src/cli/args.rs`.
- Put command-to-operation routing in `src/cli/dispatch.rs`.
- Keep domain work under `src/operations`, API code under `src/clients`, DTOs under `src/model`, output formatting under `src/output`, and user-facing errors under `src/error`.
- Add generated `assert_cmd` tests for `--help`, `--version`, and `check`.

## Cross-Language Scaffold Shape

The mistake would be to make every language use the same files. The right target is the same architecture with language-native command surfaces.

| Language | Default framework | Command adapter root | Why |
| --- | --- | --- | --- |
| Rust | clap derive | `src/cli/args.rs`, `src/cli/dispatch.rs` | Best delivery target, fast binary, standard Rust CLI parser. |
| TypeScript | oclif | `src/commands/**`, plus optional `src/base-command.ts` | Standard TypeScript CLI app framework with generator, plugins, hooks, JSON, testing, and packaging conventions. |
| Python | Typer | `src/cli/app.py`, `src/cli/commands/*.py` | Type-hint-based, agent-readable, Click-backed, easy to test and package. |

Shared boundaries across all three:

- `config`: environment, files, defaults, and validation.
- `clients`: external service clients and transport concerns.
- `model`: DTOs, command input/output shapes, and API response types.
- `operations`: product use cases. Command adapters call these.
- `output`: table, text, JSON, and quiet/verbose output behavior.
- `error`: typed errors, user-facing messages, exit-code mapping.

## Scaffold Contract Changes

Add explicit framework metadata so agents know how to extend the generated CLI:

```json
{
  "project": {
    "kind": "cli",
    "architecture": "modular-cli",
    "cli_framework": "clap",
    "command_root": "src/cli",
    "entrypoint": "src/main.rs",
    "operation_root": "src/operations"
  }
}
```

For TypeScript, `cli_framework` should be `oclif` and `command_root` should be `src/commands`. For Python, `cli_framework` should be `typer` and `command_root` should be `src/cli/commands`.

The generated agent docs should also say:

- Treat framework command files as adapters.
- Put product behavior in operations.
- Do not bypass the framework parser with custom argv parsing.
- Add new commands using the framework's native pattern.
- Keep command smoke tests in the generated test suite.

## Implementation Status

Implemented in kickstart:

- `cli_framework` defaults by language: `clap`, `typer`, and `oclif`.
- TypeScript CLI templates use oclif command discovery, `bin/dev.js`, `bin/run.js`, `src/base-command.ts`, and `src/commands`.
- Python CLI templates use Typer in `src/cli/app.py`, command modules in `src/cli/commands`, and `typer.testing.CliRunner` tests.
- Rust CLI templates use clap derive in `src/cli` and `assert_cmd` tests.
- `.kickstart/scaffold.json` records `project.cli_framework`, `project.command_root`, `project.entrypoint`, and `project.operation_root`.
- Generated smoke tests cover `check`, help, and version behavior for the framework-backed command surface.

## Decision

Rust remains the preferred delivery language when performance, single-binary distribution, and long-term operator experience matter. That preference should not force TypeScript and Python to imitate Rust's file layout. TypeScript should look like a professional oclif CLI. Python should look like a professional Typer CLI. Rust should look like a professional clap CLI.

The shared contract is architectural, not textual: commands are adapters, operations own behavior, clients own transport, models own data boundaries, output owns presentation, and errors own exit behavior.

## Implementation Contract

The scaffold encodes this decision in `.kickstart/scaffold.json` with `project.cli_framework`, `project.command_root`, `project.entrypoint`, and `project.operation_root`. Generated command files are thin framework adapters that call `src/operations`; they should not reintroduce custom argv parsing as the default path.
