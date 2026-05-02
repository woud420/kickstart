# Knowledge Base

This directory explains the generated knowledge system. The repository-level `knowledge/` directory is the durable project memory root.

## Backstage

{% if include_backstage -%}
`catalog-info.yaml` registers the workspace as a Backstage component. `templates/backstage/template.yaml` is a starting point for a Backstage Software Template.
{% else -%}
Backstage files were not generated. Re-run with `--knowledge backstage` or `--knowledge both` if you want catalog metadata.
{% endif %}

## Obsidian

{% if include_obsidian -%}
Open the generated project root as an Obsidian vault. The `.obsidian/` directory includes minimal workspace settings and all Markdown docs are directly linkable.
{% else -%}
Obsidian settings were not generated. Re-run with `--knowledge obsidian` or `--knowledge both` if you want vault metadata.
{% endif %}

## Suggested Docs

- ADRs in `docs/adr/`
- Architecture diagrams in `docs/architecture/`
- Data decisions in `docs/data/`
- Operational procedures in `docs/runbooks/`
- Durable memory and entity notes in `knowledge/`
