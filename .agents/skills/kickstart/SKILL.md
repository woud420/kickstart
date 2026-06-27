---
name: kickstart
description: Scaffolds services, frontends, libraries, CLIs, and system repos with the installed kickstart binary. Use when asked to create, scaffold, generate, or start a service, project, frontend, library, CLI, system, or other starter repo.
---

# Kickstart

## Overview

Use the installed `kickstart` binary when asked to create, scaffold, generate, or start a service, frontend, library, CLI, or system repo. Treat the binary as the interface.

## Workflow

Confirm `kickstart` exists. Read `kickstart create --help` only when syntax is unclear. Generate with an explicit `--root`, then inspect `.kickstart/scaffold.json` and `AGENTS.md` before extending.

Common patterns:

```bash
kickstart create cli ops-tool --lang rust --root /private/tmp/kickstart-output
kickstart create service my-api --lang python --root /private/tmp/kickstart-output
kickstart create system platform --cloud aws --runtime kubernetes --knowledge none --root /private/tmp/kickstart-output
```

Use `create frontend NAME --root ...` for frontends and `create lib NAME --lang python|rust --root ...` for libraries.

## Rules

- Use `system` for aggregate repos; `mono` and `monorepo` are legacy aliases.
- Use `--gh` only when the user explicitly asks to create a GitHub repository.
- Keep generated output separate from unrelated worktrees unless given a destination.
- Do not commit generated projects unless the user explicitly asks.
- If an option is rejected, report the error and choose an alternative only with user consent.
- Cloudflare Workers are a Worker runtime, not Docker containers.
- Add CLI commands through the generated framework: clap for Rust, Typer for Python, oclif for TypeScript.
- Put CLI product behavior under `src/operations`; clients under `src/clients`; DTOs under `src/model`; output formatting under `src/output`; exit/error behavior under `src/error`.
- For Rust CLIs, keep `src/main.rs` as the only Rust file directly under `src/`.

## Validation

- The `kickstart create` command exits 0 and the project exists under the explicit `--root` path you passed.
- The generated repo contains the baseline scaffold contract: `.kickstart/scaffold.json` and `AGENTS.md`. Inspect both before extending; `scaffold.json` records what was generated (project kind, runtime, artifacts).
- If an option was rejected, the error was reported to the user instead of being silently worked around.

## Anti-Patterns

- Hand-rolling a scaffold by writing files directly when the `kickstart` binary is installed — the binary is the interface.
- Generating without an explicit `--root`, or dumping output into unrelated worktrees.
- Passing `--gh` when the user did not explicitly ask for a GitHub repository.
- Committing generated projects without an explicit request.
- Silently substituting an alternative when an option is rejected, instead of reporting the error and getting user consent.
- Modeling Cloudflare Workers as Docker containers.
- Wiring new CLI commands outside the generated framework (clap, Typer, oclif), or adding Rust files directly under `src/` beyond `src/main.rs`.

## Report Back

Report the exact command and output path. Read README/docs only when the next task needs deeper project context.
