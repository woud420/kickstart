import typer
import logging
from rich import print
from rich.prompt import Prompt, Confirm
from typing import Any, Optional, Dict, Tuple

logger = logging.getLogger(__name__)

from src import __version__
from src.utils.config import load_config
from src.api import (
    create_service,
    create_frontend,
    create_lib,
    create_cli,
    create_monorepo,
)
from src.utils.updater import check_for_update

app: typer.Typer = typer.Typer(help="Kickstart: Full-stack project scaffolding CLI")

@app.command()
def version() -> None:
    """Show the current version."""
    print(f"[bold cyan]Kickstart v{__version__}[/]")

@app.command()
def upgrade() -> None:
    """Upgrade to the latest version."""
    check_for_update()

@app.command()
def completion(shell: str = typer.Argument(..., help="bash | zsh | fish | powershell")) -> None:
    """Generate shell completion script."""
    # Note: Typer completion API may vary by version
    typer.echo("Completion not implemented")

def _prompt_for_missing_args(
    project_type: Optional[str],
    name: Optional[str],
    root: Optional[str],
    lang: str,
    gh: bool,
    helm: bool,
    config: Dict[str, Any],
    database: Optional[str] = None,
    cache: Optional[str] = None,
    auth: Optional[str] = None,
    framework: Optional[str] = None
) -> Tuple[str, str, Optional[str], str, bool, bool, Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Prompt user for any missing arguments in interactive mode.

    Args:
        project_type: Type of project to create
        name: Project name
        root: Root directory
        lang: Programming language
        gh: Whether to create GitHub repo
        helm: Whether to use Helm scaffolding
        config: Configuration dictionary

    Returns:
        Tuple of (project_type, name, root, lang, gh, helm) with all values filled
    """
    # Track if we're in interactive mode
    interactive_mode = not project_type or not name

    # Handle case where project_type is provided but root is not
    if project_type and root is None:
        root = Prompt.ask("Where should the project be created?")

    # Interactive wizard if project_type not provided
    if not project_type:
        typer.echo("[bold cyan]Launching interactive wizard...\n[/]")
        project_type = Prompt.ask(
            "What do you want to create?",
            choices=["service", "frontend", "lib", "cli", "mono"]
        )
        name = Prompt.ask("Project name?")
        if root is None:
            root = Prompt.ask("Where should the project be created?")
        lang = Prompt.ask("Language", default=config.get("default_language", "python"))
        gh = Confirm.ask("Create GitHub repo?", default=False)
        if project_type in ["mono", "service"]:
            helm = Confirm.ask("Use Helm scaffolding?", default=False)

    # Prompt for extensions if creating a service and they weren't provided
    # Only prompt in interactive mode
    if project_type == "service" and lang == "python" and interactive_mode:
        if database is None:
            database_options = ["none", "postgres", "mysql", "sqlite"]
            database = Prompt.ask("Database extension", choices=database_options, default="none")
            if database == "none":
                database = None

        if cache is None:
            cache_options = ["none", "redis", "memcached"]
            cache = Prompt.ask("Cache extension", choices=cache_options, default="none")
            if cache == "none":
                cache = None

        if auth is None:
            auth_options = ["none", "jwt", "oauth"]
            auth = Prompt.ask("Authentication extension", choices=auth_options, default="none")
            if auth == "none":
                auth = None

        if framework is None:
            framework_options = ["fastapi", "minimal"]
            framework = Prompt.ask("HTTP framework", choices=framework_options, default="fastapi")
            if framework == "fastapi":
                framework = None  # None means FastAPI default

    # Ensure required values are set
    assert project_type is not None, "project_type should be set by now"
    assert name is not None, "name should be set by now"
    
    return project_type, name, root, lang, gh, helm, database, cache, auth, framework


def _dispatch_project_creation(
    project_type: str,
    name: str,
    root: Optional[str],
    lang: str,
    gh: bool,
    helm: bool,
    config: Dict[str, Any],
    database: Optional[str] = None,
    cache: Optional[str] = None,
    auth: Optional[str] = None,
    framework: Optional[str] = None
) -> None:
    """Dispatch to the appropriate project creation function.
    
    Args:
        project_type: Type of project to create
        name: Project name
        root: Root directory
        lang: Programming language  
        gh: Whether to create GitHub repo
        helm: Whether to use Helm scaffolding
        config: Configuration dictionary
    """
    # Dispatch table for cleaner code and easier extension
    project_creators = {
        "service": lambda: create_service(name, lang, gh, config, helm=helm, root=root, database=database, cache=cache, auth=auth, framework=framework),
        "frontend": lambda: create_frontend(name, gh, config, root=root),
        "lib": lambda: create_lib(name, lang, gh, config, root=root),
        "cli": lambda: create_cli(name, lang, gh, config, root=root),
        "mono": lambda: create_monorepo(name, gh, config, helm=helm, root=root),
    }
    
    creator = project_creators.get(project_type)
    if creator:
        creator()
    else:
        print(f"[bold red]❌ Type '{project_type}' not supported.[/]")


@app.command()
def create(
    project_type: Optional[str] = typer.Argument(None),
    name: Optional[str] = typer.Argument(None),
    root: Optional[str] = typer.Option(None, "--root", "-r", help="Root directory where the project will be created"),
    lang: str = typer.Option("python", "--lang", "-l"),
    gh: bool = typer.Option(False, "--gh", help="Create GitHub repo"),
    helm: bool = typer.Option(False, "--helm", help="Add Helm scaffolding (services or mono only)"),
    database: Optional[str] = typer.Option(None, "--database", help="Database extension (postgres, mysql, sqlite)"),
    cache: Optional[str] = typer.Option(None, "--cache", help="Cache extension (redis, memcached)"),
    auth: Optional[str] = typer.Option(None, "--auth", help="Authentication extension (jwt, oauth)"),
    framework: Optional[str] = typer.Option(None, "--framework", help="HTTP framework (minimal for standard library, default is FastAPI)")
) -> None:
    """Create a new service, lib, CLI, frontend, or mono repo.
    
    This command supports both non-interactive and interactive modes:
    - Non-interactive: Provide all required arguments via CLI flags
    - Interactive: Launch a wizard to guide you through project creation
    
    Args:
        project_type: Type of project (service, frontend, lib, cli, mono)
        name: Name of the project
        root: Root directory where project will be created
        lang: Programming language for the project
        gh: Create a GitHub repository
        helm: Add Helm scaffolding (for services and monorepos only)
    """
    try:
        config: Dict[str, Any] = load_config()

        # Prompt for any missing arguments
        project_type, name, root, lang, gh, helm, database, cache, auth, framework = _prompt_for_missing_args(
            project_type, name, root, lang, gh, helm, config, database, cache, auth, framework
        )

        # Dispatch to appropriate creation function
        _dispatch_project_creation(project_type, name, root, lang, gh, helm, config, database, cache, auth, framework)
        
    except KeyboardInterrupt:
        print("\n[yellow]Operation cancelled by user.[/]")
    except Exception as e:
        print(f"[bold red]❌ Failed to create project: {e}[/]")
        logger.exception("Project creation failed")
