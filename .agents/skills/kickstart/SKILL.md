---
name: kickstart
description: Use the installed kickstart binary whenever an agent is asked to create or scaffold a service, project, frontend, library, CLI, system, or other starter repo.
---

# Kickstart

## Overview

Use this skill when a user asks an agent to create, scaffold, generate, or start a project such as a service, frontend, library, CLI, or system repo.

Run the installed `kickstart` binary. Treat the binary as the interface.

## Preflight

Confirm the binary exists before generating. Read help when option syntax is unclear.

```bash
command -v kickstart
kickstart version
kickstart create --help
```

If `kickstart` is not on `PATH`, report that clearly and ask the user which installed binary path to use.

## Generate

Use `kickstart create` for scaffold requests. Use an explicit output root so the destination is predictable.

Common patterns:

```bash
kickstart create service my-api --lang python --root /private/tmp/kickstart-output
kickstart create service edge-api --lang typescript --runtime cloudflare-workers --root /private/tmp/kickstart-output
kickstart create frontend web --root /private/tmp/kickstart-output
kickstart create lib core-lib --lang python --root /private/tmp/kickstart-output
kickstart create cli ops-tool --lang rust --root /private/tmp/kickstart-output
kickstart create system platform --cloud aws --runtime kubernetes --knowledge none --root /private/tmp/kickstart-output
```

Use `system` for aggregate repos. `mono` and `monorepo` are legacy aliases and should not be the default in new commands.

Only use `--gh` when the user explicitly asks to create a GitHub repository.

## Guardrails

- Do not infer unsupported option combinations. If the binary rejects an option, report the error and pick a supported alternative only with user consent.
- Cloudflare Workers are a Worker runtime, not Docker containers.
- Keep generated output separate from unrelated worktrees unless the user gives a specific destination.
- Do not commit generated projects unless the user explicitly asks.

## Report Back

Report the exact command run and output path.
