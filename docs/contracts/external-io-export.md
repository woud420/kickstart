# External I/O exporter contract

`ExternalIOContract` and pure JSON/Markdown renderers define the shared
representation for the optional exporter planned under ENG-13. The explicit
`kickstart export external-io` command now accepts declared observations and
checks their source locations. Automatic extraction, scaffold activation and
adoption insertion remain subsequent phases. Default generated output is
unchanged.

External I/O observations belong to derived exporter artifacts. They do not
become scaffold regeneration inputs or new `.kickstart/scaffold.json` fields.
The intended consumer outputs are a section in `docs/contracts/README.md` and
`docs/contracts/surface.json`. These functions return strings; they do not write
or replace either file, inspect a repository, or collect runtime values.

## Version 1 data

The root contains `schema_version: 1`, `project`, `coverage: "partial"`, an
ordered `surfaces` array and an explicit `unknowns` array. Coverage stays partial
even when the caller has no unknown entries; an empty unknowns list does not
claim exhaustive discovery. An empty observations list requires at least one
unknown with a reason.

Each observation has a typed `surface` and a nonempty tuple of `SourceEvidence`.
The surface discriminator and data are:

| Kind | Fields |
|---|---|
| `http` | `method`, `path` (starting with `/`) |
| `cli` | `command` (nonempty argv tuple), optional `option` (starting with `-`) |
| `file` | `path`, `access` (`read`, `write`, `read-write`) |
| `config` | `name`, `source` (`env` or `config`), `required` (`true`, `false`, or `null` for unknown) |
| `network` | `protocol`, `endpoint`, `direction` (`inbound` or `outbound`) |

Configuration records describe names and requirements; they have no value field.
Surface text is supplied explicitly, never looked up in the process environment.
Text must be representable as UTF-8; escaped unpaired Unicode surrogates are
rejected before rendering.
File surface paths describe observed I/O and may be absolute. Evidence paths
are separately constrained to normalized, repository-relative POSIX file paths:
no absolute paths, parent traversal, drive/colon syntax, backslashes, trailing
slash or redundant components. Line numbers are positive integers (not booleans);
an optional end line is at or after the start.

`SurfaceUnknown` records a category (`http`, `cli`, `file`, `config`, `network`,
or `all`) and a nonempty reason. A producer without evidence should emit an
unknown instead of fabricating an observation. The typed model validates path
and range shape. The explicit exporter additionally checks that cited files and
line ranges exist inside the selected repository. Whether source content proves
a claimed surface belongs to a later evidence mapper. This model does not infer
protocol semantics, authentication, completeness, or source facts.

All records are frozen dataclasses with tuple collections. JSON preserves
observation and citation order, uses stable keys, UTF-8 text and one trailing
newline. Markdown uses the same observations, always includes unknowns and keeps
supplied text inside literal code spans, including embedded backticks.

## Example

```python
from src.generator.external_io_contract import (
    ExternalIOContract, HttpSurface, SourceEvidence,
    SurfaceObservation, SurfaceUnknown,
)
from src.generator.external_io_render import (
    render_external_io_json, render_external_io_markdown,
)

contract = ExternalIOContract(
    project="sample",
    surfaces=(SurfaceObservation(
        HttpSurface("GET", "/health"),
        (SourceEvidence("src/app.py", 4, 7),),
    ),),
    unknowns=(SurfaceUnknown(
        "http", "Authentication and error responses have not been inspected",
    ),),
)
json_text = render_external_io_json(contract)
markdown_text = render_external_io_markdown(contract)
```

JSON:

```json
{
  "coverage": "partial",
  "project": "sample",
  "schema_version": 1,
  "surfaces": [
    {
      "evidence": [
        {
          "end_line": 7,
          "path": "src/app.py",
          "start_line": 4
        }
      ],
      "surface": {
        "kind": "http",
        "method": "GET",
        "path": "/health"
      }
    }
  ],
  "unknowns": [
    {
      "category": "http",
      "reason": "Authentication and error responses have not been inspected"
    }
  ]
}
```

Markdown section:

```markdown
## External I/O

Project: ` sample `.
Schema: 1. Coverage: partial.

### Observed surfaces

- http: ` GET /health `; evidence: ` src/app.py:4-7 `.

### Unknowns

- http: ` Authentication and error responses have not been inspected `.
```

`SurfaceObservation(HttpSurface("GET", "/health"), ())` is rejected because it
has no citation. `SourceEvidence("../outside.py", 1)` is rejected because the
citation escapes the repository. `ExternalIOContract("sample", (), ())` is
rejected because absence of observations needs an explicit unknown reason.
Malformed declarations raise `ExternalIOContractError`.

## Read-only CLI export

Supply a version-1 declaration in the JSON shape above. No scaffold manifest is
required: PATH may be an existing repository or another source directory.

```bash
kickstart export external-io path/to/repo --input declaration.json
kickstart export external-io path/to/repo --input declaration.json --format markdown
```

JSON is the default; `--format` accepts `json` or `markdown`. The input file path
is relative to the caller's working directory, while citation paths are relative
to PATH. Both outputs go to stdout with one trailing newline. Success exits 0;
invalid input, source locations or CLI arguments exit 2. Diagnostics go to stderr.

The reader rejects duplicate keys, unknown/missing fields, unsupported versions,
non-JSON numbers and invalid model values. All root fields are required. The
optional `end_line`, CLI `option` and config `required` fields may be absent or
null. Observations require citations; declarations without observations require
explicit unknowns. No configuration value field is accepted or expanded.

Cited sources must be UTF-8 files with existing one-based line ranges. Symlinks
within the selected root are allowed; a citation resolving outside it is rejected.
This checks locations and ranges, not whether the supplied claim follows from
the source. Coverage remains partial. Repository content, owned fences, manifests
and input declarations are not written.

## Integration boundary

The explicit command consumes declared evidence and renders one representation.
Automatic source discovery, optional create/adopt activation and safe insertion
into owned `docs/contracts/README.md` and `surface.json` remain follow-ups. Deep
analysis may be delegated later. No evidence, runtime API semantics or exporter
state is added to scaffold.json.
