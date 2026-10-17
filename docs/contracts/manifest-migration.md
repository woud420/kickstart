# Scaffold manifest migration

`kickstart migrate [repo]` plans a migration to schema 4.0 without writing.
`--apply` explicitly applies a fully resolved plan. It writes only
`.kickstart/scaffold.json`; application files, managed docs, Makefiles and CI
workflows are not repaired or adopted by this command.

```bash
kickstart migrate ./old-repo --json
kickstart migrate ./old-repo --language python --framework minimal --json
kickstart migrate ./old-repo --language python --framework minimal --apply
```

Review the plan's diff and diagnostics first. To bind a later apply invocation to
that exact source, pass the `source_sha256` from its JSON report:

```bash
kickstart migrate ./old-repo --apply --language python --framework minimal --expected-sha256 <reviewed-source-sha256>
```

## Resolution policy

Migrations support generated schemas 3.0, 3.1 and 3.2. A valid 4.0 manifest is
already migrated and is left byte-for-byte unchanged. Fresh generation now emits
4.0; [the format contract](scaffold-schema-4.md) and
[structural schema](scaffold-4.0.schema.json) define the target.

Explicit recorded identity is preserved. Fixed frontend choices, native CLI
frameworks and the language recorded in library/CLI package metadata can resolve
missing fields unambiguously. Remaining service/Worker language requires
`--language`; missing Python service framework requires `--framework fastapi`
or `--framework minimal`. Overrides may resolve missing data or repeat recorded
values; conflicting values block migration. The command never guesses from
`package.json`, source files or another component's toolchain.

Recorded generator identity is preserved. A canonical version-pinned Kickstart
semantics URL can recover an otherwise unversioned `generated_by`; conflicting
recorded versions block migration. If no release can be recovered, the target
keeps the explicit `kickstart` marker and reports a nonblocking
`unknown-provenance` diagnostic. It never substitutes the installed CLI release.
That marker is not a historical generated base or proof of reproducibility.

Unknown fields, malformed values, nonstandard docs mappings and custom semantics
references block conversion instead of being discarded. Required scaffold choices
must be present; missing system composition is unresolved rather than inferred
from the current directory tree. Review or explicitly correct that source metadata
before retrying. The original file is preserved while the plan is blocked.

## Apply contract

The typed plan captures source bytes and file identity. Apply checks that snapshot
before preparing a temporary file and again immediately before atomically replacing
the manifest. A detected concurrent change is preserved and requires a new plan.
The optional reviewed-source hash also protects separate CLI plan/apply invocations.
Symlinked manifests and symlinked `.kickstart` directories are refused. Successful
application preserves file permissions and is deterministic and idempotent;
reapplying the same target does not rewrite it. Write/replacement errors preserve
the original manifest and remove the temporary file when the filesystem permits.

The migration drops the known constant `docs` map and `semantics` after their useful
provenance has been preserved, flattens `capabilities.service_extensions` into
`extensions`, and converts the legacy Worker kind into a service execution profile.
It does not invent historical ownership or original-file hashes. A migrated
TypeScript Worker's old fenced contracts README may report the `worker` label as
drift under `kickstart plan`; migration does not rewrite that document.

Exit codes: 0 for a ready plan or successful/unchanged apply; 1 for unresolved or
invalid metadata; 2 for an unusable target or failed apply. JSON reports include
readiness, diagnostics, source hash, diff and action.
