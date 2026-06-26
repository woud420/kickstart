---
name: kickstart
description: Use the installed kickstart binary whenever an agent is asked to create or scaffold a service, project, frontend, library, CLI, system, or other starter repo.
---

# Kickstart

## Use When

Use the installed `kickstart` binary when asked to create, scaffold, generate, or start a service, frontend, library, CLI, or system repo. Treat the binary as the interface.

## Hot Path

Confirm `kickstart` exists. Read `kickstart create --help` only when syntax is unclear. Generate with an explicit `--root`, then inspect `.kickstart/scaffold.json` and `AGENTS.md` before extending.

Common patterns:

```bash
kickstart create cli ops-tool --lang rust --root /tmp/kickstart-output
kickstart create service my-api --lang python --root /tmp/kickstart-output
kickstart create system platform --cloud aws --runtime kubernetes --knowledge none --root /tmp/kickstart-output
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

## Report Back

Report the exact command and output path. Read README/docs only when the next task needs deeper project context.
