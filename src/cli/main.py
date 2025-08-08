import typer
from rich import print
from rich.prompt import Prompt, Confirm
from typing import Optional

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
from src.utils.codegen import generate_dao_from_schema
from src.utils.help_generator import get_help_generator

app = typer.Typer(help="Kickstart: Full-stack project scaffolding CLI")


@app.command()
def version():
    """Show the current version."""
    print(f"[bold cyan]Kickstart v{__version__}[/]")

@app.command()
def upgrade():
    """Upgrade to the latest version."""
    check_for_update()

@app.command("list")
def list_templates():
    """List all available project templates and their capabilities."""
    help_gen = get_help_generator()
    output = help_gen.generate_list_command_output()
    print(output)

@app.command()
def completion(shell: str = typer.Argument(..., help="bash | zsh | fish | powershell")):
    """Generate shell completion script."""
    typer.echo(app.get_completion(shell))

@app.command()
def create(
    project_type: Optional[str] = typer.Argument(None),
    name: Optional[str] = typer.Argument(None),
    root: Optional[str] = typer.Option(None, "--root", "-r", help="Root directory where the project will be created"),
    lang: str = typer.Option("python", "--lang", "-l"),
    gh: bool = typer.Option(False, "--gh", help="Create GitHub repository automatically"),
    helm: bool = typer.Option(False, "--helm", help="Add Helm chart for Kubernetes deployment (services and monorepos only)"),
    non_interactive: bool = typer.Option(
        False,
        "--non-interactive",
        "--yes",
        help="Run without prompts; requires all arguments via CLI",
    ),
):
    """Create a new project with modern tooling and best practices."""
    config = load_config()

    if non_interactive:
        if not project_type or not name or root is None:
            print("[bold red]❌ Non-interactive mode requires project type, name, and --root.[/]")
            raise typer.Exit(1)
    else:
        if project_type and root is None:
            root = Prompt.ask("Where should the project be created?")

        if not project_type:
            typer.echo("[bold cyan]Launching interactive wizard...\n[/]")
            project_type = Prompt.ask("What do you want to create?", choices=["service", "frontend", "lib", "cli", "mono"])
            name = Prompt.ask("Project name?")
            if root is None:
                root = Prompt.ask("Where should the project be created?")
            lang = Prompt.ask("Language", default=config.get("default_language", "python"))
            gh = Confirm.ask("Create GitHub repo?", default=False)
            if project_type in ["mono", "service"]:
                helm = Confirm.ask("Use Helm scaffolding?", default=False)

    if project_type == "service":
        create_service(name, lang, gh, config, helm=helm, root=root)
    elif project_type == "frontend":
        create_frontend(name, gh, config, root=root)
    elif project_type == "lib":
        create_lib(name, lang, gh, config, root=root)
    elif project_type == "cli":
        create_cli(name, lang, gh, config, root=root)
    elif project_type == "mono":
        create_monorepo(name, gh, config, helm=helm, root=root)
    else:
        print(f"[bold red]❌ Type '{project_type}' not supported.[/]")

@app.command()
def codegen(
    schema_file: str = typer.Argument(..., help="Path to SQL schema file"),
    language: str = typer.Option("rust", "--lang", "-l", help="Target language (rust, cpp, python, go)"),
    output_dir: str = typer.Option("./src", "--output", "-o", help="Output directory"),
    service_name: str = typer.Option("service", "--name", "-n", help="Service name")
):
    """Generate DAO code from database schema for multiple languages."""
    import os
    from pathlib import Path
    
    if not os.path.exists(schema_file):
        print(f"[bold red]❌ Schema file '{schema_file}' not found.[/]")
        raise typer.Exit(1)
    
    supported_languages = ['rust', 'cpp', 'python', 'go']
    if language not in supported_languages:
        print(f"[bold red]❌ Unsupported language '{language}'. Supported: {', '.join(supported_languages)}[/]")
        raise typer.Exit(1)
    
    try:
        generate_dao_from_schema(schema_file, output_dir, service_name, language)
        print(f"[bold green]✅ Generated {language.upper()} DAO code in '{output_dir}'[/]")
    except Exception as e:
        print(f"[bold red]❌ Error generating code: {e}[/]")
        raise typer.Exit(1)

# Initialize dynamic help after all commands are defined
def _initialize_dynamic_help():
    """Update CLI help text dynamically based on available templates."""
    try:
        help_gen = get_help_generator()
        create.__doc__ = help_gen.generate_detailed_help_docstring()
    except Exception:
        # Fallback to static help if dynamic generation fails
        pass

_initialize_dynamic_help()
