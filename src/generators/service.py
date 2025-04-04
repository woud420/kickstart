from pathlib import Path
from src.utils.fs import write_file
from src.utils.logger import info, success, warn

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"

def create_service(name: str, lang: str, gh: bool, config: dict, helm: bool = False):
    project = Path(name)
    if project.exists():
        warn(f"Directory '{name}' already exists.")
        return

    (project / "src").mkdir(parents=True)
    (project / "tests" / "unit").mkdir(parents=True)
    (project / "tests" / "integration").mkdir(parents=True)
    (project / "architecture").mkdir(parents=True)

    templates = TEMPLATE_DIR / lang
    if not templates.exists():
        warn(f"No templates for language: {lang}")
        return

    write_file(project / "README.md", templates / "README.md.tpl", service_name=name)
    write_file(project / ".gitignore", templates / "gitignore.tpl")
    write_file(project / "Dockerfile", templates / "Dockerfile.tpl")
    write_file(project / "Makefile", templates / "Makefile.tpl", service_name=name)
    write_file(project / "architecture" / "README.md", f"# {name} Architecture Notes\n")
    write_file(project / ".env.example", "EXAMPLE_ENV_VAR=value\n")

    if lang == "python":
        write_file(project / "requirements.txt", templates / "requirements.txt.tpl")
    elif lang == "rust":
        write_file(project / "Cargo.toml", templates / "Cargo.toml.tpl", service_name=name)

    if helm:
        helm_path = project / "helm" / name
        (helm_path / "templates").mkdir(parents=True)
        write_file(helm_path / "Chart.yaml", TEMPLATE_DIR / "monorepo/helm/Chart.yaml", service_name=name)
        write_file(helm_path / "values.yaml", TEMPLATE_DIR / "monorepo/helm/values.yaml", service_name=name)
        write_file(helm_path / "templates/deployment.yaml", TEMPLATE_DIR / "monorepo/helm/deployment.yaml", service_name=name)
        info("Helm chart scaffolded")

    success(f"{lang.title()} service '{name}' created successfully!")

