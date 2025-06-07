import typer
from rich import print
from rich.prompt import Prompt, Confirm

from src import __version__
from src.utils.config import load_config
from src.generators.service import create_service
from src.generators.frontend import create_frontend
from src.generators.lib import create_lib, create_cli
from src.generators.monorepo import create_monorepo
from src.utils.updater import check_for_update

app = typer.Typer(help="Kickstart: Full-stack project scaffolding CLI")

@app.command()
def version():
    """Show the current version."""
    print(f"[bold cyan]Kickstart v{__version__}[/]")

@app.command()
def upgrade():
    """Upgrade to the latest version."""
    check_for_update()

@app.command()
def completion(shell: str = typer.Argument(..., help="bash | zsh | fish | powershell")):
    """Generate shell completion script."""
    typer.echo(app.get_completion(shell))

@app.command()
def create(
    type: str = typer.Argument(None),
    name: str = typer.Argument(None),
    root: str = typer.Option(..., "--root", "-r", help="Root directory where the project will be created"),
    lang: str = typer.Option("python", "--lang", "-l"),
    gh: bool = typer.Option(False, "--gh", help="Create GitHub repo"),
    helm: bool = typer.Option(False, "--helm", help="Add Helm scaffolding (services or mono only)")
):
    """
    Create a new service, lib, CLI, frontend, or mono repo.
    """
    config = load_config()

    if not type:
        typer.echo("[bold cyan]Launching interactive wizard...\n[/]")
        type = Prompt.ask("What do you want to create?", choices=["service", "frontend", "lib", "cli", "mono"])
        name = Prompt.ask("Project name?")
        root = Prompt.ask("Where should the project be created?")
        lang = Prompt.ask("Language", default=config.get("default_language", "python"))
        gh = Confirm.ask("Create GitHub repo?", default=False)
        if type in ["mono", "service"]:
            helm = Confirm.ask("Use Helm scaffolding?", default=False)

    if type == "service":
        create_service(name, lang, gh, config, helm=helm, root=root)
    elif type == "frontend":
        create_frontend(name, config, root=root)
    elif type == "lib":
        create_lib(name, lang, config, root=root)
    elif type == "cli":
        create_cli(name, lang, config, root=root)
    elif type == "mono":
        create_monorepo(name, config, helm=helm, root=root)
    else:
        print(f"[bold red]❌ Type '{type}' not supported.[/]")
