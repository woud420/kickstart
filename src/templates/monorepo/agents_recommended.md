# Recommended Agent Workflow

Use these review lanes when evolving this workspace.

| Need | Agent | Expected output |
| --- | --- | --- |
| External contracts | `io-mapper` | Source-cited CLI, HTTP, files, config, and network surface |
| Architecture map | `mermaid-architect` | Mermaid diagrams and machine-readable component model |
| Infrastructure | `infra-architect-iac` | K8s and Terraform changes aligned with detected app needs |
| Data model | `data-modeler` | SQL schema, indexes, consistency tradeoffs, migration notes |
| Python implementation | `python-coder` | Typed Python modules and tests |
| Rust implementation | `rust-coder` | Layered Rust service or CLI code with tests |
| UI and TypeScript | `ui-agent` | Typed frontend/service code that matches existing conventions |
| Dependency map | `api-dependency-mapper` | Business and technical dependency graph before large changes |
| Security review | `security-pentester` | Prioritized vulnerabilities and remediation |
| Multi-step routing | `orchestrator-meta` | Agent plan and prompt handoffs |

## Missing Useful Lane

Add a C++ agent if C++ services become common. The generated stack supports C++20/CMake, but the local agent inventory does not currently include a dedicated C++ reviewer.

## Default Sequence

1. `io-mapper` after a service exposes a new interface.
2. `data-modeler` before schema or persistence changes.
3. Language-specific agent for implementation.
4. `infra-architect-iac` when runtime dependencies change.
5. `security-pentester` before release.
6. `mermaid-architect` after meaningful topology changes.
