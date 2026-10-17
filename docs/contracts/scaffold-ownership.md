# Persisted scaffold ownership

Fresh schema-4 generation records an `ownership` object keyed by safe relative
POSIX paths. Each compact typed tag identifies one generated artifact's scope:

```json
{
  "AGENTS.md": "agent-map",
  "Makefile": "make-check",
  "docs/architecture/README.md": "architecture-readme",
  "src/main.py": "seed"
}
```

| Tags | Classification | Bounded check |
| --- | --- | --- |
| `seed` | Generated once, project-owned | Excluded from inspection |
| `agent-map`, `claude-pointer`, `agents-skills-readme`, `contracts-readme`, `operations-readme`, `decisions-readme` | Managed fenced region | Compare only the named fence with the current standard's render |
| `architecture-readme` | Managed fenced region | Verify fence presence; title/directory render inputs are not recorded |
| `make-check` | Co-owned structural artifact | Check a simple literal `check` target declaration, including target lists |
| `workflow-presence` | Co-owned structural artifact | Verify file presence, UTF-8 readability and nonempty content |
| `manifest-shape` | Tool-state structural artifact | Validate the manifest's current schema |

The shared `managed_artifacts.py` registry supplies approved paths, fence IDs and
comparison policy to generation, the schema and the consumer. The schema rejects
unsupported tags, unsafe paths, mismatched region identities and promotion of
application files into managed regions. A tag may be changed to `seed` to exclude
a path from this scoped inspection; removing an entry also removes it from scope.

## Persistence boundary

The generator builds a typed deterministic plan from successful template/content
write targets and the generated skills link, after language and extension setup.
It does not scan existing files to decide ownership. The final manifest is written
before success or GitHub creation; failure to persist it fails generation.
Generated application code, tests, README prose, deployment configurations and other
outputs outside the declared envelope are seeds. Each project manifest scopes its
own generated artifacts; system roots do not acquire ownership of child projects.

Ownership is optional for older schema-4 manifests. Migration from 3.x leaves it
unrecorded. Current user files, even when fenced, do not establish historical
ownership, generated bases or original-file hashes. No such hashes are persisted.

## Read-only consumer

```bash
kickstart plan ./repo --ownership
kickstart plan ./repo --ownership --json
```

This mode reads the stored classification and checks only declared non-seed
artifacts. It excludes seed contents, unlisted files and user text outside named
fences from comparisons. Owned targets that resolve outside the project or through
unresolvable links are reported unreadable. Reports include `recorded` and `in_sync`, excluded seed
counts, per-artifact status and fenced diffs where the reference is derivable.
No persisted index produces an explicit `recorded: false` report; files are not
classified retroactively.

Co-owned Makefiles and CI workflows expose structural facts only. Recipe bodies,
workflow job graphs and entire files are not content-diffed. Managed docs compare
against the current standard, using recorded project identity and lifecycle data;
the report does not reconstruct an original generated base. Architecture content
remains presence-only until its missing render inputs are captured.

The default `kickstart plan` remains the existing managed-doc standard check.
`adopt --check` remains the conformance interface. This ownership mode supplies a
bounded metadata consumer for the prerequisite tracked by ENG-630; the general
drift command remains ENG-12. Existing [fence boundaries](../decisions/docs-ownership-fences.md)
and [docs-plan scope](plan-drift-scope.md) remain in force. Broader reconciliation,
repair, three-way merge and the older proposal's go/no-go decisions remain outside
this change; this contract does not mark that proposal accepted.

Exit codes: 0 when the recorded scope passes, 1 for findings or unrecorded ownership,
2 for an unusable target or invalid manifest.
