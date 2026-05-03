"""Interactive prompt handling for CLI create options."""

from typing import Protocol, cast

import typer

from src.cli.options import CreateCommandOptions, CreateOptions
from src.utils.types import GeneratorConfig


class PromptReader(Protocol):
    """Prompt API used by interactive create flows."""

    def ask(
        self,
        prompt: str,
        *,
        choices: list[str] | None = None,
        default: str | None = None,
    ) -> str:
        """Ask for a string value."""


class ConfirmReader(Protocol):
    """Confirmation API used by interactive create flows."""

    def ask(self, prompt: str, *, default: bool = False) -> bool:
        """Ask for a yes/no value."""


def prompt_for_missing_args(
    options: CreateCommandOptions,
    config: GeneratorConfig,
    *,
    prompt: PromptReader,
    confirm: ConfirmReader,
) -> CreateOptions:
    """Prompt user for any missing create arguments in interactive mode."""
    project_type = options.project_type
    name = options.name
    root = options.root
    lang = options.lang
    gh = options.gh
    helm = options.helm
    database = options.database
    cache = options.cache
    auth = options.auth
    framework = options.framework
    cloud = options.cloud
    knowledge = options.knowledge
    runtime = options.runtime
    interactive_mode = not project_type or not name

    if project_type and root is None:
        root = prompt.ask("Where should the project be created?")

    if not project_type:
        typer.echo("[bold cyan]Launching interactive wizard...\n[/]")
        project_type = prompt.ask(
            "What do you want to create?",
            choices=["service", "frontend", "lib", "cli", "mono"],
        )
        name = prompt.ask("Project name?")
        if root is None:
            root = prompt.ask("Where should the project be created?")
        default_language = cast(str, config.get("default_language", "python"))
        lang = prompt.ask("Language", default=default_language)
        gh = confirm.ask("Create GitHub repo?", default=False)
        if project_type in ["mono", "service"]:
            helm = confirm.ask("Use Helm scaffolding?", default=False)

    if project_type == "service" and lang == "python" and interactive_mode:
        if database is None:
            database = prompt.ask("Database extension", choices=["none", "postgres"], default="none")
            if database == "none":
                database = None

        if cache is None:
            cache = prompt.ask("Cache extension", choices=["none", "redis"], default="none")
            if cache == "none":
                cache = None

        if auth is None:
            auth = prompt.ask("Authentication extension", choices=["none", "jwt"], default="none")
            if auth == "none":
                auth = None

        if framework is None:
            framework = prompt.ask("HTTP framework", choices=["fastapi", "minimal"], default="fastapi")
            if framework == "fastapi":
                framework = None

    assert project_type is not None, "project_type should be set by now"
    assert name is not None, "name should be set by now"

    return CreateOptions(
        project_type=project_type,
        name=name,
        root=root,
        lang=lang,
        gh=gh,
        helm=helm,
        database=database,
        cache=cache,
        auth=auth,
        framework=framework,
        cloud=cloud,
        knowledge=knowledge,
        runtime=runtime,
    )
