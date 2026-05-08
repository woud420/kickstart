"""Audit template wiring and explicit blueprint inventory."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from src.generator.language_setup import (
    go_service_content_templates,
    rust_service_content_templates,
    typescript_service_templates,
)
from src.generator.lib import CLI_LANGUAGE_SETUP, LIBRARY_LANGUAGE_SETUP
from src.generator.template_plans import (
    cli_template_plan,
    frontend_template_plan,
    library_template_plan,
    python_service_core_template_plan,
)
from src.stack.profile import stack_registry
from src.utils.extension_manager import ExtensionManager


TEMPLATE_ROOT = Path("src/templates")


@dataclass(frozen=True)
class BlueprintTemplateSet:
    """Known intentionally retained templates that are not active defaults yet."""

    name: str
    prefixes: tuple[str, ...] = ()
    files: tuple[str, ...] = ()

    def contains(self, path: str) -> bool:
        """Return True when the template belongs to this blueprint set."""
        return path in self.files or path.startswith(self.prefixes)


@dataclass(frozen=True)
class TemplateFamilySummary:
    """Per-family template wiring counts."""

    family: str
    active: int
    blueprint: int
    unknown: int
    total: int


KNOWN_BLUEPRINT_SETS = (
    BlueprintTemplateSet(
        name="shared-reference",
        files=(
            "_shared/base_gitignore.tpl",
            "_shared/lang_config.py",
            "_shared/project_structure.md",
            "_shared/service_readme.tpl",
        ),
    ),
    BlueprintTemplateSet(
        name="python-rich-service-reference",
        prefixes=(
            "python/base/",
            "python/core/api/",
            "python/core/infrastructure/",
            "python/core/model/dto/",
            "python/core/model/entities/",
            "python/core/services/",
            "python/core/validators/",
            "python/dao/",
            "python/repository/",
        ),
        files=(
            "python/core/__init__.py.tpl",
            "python/core/model/schemas.py.tpl",
        ),
    ),
)


def main() -> None:
    """Run the template wiring audit."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="Fail when unknown templates are present.")
    args = parser.parse_args()

    files = _template_files()
    active = _active_templates()
    active.update(_referenced_templates(active))
    blueprints = {path for path in files if _is_known_blueprint(path)}
    unknown = sorted(files - active - blueprints)

    print(f"template files: {len(files)}")
    print(f"active templates: {len(active & files)}")
    print(f"blueprint templates: {len(blueprints)}")
    print(f"unknown templates: {len(unknown)}")
    print("template families:")
    for summary in _family_summaries(files, active, blueprints):
        print(
            f"  {summary.family}: "
            f"{summary.active} active, {summary.blueprint} blueprint, "
            f"{summary.unknown} unknown, {summary.total} total"
        )
    for path in unknown:
        print(f"unknown: {path}")

    if args.strict and unknown:
        raise SystemExit(1)


def _template_files() -> set[str]:
    return {
        str(path.relative_to(TEMPLATE_ROOT))
        for path in TEMPLATE_ROOT.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }


def _active_templates() -> set[str]:
    active: set[str] = set()

    for language in stack_registry.languages:
        for runtime in stack_registry.service_runtimes:
            try:
                selection = stack_registry.service_selection(language, runtime)
            except Exception:
                continue
            active.update(template.template for template in selection.templates)

    for cloud in stack_registry.clouds:
        for knowledge in stack_registry.knowledge:
            for runtime in stack_registry.monorepo_runtimes:
                for helm in (False, True):
                    try:
                        selection = stack_registry.monorepo_selection(cloud, knowledge, runtime, helm=helm)
                    except Exception:
                        continue
                    active.update(f"monorepo/{template.template}" for template in selection.templates)

    active.update(f"monorepo/{template.template}" for template in stack_registry.helm_template_configs())
    active.update(f"monorepo/{template.template}" for template in stack_registry.kustomize_template_configs())
    active.update(
        {
            "monorepo/Makefile.tpl",
            "monorepo/README.md.tpl",
            "monorepo/kustomize/overlay-kustomization.yaml",
        }
    )

    for entry in frontend_template_plan().entries():
        active.add(f"react/{entry.template}")

    for language, profile in stack_registry.languages.items():
        if profile.library:
            for entry in library_template_plan(language).entries():
                active.add(entry.template)
        if profile.cli:
            for entry in cli_template_plan(language).entries():
                active.add(entry.template)

    for setup in (*LIBRARY_LANGUAGE_SETUP.values(), *CLI_LANGUAGE_SETUP.values()):
        active.update(template.template for template in setup.templates)

    for framework in (None, "minimal"):
        active.update(entry.template for entry in python_service_core_template_plan(framework).entries())

    active.update(template.template for template in go_service_content_templates())
    for include_redis_cache in (False, True):
        for include_jwt_auth in (False, True):
            active.update(
                template.template
                for template in rust_service_content_templates(
                    include_redis_cache=include_redis_cache,
                    include_jwt_auth=include_jwt_auth,
                )
            )

    active.update(template.template for template in typescript_service_templates(include_postgres_database=True))

    extension_manager = ExtensionManager()
    for extension_group in extension_manager._extensions.values():
        for extension in extension_group.values():
            active.update(template.template for template in extension.config.templates)
            active.add(extension.config.requirements_file)

    active.update(
        {
            "python/core/env.example.tpl",
            "python/core/migrations/001_initial.sql.tpl",
            "typescript/extensions/database/migrations.sql.tpl",
            "typescript/src/clients/database.ts.tpl",
            "rust/extensions/cache/redis.rs.tpl",
            "rust/extensions/auth/jwt.rs.tpl",
        }
    )
    return active


def _referenced_templates(seed_templates: set[str]) -> set[str]:
    referenced: set[str] = set()
    pending = list(seed_templates)

    while pending:
        template = pending.pop()
        path = TEMPLATE_ROOT / template
        if not path.exists() or not path.is_file():
            continue

        for nested in _jinja_references(path.read_text(encoding="utf-8", errors="ignore")):
            if nested not in referenced:
                referenced.add(nested)
                pending.append(nested)

    return referenced


def _jinja_references(template_text: str) -> set[str]:
    references: set[str] = set()
    for marker in ('{% include "', '{% extends "'):
        position = 0
        while True:
            start = template_text.find(marker, position)
            if start == -1:
                break
            start += len(marker)
            end = template_text.find('"', start)
            if end == -1:
                break
            references.add(template_text[start:end])
            position = end + 1
    return references


def _is_known_blueprint(path: str) -> bool:
    return any(blueprint_set.contains(path) for blueprint_set in KNOWN_BLUEPRINT_SETS)


def _family_summaries(
    files: set[str],
    active: set[str],
    blueprints: set[str],
) -> tuple[TemplateFamilySummary, ...]:
    """Return active/blueprint/unknown counts grouped by top-level template family."""
    summaries: list[TemplateFamilySummary] = []
    for family in sorted({_template_family(path) for path in files}):
        family_files = {path for path in files if _template_family(path) == family}
        family_active = family_files & active
        family_blueprints = family_files & blueprints
        family_unknown = family_files - family_active - family_blueprints
        summaries.append(
            TemplateFamilySummary(
                family=family,
                active=len(family_active),
                blueprint=len(family_blueprints),
                unknown=len(family_unknown),
                total=len(family_files),
            )
        )
    return tuple(summaries)


def _template_family(path: str) -> str:
    """Return the top-level template family for a template path."""
    return path.split("/", 1)[0]


if __name__ == "__main__":
    main()
