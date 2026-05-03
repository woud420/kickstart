"""Audit template wiring and explicit blueprint inventory."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.generator.language_setup import typescript_service_templates
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

KNOWN_BLUEPRINT_PREFIXES = (
    "python/base/",
    "python/core/api/",
    "python/core/infrastructure/",
    "python/core/model/dto/",
    "python/core/model/entities/",
    "python/core/services/",
    "python/core/validators/",
    "python/dao/",
    "python/repository/",
)

KNOWN_BLUEPRINT_FILES = {
    "_shared/base_gitignore.tpl",
    "_shared/lang_config.py",
    "_shared/project_structure.md",
    "_shared/service_readme.tpl",
    "python/core/__init__.py.tpl",
    "python/core/model/schemas.py.tpl",
}


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

    for language in ("python", "rust"):
        for entry in library_template_plan(language).entries():
            active.add(entry.template)
        for entry in cli_template_plan(language).entries():
            active.add(entry.template)

    for setup in (*LIBRARY_LANGUAGE_SETUP.values(), *CLI_LANGUAGE_SETUP.values()):
        active.update(template.template for template in setup.templates)

    for framework in (None, "minimal"):
        active.update(entry.template for entry in python_service_core_template_plan(framework).entries())

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
    return path in KNOWN_BLUEPRINT_FILES or path.startswith(KNOWN_BLUEPRINT_PREFIXES)


if __name__ == "__main__":
    main()
