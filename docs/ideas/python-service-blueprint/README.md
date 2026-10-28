# Python service blueprint

Status: reference material for future development. These templates are not a
supported generator profile or a runnable application.

## Purpose and provenance

This directory preserves the 46 unrendered Python templates previously held in
`src/templates/`. Their contents are unchanged from
[`1d227ee89bfa8ce8c76c4b94890fecafd3075819`](https://github.com/woud420/kickstart/tree/1d227ee89bfa8ce8c76c4b94890fecafd3075819/src/templates/python).
Paths below `python/` retain their original structure. The former
`python-rich-service-reference` inventory identifies the set; active templates
such as `python/core/api/__init__.py.tpl` and `python/core/api/services.py.tpl`
remain in `src/templates/` and are not duplicated here.

The reference belongs outside `src/` so it remains discoverable without shipping
in the wheel or the PyInstaller template bundle. The four former `_shared/`
reference files are redundant with the current language configuration and active
templates and are not retained here.

## Reference map

| Area | Potential reuse |
| --- | --- |
| [`python/base/`](python/base/) | Package exports and health-check variants |
| [`python/core/api/`](python/core/api/) | Dependency injection, routes, auth, and request logging |
| [`python/core/infrastructure/`](python/core/infrastructure/) | PostgreSQL pooling and Redis caching |
| [`python/core/model/`](python/core/model/) | Domain entities, request/response DTOs, and schemas |
| [`python/core/services/`](python/core/services/) | Business operations and service errors |
| [`python/core/validators/`](python/core/validators/) | Domain validation |
| [`python/dao/`](python/dao/) | Database access interfaces and PostgreSQL operations |
| [`python/repository/`](python/repository/) | Repository interfaces and user repository implementation |

## Limitations

- No generator renders these paths. Passing Kickstart tests does not validate this
  reference as a generated application, and the template-wiring audit only covers
  the shipped tree under `src/templates/`.
- Imports, package exports, dependencies, configuration, and Jinja blocks reflect
  an earlier design. Preserving relative paths does not make the set complete or
  compatible with the active scaffold.
- `python/core/services/base_service.py.tpl` documents a transaction scope, but
  its base implementation only yields `None` and logs success. It supplies no
  database commit, rollback, or cross-repository atomicity guarantee.
- The active scaffold already has entities, DTOs, a repository contract, service
  operations, routes, and database/cache/auth extensions. The extra DAO,
  repository, and service layers require a concrete use case before adoption.
- Auth, SQL construction, cache serialization, error handling, and transaction
  behavior require review and behavior tests before any code is activated.

## Recommended development path

Extract useful pieces into the existing extensions first. If a richer service
profile is justified, make it an explicit option while preserving the lightweight
default. Reconcile the reference with the current typed template plans, package
layout, configuration, and dependency choices rather than copying the whole tree.

Before promotion, add tests for the rendered application and affected extension
combinations, including persistence, transaction failure, auth failures, cache
behavior, and lifecycle cleanup as applicable. Run `make check` and the generator
evals in [`docs/operations/evals.md`](../../operations/evals.md). Document the
selected capability and generated-output contract when it becomes supported.
