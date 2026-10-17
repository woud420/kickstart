# Kickstart self-adoption

Date: 2026-10-17

Kickstart records its own existing repository as a manually adopted Python CLI
using schema 4.0. The manifest enables the same read-only adoption and derived
export consumers used by generated repositories. It does not claim that this
repository was generated from a current CLI template.

## Recorded identity and lifecycle

- `project.name` matches the package name in `pyproject.toml`.
- The project is a Python `cli`, using Typer and the existing `modular-cli`
  vocabulary. Its command adapters live under `src/cli`; its entrypoint is
  `src/cli/main.py`, matching the package script `src.cli.main:app`.
- `operation_root` is omitted: generation, stack policy, telemetry and other
  behavior span existing modules rather than one generated `src/operations`
  directory. The repository's authored agent map remains the detailed map.
- Execution is a local CLI, with a Python package artifact. Optional binary
  packaging is an existing build target, not a new artifact field or release.
- Lifecycle commands name existing Makefile targets: `make install`,
  `make tests`, `make check`, `make build` and `make run`. No deployment
  command or provider target is claimed.
- `generated_by` is `unknown`. The manifest is authored for adoption, so a
  current generator version or revision would invent historical provenance.
- No service extension or external knowledge adapter is enabled.

Schema 4.0 is already supported on master. The earlier choice between authoring
3.0 as a migration fixture and waiting for 4.0 therefore resolves to 4.0;
legacy migration coverage remains in its dedicated fixtures.

## Ownership boundary

The repository keeps its existing authored documentation. Recorded documentation
and the custom CI workflow are seeds; other unlisted files also stay user-owned.
No ownership fences are inserted and no authored guidance is moved into a
regenerable region. The manifest and Makefile have the existing structural
`manifest-shape` and `make-check` roles.

Adoption now uses schema-4 ownership when checking fence readiness: only recorded
managed regions require fences. An explicitly empty map claims no managed
regions. A missing ownership map retains the legacy full-projection fence check,
and all Level 1 artifact requirements still apply. Fresh generators continue to
record their managed regions, so their fence requirements remain intact.

This is a declared adoption boundary, not a way to suppress missing fences in a
managed scaffold. Ownership must describe who maintains each file. A successful
check establishes conformance and readiness for the recorded scope; it does not
certify the contents of user-owned prose.

`kickstart plan --json` still enumerates the standard projection targets and may
show authored files as unfenced or missing. `kickstart plan --ownership --json`
inspects the recorded ownership boundary. Neither command rewrites those files.

## Enforcement and consumers

`make adopt-check` requires the checked-in manifest and runs the repository's
read-only adoption check. It is included in `make check`. The explicit file
requirement matters because ordinary adoption intentionally allows a fully
conformant repository without any manifest.

Integration tests validate manifest identity against package metadata, dry-run
every recorded lifecycle target, check read-only adoption and run the Backstage
exporter on a scratch copy. Exporting twice must produce the same bytes. The
result is a `Component` named `kickstart` with type `tool`; anonymous owner and
experimental lifecycle defaults are retained for this structural validation.
A real catalog registration still needs its own owner/lifecycle decision.

The scratch catalog is not checked in or registered with an external service.
The scope is self-adoption and consumer validation; automatic adoption writes
and generated documentation taxonomy changes remain separate work.
