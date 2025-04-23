from pathlib import Path
from src.utils.fs import write_file
from src.utils.logger import success, warn

TEMPLATE_ROOT = Path(__file__).parent.parent / "templates"

def create_lib(name: str, lang: str, config: dict, root: str = None):
    project = Path(root) / name if root else Path(name)
    if project.exists():
        warn(f"Directory '{project}' already exists.")
        return

    (project / "src").mkdir(parents=True)
    (project / "tests").mkdir()
    (project / "architecture").mkdir()

    templates = TEMPLATE_ROOT / lang
    write_file(project / ".gitignore", templates / "gitignore.tpl")
    write_file(project / "Makefile", templates / "Makefile.tpl", service_name=name)
    write_file(project / "README.md", templates / "README.md.tpl", service_name=name)
    write_file(project / "architecture/README.md", f"# {name} Library Docs\n")

    if lang == "python":
        write_file(project / "pyproject.toml", templates / "pyproject.toml.tpl", service_name=name)
    elif lang == "rust":
        write_file(project / "Cargo.toml", templates / "Cargo.toml.tpl", service_name=name)

    success(f"{lang.title()} library '{name}' created successfully in '{project}'!")

def create_cli(name: str, lang: str, config: dict, root: str = None):
    project = Path(root) / name if root else Path(name)
    if project.exists():
        warn(f"Directory '{project}' already exists.")
        return

    (project / "src").mkdir(parents=True)
    (project / "tests").mkdir()
    (project / "architecture").mkdir()

    templates = TEMPLATE_ROOT / lang
    write_file(project / ".gitignore", templates / "gitignore.tpl")
    write_file(project / "Makefile", templates / "Makefile.tpl", service_name=name)
    write_file(project / "README.md", templates / "README.md.tpl", service_name=name)
    write_file(project / "architecture/README.md", f"# {name} CLI Docs\n")

    if lang == "python":
        write_file(project / "pyproject.toml", templates / "pyproject.cli.toml.tpl", service_name=name)
        write_file(project / "src/main.py", 'import sys\\nprint("Hello from CLI")\\nsys.exit(0)\n')
    elif lang == "rust":
        write_file(project / "Cargo.toml", templates / "Cargo.cli.toml.tpl", service_name=name)
        write_file(project / "src/main.rs", 'fn main() {\n    println!("Hello from CLI!");\n}\n')

    success(f"{lang.title()} CLI '{name}' created successfully in '{project}'!")

