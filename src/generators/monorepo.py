from pathlib import Path
from src.utils.fs import write_file
from src.utils.logger import success, warn

TEMPLATE_ROOT = Path(__file__).parent.parent / "templates" / "monorepo"

def create_monorepo(name: str, config: dict, helm: bool = False):
    project = Path(name)
    if project.exists():
        warn(f"Directory '{name}' already exists.")
        return

    (project / "infra" / "docker").mkdir(parents=True)
    (project / "infra" / "terraform" / "modules" / "example_module").mkdir(parents=True)
    for env in ["dev", "staging", "prod"]:
        (project / f"infra/terraform/env/{env}").mkdir(parents=True)

    if helm:
        (project / "infra" / "helm" / "example-service" / "templates").mkdir(parents=True)
        write_file(project / "infra/helm/example-service/Chart.yaml", TEMPLATE_ROOT / "helm/Chart.yaml")
        write_file(project / "infra/helm/example-service/values.yaml", TEMPLATE_ROOT / "helm/values.yaml")
        write_file(project / "infra/helm/example-service/templates/deployment.yaml", TEMPLATE_ROOT / "helm/deployment.yaml")
    else:
        (project / "infra/k8s/base").mkdir(parents=True)
        for env in ["dev", "staging", "prod"]:
            (project / f"infra/k8s/overlays/{env}").mkdir(parents=True)
        write_file(project / "infra/k8s/base/kustomization.yaml", TEMPLATE_ROOT / "kustomize/kustomization.yaml")
        write_file(project / "infra/k8s/base/deployment.yaml", TEMPLATE_ROOT / "kustomize/deployment.yaml")
        write_file(project / "infra/k8s/base/service.yaml", TEMPLATE_ROOT / "kustomize/service.yaml")

    write_file(project / "infra/docker/docker-compose.yml", TEMPLATE_ROOT / "docker-compose.yml")
    for env in ["dev", "staging", "prod"]:
        write_file(project / f"infra/terraform/env/{env}/main.tf", TEMPLATE_ROOT / "terraform_env_main.tf")
        write_file(project / f"infra/terraform/env/{env}/variables.tf", TEMPLATE_ROOT / "variables.tf")

    (project / ".github" / "workflows").mkdir(parents=True)
    for wf in ["build.yml", "test.yml", "deploy.yml"]:
        write_file(project / f".github/workflows/{wf}", TEMPLATE_ROOT / wf)

    (project / "architecture").mkdir()
    write_file(project / "architecture/README.md", f"# {name} Deployment Infra Docs\n")
    write_file(project / "Makefile", TEMPLATE_ROOT / "Makefile.tpl", monorepo_name=name)
    write_file(project / "README.md", TEMPLATE_ROOT / "README.md.tpl", monorepo_name=name)

    success(f"Monorepo '{name}' scaffolded with {'Helm' if helm else 'Kustomize'} support.")

