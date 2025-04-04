from pathlib import Path
from src.utils.fs import write_file
from src.utils.logger import success, warn

TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "react"

def create_frontend(name: str, config: dict):
    project = Path(name)
    if project.exists():
        warn(f"Directory '{name}' already exists.")
        return

    (project / "src").mkdir(parents=True)
    (project / "public").mkdir()
    (project / "tests").mkdir()
    (project / "architecture").mkdir()

    write_file(project / ".gitignore", TEMPLATE_DIR / "gitignore.tpl")
    write_file(project / "Dockerfile", TEMPLATE_DIR / "Dockerfile.tpl")
    write_file(project / "Makefile", TEMPLATE_DIR / "Makefile.tpl", service_name=name)
    write_file(project / "README.md", TEMPLATE_DIR / "README.md.tpl", service_name=name)
    write_file(project / "package.json", TEMPLATE_DIR / "package.json.tpl", service_name=name)
    write_file(project / "architecture/README.md", f"# {name} Frontend Docs\n")

    success(f"Frontend app '{name}' created successfully!")

