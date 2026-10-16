# Scaffold schema 4.0

The structural authority is [scaffold-4.0.schema.json](scaffold-4.0.schema.json),
generated from the TypedDicts in `src/generator/manifest_types.py` plus the
identity invariants in `src/generator/manifest_schema.py`. The shared inverse
uses that same schema through the Draft 2020-12 validator. The committed artifact
is checked against the typed source in tests. JSON Schema conditional semantics
follow the [official specification reference](https://json-schema.org/understanding-json-schema/reference/conditionals).

## Compatibility and cutover

Readers accept exactly 3.0, 3.1, 3.2 and 4.0. Fresh generation emits 4.0 after
the explicit, tested [manifest migration path](manifest-migration.md) is available.
Existing repositories migrate only through an explicit command; this does not
release a CLI or implement broader reconciliation.

Schema 4.0 removes `semantics`, `docs` and `capabilities`. `generated_by` preserves
the recorded producer; an explicitly unversioned `kickstart` marker remains
unknown provenance, never proof of a reproducible generated base. Non-system
projects require recorded language. Frameworks distinguish Python service output,
frontends and CLI frameworks; language-neutral systems omit language/framework.
The compatible CLI `cli_framework` field may remain, but must match `framework`.

`extensions.{database,cache,auth}` replaces the legacy
`capabilities.service_extensions` nesting. Backstage tags and generated extension
coverage checks understand both formats. No runtime semantics are added.

A Cloudflare Worker is `project.kind: service` with the single execution model
`cloudflare-worker`, platform `cloudflare-workers`, the `wrangler` artifact and a
Cloudflare provider target. Worker lifecycle defaults and documentation profiles
follow this execution model. TypeScript and Rust profiles remain distinct.
Legacy `worker` manifests retain their existing behavior.

## Unknown or conflicting metadata

Schema 4.0 rejects unknown properties, null optional values, missing identity and
conflicting representations instead of discarding them. Systems retain their
recorded composition fields and child-manifest globs. Optional legacy reads keep
the established compatibility behavior; the shared inverse is not a lossless
editor for arbitrary schema-3 extensions.

The migration refuses unknown fields and nonstandard legacy docs mappings that
cannot be represented after removing `docs`. It exposes missing language/framework
as unresolved inputs and preserves the source on failure. It does not infer inputs
from current application files or rewrite managed docs.

## Consumers

`adopt --check`, `plan`, Backstage export and generated-project evals recognize
the versioned format. A manifest-only Worker conversion can make the existing
contracts README's legacy `worker` label differ from the schema-4 `service` label;
docs planning reports that as content drift inside the owned fence. It does not
rewrite the README. User content outside ownership fences remains excluded.

Regenerate the schema artifact with:

```bash
PYTHONPATH=. poetry run python -c 'from src.generator.manifest_schema import manifest_v4_schema_json; print(manifest_v4_schema_json(), end="")' > docs/contracts/scaffold-4.0.schema.json
```
