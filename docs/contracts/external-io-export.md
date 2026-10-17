# External I/O exporter contract

The first phase defines `ExternalIOContract` and pure JSON/Markdown renderers.
It supplies a shared representation for the optional exporter planned under
ENG-13. CLI registration, source extraction, scaffold activation and adoption
integration are subsequent phases. No existing generation path imports these
modules; this phase leaves default generated output unchanged.

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
File surface paths describe observed I/O and may be absolute. Evidence paths
are separately constrained to normalized, repository-relative POSIX file paths:
no absolute paths, parent traversal, drive/colon syntax, backslashes, trailing
slash or redundant components. Line numbers are positive integers (not booleans);
an optional end line is at or after the start.

`SurfaceUnknown` records a category (`http`, `cli`, `file`, `config`, `network`,
or `all`) and a nonempty reason. A producer without evidence should emit an
unknown instead of fabricating an observation. Citation checks validate path
and range shape; verifying file existence and whether its contents support the
claim belongs to the later evidence mapper. This model does not infer protocol
semantics, authentication, completeness, or source facts.

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

## Integration boundary

This contract defines data and rendering only. The follow-up must explicitly
choose optional CLI/scaffold/adopt activation, obtain evidence, and preserve
existing repository content when inserting a derived section. Deep analysis
may be delegated later. No evidence, runtime API semantics or exporter state
is added to scaffold.json in this phase.
