# Kickstart Token Savings Evidence

Date: 2026-05-08

## Decision

Keep the kickstart skill short and treat kickstart as a deterministic create-once scaffold tool.
The useful operating model is:

1. Load the skill.
2. Run one or more explicit `kickstart create ... --root ...` commands.
3. Inspect `.kickstart/scaffold.json` and `AGENTS.md` before extending.
4. Read generated README/docs only when deeper context is needed.

This keeps the fixed prompt cost low while preserving the scaffold contract that lets agents avoid hand-authoring boilerplate.

## Method

The evidence run generated 18 use cases twice under `/tmp` and compared each pair by file count, byte count, line count, and a tree SHA-256 over relative paths plus file content.

Token savings were estimated with a deterministic proxy:

```text
estimated tokens = ceil(UTF-8 text characters / 4)
```

The baseline is all generated UTF-8 text files under the measured project root. That is a conservative lower bound for what an agent would need to produce or review when hand-authoring the same scaffold.

The measured kickstart contexts were:

- create-only: optimized skill text plus exact command text
- minimal orientation: skill plus command text plus generated `.kickstart/scaffold.json` and `AGENTS.md`
- full orientation: skill plus command text plus README/docs entrypoints

The raw report was generated at `/tmp/kickstart-savings-matrix.xYLb8V/savings-matrix.json`.
The generated project outputs were intentionally kept under `/tmp` and should not be committed.

## Skill Cost

The optimized skill reduced fixed skill cost from 739 estimated tokens to 506 estimated tokens.

| Skill | Bytes | Lines | Estimated Tokens |
|---|---:|---:|---:|
| Previous | 2,954 | 60 | 739 |
| Optimized | 2,024 | 40 | 506 |

Savings: 233 estimated tokens per skill load, or 31.5%.

## Matrix Results

All 18 use cases were deterministic across paired runs.

Average savings:

- create-only: 74.8%
- minimal orientation: 43.5%

| Case | Files | Full Tokens | Create-Only Savings | Minimal Orientation Savings |
|---|---:|---:|---:|---:|
| `lib_rust` | 11 | 1,007 | 46.8% | -13.3% |
| `service_rust_minimal` | 17 | 1,151 | 53.2% | -0.6% |
| `lib_python` | 12 | 1,197 | 55.1% | 4.5% |
| `service_rust_cache_auth` | 21 | 1,621 | 66.2% | 26.7% |
| `frontend_react` | 17 | 1,712 | 68.8% | 32.1% |
| `worker_rust_cloudflare` | 15 | 1,768 | 69.1% | 33.0% |
| `service_typescript_minimal` | 19 | 1,943 | 72.1% | 40.2% |
| `cli_rust` | 22 | 2,020 | 73.5% | 40.9% |
| `service_typescript_postgres` | 21 | 2,206 | 75.2% | 46.3% |
| `worker_typescript_cloudflare` | 15 | 2,297 | 76.0% | 41.7% |
| `cli_python` | 24 | 2,313 | 76.7% | 47.9% |
| `cli_typescript` | 25 | 2,422 | 77.7% | 50.4% |
| `service_python_minimal` | 39 | 2,973 | 81.8% | 61.0% |
| `service_python_full` | 42 | 3,969 | 86.1% | 69.8% |
| `system_cloudflare_workers` | 33 | 5,390 | 89.7% | 75.4% |
| `system_aws_kubernetes` | 41 | 5,711 | 90.4% | 77.0% |
| `composite_system_frontend_backend` | 98 | 10,640 | 94.1% | 74.9% |
| `composite_system_two_clis` | 88 | 11,165 | 94.4% | 75.6% |

## Interpretation

Kickstart reliably saves tokens for scaffold creation. The savings grow with scaffold size:

- Small libraries and minimal Rust services save tokens when the agent only needs creation, but metadata inspection can cost as much as reading the tiny generated project.
- CLIs, TypeScript services, Python services, Workers, systems, and composite systems show meaningful savings even after minimal orientation.
- Composite systems are the strongest fit because one short command sequence replaces a large amount of repeated project structure and documentation.

The tool is deterministic for fresh generation. It is safe on repeat because existing target directories are refused, but it is not yet a merge-style idempotent reconciler.

## Follow-Ups

- Add a checked-in eval script if token savings becomes a release criterion.
- Add explicit `plan` or `dry-run` output if future agents need deterministic previews without creating files.
- Add a merge/converge mode only if kickstart should become an idempotent repo reconciler instead of a create-once scaffold tool.
