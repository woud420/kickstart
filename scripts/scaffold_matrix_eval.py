"""Generate a broad scaffold evaluation matrix.

The harness intentionally validates generated output rather than imported
generator internals. It is meant for local design evals, not release CI.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
from typing import Literal, TypeGuard, cast


ProjectScale = Literal["micro", "small", "medium", "large"]
ComponentKind = Literal["system", "service", "worker", "frontend", "cli", "library"]
JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]
type ManifestObject = dict[str, JsonValue]


@dataclass(frozen=True)
class ComponentPlan:
    """One generated component inside an imagined project."""

    kind: ComponentKind
    name: str
    args: tuple[str, ...]
    root_slot: str
    intent: str
    desired_gap: str | None = None


@dataclass(frozen=True)
class ProjectPlan:
    """One imagined project to evaluate against kickstart."""

    index: int
    slug: str
    title: str
    scale: ProjectScale
    domain: str
    organization: str
    components: tuple[ComponentPlan, ...]


@dataclass(frozen=True)
class ComponentResult:
    """Generation and validation result for one component."""

    plan: ComponentPlan
    command: tuple[str, ...]
    target_path: Path
    returncode: int
    issues: tuple[str, ...]
    stdout: str
    stderr: str


@dataclass(frozen=True)
class ProjectResult:
    """Evaluation result for one imagined project."""

    plan: ProjectPlan
    components: tuple[ComponentResult, ...]

    @property
    def issues(self) -> tuple[str, ...]:
        """Return flattened issues for this project."""
        all_issues: list[str] = []
        for component in self.components:
            all_issues.extend(component.issues)
        return tuple(all_issues)


DOMAINS = (
    "accounting ledger",
    "appointment booking",
    "asset inventory",
    "audit evidence",
    "billing reconciliation",
    "campus events",
    "chat moderation",
    "clinical intake",
    "compliance policy",
    "construction punch list",
    "content publishing",
    "contract review",
    "customer support",
    "data labeling",
    "developer portal",
    "document search",
    "donation tracking",
    "edge image resize",
    "energy telemetry",
    "feature flagging",
    "fleet maintenance",
    "fraud review",
    "game leaderboard",
    "grant management",
    "habit coaching",
    "home automation",
    "incident response",
    "internal analytics",
    "inventory forecasting",
    "invoice ingestion",
    "iot device registry",
    "job board",
    "knowledge capture",
    "lab sample tracking",
    "lead routing",
    "legal matter tracker",
    "log enrichment",
    "marketplace search",
    "membership portal",
    "metrics gateway",
    "mobile backend",
    "newsletter operations",
    "observability control plane",
    "order fulfillment",
    "payment webhook",
    "personal finance",
    "privacy request workflow",
    "product feedback",
    "project staffing",
    "queue worker admin",
    "real estate listings",
    "recipe planner",
    "release coordination",
    "research archive",
    "retail kiosk",
    "risk scoring",
    "sales compensation",
    "school roster",
    "security questionnaire",
    "sensor alerting",
    "shipping labels",
    "subscription portal",
    "support runbooks",
    "team directory",
    "ticket triage",
    "timesheet approvals",
    "travel expenses",
    "warehouse receiving",
    "workflow automation",
)


SYSTEM_ARCHETYPES = (
    ("aws", "kubernetes", False, "none"),
    ("aws", "kubernetes", True, "none"),
    ("gcp", "kubernetes", False, "obsidian"),
    ("multi", "hybrid", False, "both"),
    ("cloudflare", "cloudflare-workers", False, "backstage"),
    ("cloudflare", "hybrid", True, "both"),
    ("none", "kubernetes", False, "none"),
)


SERVICE_LANGUAGES = ("python", "typescript", "rust", "cpp", "go")
WORKER_LANGUAGES = ("typescript", "rust")
PACKAGE_LANGUAGES = ("python", "rust")


def build_plans(
    count: int,
    seed: int,
    *,
    max_components_per_project: int = 9,
    max_system_depth: int = 1,
    include_known_gaps: bool = True,
) -> tuple[ProjectPlan, ...]:
    """Build deterministic imagined project plans."""
    rng = random.Random(seed)
    domains = list(DOMAINS)
    rng.shuffle(domains)
    plans: list[ProjectPlan] = []

    for index in range(1, count + 1):
        domain = domains[(index - 1) % len(domains)]
        scale = _scale_for_index(index)
        slug = f"eval-{index:03d}-{domain.replace(' ', '-')}"
        components = _components_for_project(
            index,
            scale,
            rng,
            max_components_per_project=max_components_per_project,
            max_system_depth=max_system_depth,
            include_known_gaps=include_known_gaps,
        )
        plans.append(
            ProjectPlan(
                index=index,
                slug=slug,
                title=f"{domain.title()} Project",
                scale=scale,
                domain=domain,
                organization=_organization_for(scale),
                components=components,
            )
        )

    return tuple(plans)


def _scale_for_index(index: int) -> ProjectScale:
    if index <= 30:
        return "micro"
    if index <= 65:
        return "small"
    if index <= 100:
        return "medium"
    return "large"


def _organization_for(scale: ProjectScale) -> str:
    if scale == "micro":
        return "single generated component"
    if scale == "small":
        return "two to three generated components under one project root"
    if scale == "medium":
        return "system monorepo plus application components"
    return "system monorepo with multiple services, edge paths, packages, and tools"


def _components_for_project(
    index: int,
    scale: ProjectScale,
    rng: random.Random,
    *,
    max_components_per_project: int,
    max_system_depth: int,
    include_known_gaps: bool,
) -> tuple[ComponentPlan, ...]:
    components: tuple[ComponentPlan, ...]
    if scale == "micro":
        components = (_micro_component(index, rng),)
    elif scale == "small":
        components = _small_components(index, rng)
    elif scale == "medium":
        components = _system_components(index, rng, service_count=2, include_frontend=index % 3 != 0)
    else:
        components = _system_components(
            index,
            rng,
            service_count=3,
            include_frontend=True,
            include_gap=include_known_gaps and index % 5 == 0,
        )

    return _expand_components_for_limits(
        index,
        scale,
        rng,
        components,
        max_components_per_project=max_components_per_project,
        max_system_depth=max_system_depth,
    )


def _expand_components_for_limits(
    index: int,
    scale: ProjectScale,
    rng: random.Random,
    components: tuple[ComponentPlan, ...],
    *,
    max_components_per_project: int,
    max_system_depth: int,
) -> tuple[ComponentPlan, ...]:
    """Expand a plan for wider eval profiles while preserving default shape."""
    if max_components_per_project <= 9 and max_system_depth <= 1:
        return components

    desired_count = _desired_component_count(index, scale, max_components_per_project)
    expanded = list(components[:max_components_per_project])

    if (
        max_system_depth >= 2
        and scale in {"medium", "large"}
        and any(component.kind == "system" and component.root_slot == "." for component in expanded)
        and len(expanded) < desired_count
    ):
        expanded.append(_nested_system_component(index))

    while len(expanded) < desired_count:
        expanded.append(_extra_component(index, len(expanded) + 1, rng))

    return tuple(expanded[:max_components_per_project])


def _desired_component_count(index: int, scale: ProjectScale, max_components_per_project: int) -> int:
    """Return a deterministic target count for an eval project."""
    if scale == "micro":
        return 1
    if scale == "small":
        return min(max_components_per_project, 2 + (index % 4))
    if scale == "medium":
        return min(max_components_per_project, 4 + (index % 7))
    return min(max_components_per_project, 6 + (index % 10))


def _nested_system_component(index: int) -> ComponentPlan:
    """Return a second-level system component inside a generated system."""
    cloud, runtime, helm, knowledge = SYSTEM_ARCHETYPES[(index + 3) % len(SYSTEM_ARCHETYPES)]
    args = ["create", "mono", "subsystem", "--cloud", cloud, "--runtime", runtime, "--knowledge", knowledge]
    if helm:
        args.append("--helm")
    return ComponentPlan(
        "system",
        f"subsystem-{(index % 3) + 1}",
        tuple(args),
        "systems",
        f"nested {runtime} system boundary targeting {cloud}",
    )


def _extra_component(index: int, position: int, rng: random.Random) -> ComponentPlan:
    """Return an additional component for wide eval profiles."""
    name_suffix = f"extra-{position}"
    choice = (index + position) % 5
    if choice == 0:
        return _service_component(f"svc-{name_suffix}", rng, helm=False)
    if choice == 1:
        return _worker_component(f"edge-{name_suffix}", rng)
    if choice == 2:
        return _library_component(f"shared-{name_suffix}", rng)
    if choice == 3:
        return _cli_component(f"ops-{name_suffix}", rng)
    return ComponentPlan(
        "frontend",
        f"web-{name_suffix}",
        ("create", "frontend", f"web-{name_suffix}"),
        "apps",
        "additional frontend surface",
    )


def _micro_component(index: int, rng: random.Random) -> ComponentPlan:
    choice = index % 6
    if choice == 0:
        return _service_component("api", rng, helm=index % 12 == 0)
    if choice == 1:
        return _worker_component("edge", rng)
    if choice == 2:
        return ComponentPlan("frontend", "web", ("create", "frontend", "web"), ".", "React static frontend")
    if choice == 3:
        return _cli_component("ops", rng)
    if choice == 4:
        return _library_component("core", rng)
    return _python_data_service("api")


def _small_components(index: int, rng: random.Random) -> tuple[ComponentPlan, ...]:
    components = [
        _service_component("api", rng, helm=index % 10 == 0),
        ComponentPlan("frontend", "web", ("create", "frontend", "web"), "apps", "operator/browser frontend"),
    ]
    if index % 3 == 0:
        components.append(_cli_component("ops", rng))
    if index % 4 == 0:
        components.append(_worker_component("edge", rng))
    return tuple(components)


def _system_components(
    index: int,
    rng: random.Random,
    *,
    service_count: int,
    include_frontend: bool,
    include_gap: bool = False,
) -> tuple[ComponentPlan, ...]:
    cloud, runtime, helm, knowledge = SYSTEM_ARCHETYPES[index % len(SYSTEM_ARCHETYPES)]
    args = ["create", "mono", "system", "--cloud", cloud, "--runtime", runtime, "--knowledge", knowledge]
    if helm:
        args.append("--helm")

    components: list[ComponentPlan] = [
        ComponentPlan("system", "system", tuple(args), ".", f"{runtime} system workspace targeting {cloud}"),
    ]
    if include_frontend:
        components.append(ComponentPlan("frontend", "web", ("create", "frontend", "web"), "apps", "user/admin frontend"))

    for service_index in range(service_count):
        service_name = f"svc-{service_index + 1}"
        components.append(_service_component(service_name, rng, helm=helm and service_index == 0))

    components.append(_library_component("shared", rng))
    components.append(_cli_component("ops", rng))

    if runtime in {"hybrid", "cloudflare-workers"}:
        components.append(_worker_component("edge", rng))

    if include_gap:
        components.append(
            ComponentPlan(
                "service",
                "cf-container",
                ("create", "service", "cf-container", "--lang", "python", "--runtime", "cloudflare-containers"),
                "services",
                "Cloudflare Containers service behind a Worker",
                desired_gap="cloudflare-containers execution model",
            )
        )

    return tuple(components)


def _service_component(name: str, rng: random.Random, *, helm: bool) -> ComponentPlan:
    language = rng.choice(SERVICE_LANGUAGES)
    args = ["create", "service", name, "--lang", language]
    intent = f"{language} container service"
    if language == "python":
        args.extend(["--database", "postgres"])
        if rng.random() < 0.7:
            args.extend(["--cache", "redis"])
        if rng.random() < 0.5:
            args.extend(["--auth", "jwt"])
        intent = "Python API service with generated extension hooks"
    if helm:
        args.append("--helm")
        intent = f"{intent} with Helm artifacts"
    return ComponentPlan("service", name, tuple(args), "services", intent)


def _python_data_service(name: str) -> ComponentPlan:
    return ComponentPlan(
        "service",
        name,
        ("create", "service", name, "--lang", "python", "--database", "postgres", "--cache", "redis", "--auth", "jwt"),
        "services",
        "Python API service with Postgres, Redis, and JWT hooks",
    )


def _worker_component(name: str, rng: random.Random) -> ComponentPlan:
    language = rng.choice(WORKER_LANGUAGES)
    return ComponentPlan(
        "worker",
        name,
        ("create", "service", name, "--lang", language, "--runtime", "cloudflare-workers"),
        "apps",
        f"{language} Cloudflare Worker edge component",
    )


def _cli_component(name: str, rng: random.Random) -> ComponentPlan:
    language = rng.choice(PACKAGE_LANGUAGES)
    return ComponentPlan("cli", name, ("create", "cli", name, "--lang", language), "tools", f"{language} CLI tool")


def _library_component(name: str, rng: random.Random) -> ComponentPlan:
    language = rng.choice(PACKAGE_LANGUAGES)
    return ComponentPlan(
        "library",
        name,
        ("create", "lib", name, "--lang", language),
        "libs",
        f"{language} shared library",
    )


def evaluate(plans: tuple[ProjectPlan, ...], repo_root: Path, output_root: Path) -> tuple[ProjectResult, ...]:
    """Run kickstart for every planned project and validate output."""
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)

    results: list[ProjectResult] = []
    for plan in plans:
        project_root = output_root / plan.slug
        if not _has_top_level_system(plan):
            project_root.mkdir(parents=True)

        component_results: list[ComponentResult] = []
        for component in plan.components:
            root = _component_root(output_root, project_root, component)
            root.mkdir(parents=True, exist_ok=True)
            command = _command_with_root(plan, component, root)
            completed = _run_command(command, repo_root)
            target_path = _target_path(output_root, root, plan, component)
            issues = _validate_component(component, target_path, completed.returncode, completed.stdout, completed.stderr)
            component_results.append(
                ComponentResult(
                    plan=component,
                    command=command,
                    target_path=target_path,
                    returncode=completed.returncode,
                    issues=tuple(issues),
                    stdout=completed.stdout,
                    stderr=completed.stderr,
                )
            )
        results.append(ProjectResult(plan=plan, components=tuple(component_results)))
    return tuple(results)


def _has_top_level_system(plan: ProjectPlan) -> bool:
    return any(component.kind == "system" and component.root_slot == "." for component in plan.components)


def _component_root(output_root: Path, project_root: Path, component: ComponentPlan) -> Path:
    if component.kind == "system":
        if component.root_slot == ".":
            return output_root
        return project_root / component.root_slot
    if component.root_slot == ".":
        return project_root
    return project_root / component.root_slot


def _target_path(output_root: Path, root: Path, plan: ProjectPlan, component: ComponentPlan) -> Path:
    if component.kind == "system":
        return root / _system_component_name(plan, component)
    return root / component.name


def _command_with_root(plan: ProjectPlan, component: ComponentPlan, root: Path) -> tuple[str, ...]:
    args = list(component.args)
    if component.kind == "system":
        args[2] = _system_component_name(plan, component)
    return (sys.executable, "-m", "src.cli.main", *args, "--root", str(root))


def _system_component_name(plan: ProjectPlan, component: ComponentPlan) -> str:
    """Return the generated directory name for a system component."""
    if component.root_slot == ".":
        return plan.slug
    return component.name


def _run_command(command: tuple[str, ...], repo_root: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root)
    return subprocess.run(
        command,
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _validate_component(
    component: ComponentPlan,
    target_path: Path,
    returncode: int,
    stdout: str,
    stderr: str,
) -> list[str]:
    issues: list[str] = []
    if returncode != 0:
        issue = f"command failed with code {returncode}"
        if component.desired_gap is not None:
            issue = f"desired gap unsupported: {component.desired_gap}"
        issues.append(issue)
        if "Unsupported" in stderr or "Unsupported" in stdout:
            issues.append(_compact_output(stdout, stderr))
        return issues

    if not target_path.exists():
        return [f"target path was not created: {target_path}"]

    manifest_path = target_path / ".kickstart/scaffold.json"
    if not manifest_path.exists():
        issues.append("missing .kickstart/scaffold.json")
        return issues

    manifest = _load_manifest(manifest_path, issues)
    if manifest is None:
        return issues

    _validate_common_contract(target_path, manifest, issues)
    _validate_kind_contract(component, target_path, manifest, issues)
    return issues


def _compact_output(stdout: str, stderr: str) -> str:
    text = "\n".join(part.strip() for part in (stdout, stderr) if part.strip())
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and "...<" not in line and line.strip() not in {")", "("}
    ]
    return " / ".join(lines[-3:])[:240]


def _load_manifest(path: Path, issues: list[str]) -> ManifestObject | None:
    try:
        payload = cast(JsonValue, json.loads(path.read_text()))
    except json.JSONDecodeError as exc:
        issues.append(f"manifest json decode failed: {exc}")
        return None
    if not _is_json_object(payload):
        issues.append("manifest root is not an object")
        return None
    return payload


def _validate_common_contract(target_path: Path, manifest: ManifestObject, issues: list[str]) -> None:
    required_paths = (
        "AGENTS.md",
        "docs/architecture/README.md",
        "docs/contracts/README.md",
        "docs/operations/README.md",
        "docs/decisions/README.md",
    )
    for relative_path in required_paths:
        if not (target_path / relative_path).exists():
            issues.append(f"missing {relative_path}")

    if "options" in manifest:
        issues.append("manifest still contains legacy options object")

    project = manifest.get("project")
    if not _is_json_object(project):
        issues.append("manifest project is not an object")
    else:
        if "type" in project:
            issues.append("manifest project still uses legacy type key")
        if "kind" not in project:
            issues.append("manifest project.kind missing")
        if "repo_layout" not in project:
            issues.append("manifest project.repo_layout missing")

    if not _is_json_object(manifest.get("execution")):
        issues.append("manifest execution is not an object")
    if not _is_json_object(manifest.get("artifacts")):
        issues.append("manifest artifacts is not an object")
    if not _is_json_object(manifest.get("provider")):
        issues.append("manifest provider is not an object")


def _validate_kind_contract(
    component: ComponentPlan,
    target_path: Path,
    manifest: ManifestObject,
    issues: list[str],
) -> None:
    project = manifest.get("project")
    execution = manifest.get("execution")
    artifacts = manifest.get("artifacts")
    provider = manifest.get("provider")
    if not _is_json_object(project) or not _is_json_object(execution) or not _is_json_object(artifacts):
        return

    kind = project.get("kind")
    if component.kind == "worker":
        if kind != "worker":
            issues.append(f"worker generated manifest kind {kind!r}")
        _expect_list_member(execution, "models", "cloudflare-worker", issues)
        _expect_list_member(execution, "platforms", "cloudflare-workers", issues)
        if artifacts.get("worker") != "wrangler":
            issues.append("worker manifest missing wrangler artifact")
        if _is_json_object(provider) and "cloudflare" not in _string_list(provider.get("targets")):
            issues.append("worker provider target does not include cloudflare")
        if (target_path / "Dockerfile").exists():
            issues.append("worker generated a Dockerfile")
    elif component.kind == "service":
        if kind != "service":
            issues.append(f"service generated manifest kind {kind!r}")
        _expect_list_member(execution, "models", "container", issues)
        if artifacts.get("image") != "dockerfile":
            issues.append("container service missing dockerfile image artifact")
        if artifacts.get("kubernetes") == "helm":
            _validate_helm(target_path, issues)
    elif component.kind == "system":
        if kind != "system":
            issues.append(f"system generated manifest kind {kind!r}")
        if project.get("repo_layout") != "monorepo":
            issues.append("system repo_layout is not monorepo")
        _validate_system(target_path, manifest, issues)
    elif component.kind == "frontend":
        if kind != "frontend":
            issues.append(f"frontend generated manifest kind {kind!r}")
        if artifacts.get("static_site") != "vite":
            issues.append("frontend missing vite static_site artifact")
    elif component.kind == "cli":
        if kind != "cli":
            issues.append(f"cli generated manifest kind {kind!r}")
    elif component.kind == "library" and kind != "library":
        issues.append(f"library generated manifest kind {kind!r}")


def _expect_list_member(source: ManifestObject, key: str, expected: str, issues: list[str]) -> None:
    values = _string_list(source.get(key))
    if expected not in values:
        issues.append(f"manifest {key} missing {expected}")


def _string_list(value: JsonValue | None) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str))


def _is_json_object(value: JsonValue | None) -> TypeGuard[ManifestObject]:
    return isinstance(value, dict)


def _validate_helm(target_path: Path, issues: list[str]) -> None:
    helm_roots = [path for path in (target_path / "helm").glob("*") if path.is_dir()] if (target_path / "helm").exists() else []
    helm_roots.extend([path for path in (target_path / "infra/helm").glob("*") if path.is_dir()] if (target_path / "infra/helm").exists() else [])
    if not helm_roots:
        issues.append("helm artifact declared but no chart root exists")
        return

    for chart_root in helm_roots:
        for relative_path in (
            "Chart.yaml",
            "values.yaml",
            "templates/deployment.yaml",
            "templates/service.yaml",
            "templates/configmap.yaml",
            "templates/_helpers.tpl",
        ):
            if not (chart_root / relative_path).exists():
                issues.append(f"helm chart missing {chart_root.name}/{relative_path}")
        deployment = chart_root / "templates/deployment.yaml"
        if deployment.exists():
            text = deployment.read_text()
            for bad_fragment in ("}}  labels", "}}spec", "}}  selector", "targetPort }}          envFrom"):
                if bad_fragment in text:
                    issues.append(f"helm deployment contains collapsed fragment {bad_fragment!r}")


def _validate_system(target_path: Path, manifest: ManifestObject, issues: list[str]) -> None:
    execution = manifest.get("execution")
    artifacts = manifest.get("artifacts")
    provider = manifest.get("provider")
    if not _is_json_object(execution) or not _is_json_object(artifacts) or not _is_json_object(provider):
        return

    platforms = _string_list(execution.get("platforms"))
    provider_targets = _string_list(provider.get("targets"))
    if "cloudflare-workers" in platforms and "cloudflare" not in provider_targets:
        issues.append("Cloudflare Workers platform without cloudflare provider target")
    if artifacts.get("kubernetes") == "kustomize" and not (target_path / "infra/k8s/base/deployment.yaml").exists():
        issues.append("kustomize artifact declared but infra/k8s/base/deployment.yaml missing")
    if artifacts.get("kubernetes") == "helm":
        _validate_helm(target_path, issues)
    tfvars = target_path / "infra/terraform/env/dev/terraform.tfvars.example"
    if tfvars.exists():
        text = tfvars.read_text()
        if "clouds =" in text:
            issues.append("terraform tfvars still uses legacy clouds variable")


def write_report(path: Path, results: tuple[ProjectResult, ...], output_root: Path) -> None:
    """Write a Markdown eval report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    total_components = sum(len(result.components) for result in results)
    failed_commands = sum(1 for result in results for component in result.components if component.returncode != 0)
    issue_projects = sum(1 for result in results if result.issues)
    issue_components = sum(1 for result in results for component in result.components if component.issues)

    lines = [
        f"# {len(results)} Project Scaffold Eval",
        "",
        f"- Output root: `{output_root}`",
        f"- Projects: {len(results)}",
        f"- Components: {total_components}",
        f"- Failed commands: {failed_commands}",
        f"- Components with issues: {issue_components}",
        f"- Projects with issues: {issue_projects}",
        "",
        "## Findings",
        "",
    ]
    lines.extend(_finding_lines(results))
    lines.extend(["", "## Project Matrix", ""])
    lines.append("| # | Project | Scale | Organization | Components | Result |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for result in results:
        component_summary = ", ".join(f"{component.plan.kind}:{component.plan.name}" for component in result.components)
        result_text = "pass" if not result.issues else "; ".join(result.issues[:3])
        lines.append(
            "| {index} | {title} | {scale} | {organization} | {components} | {result} |".format(
                index=result.plan.index,
                title=_escape_table(result.plan.title),
                scale=result.plan.scale,
                organization=_escape_table(result.plan.organization),
                components=_escape_table(component_summary),
                result=_escape_table(result_text),
            )
        )

    lines.extend(["", "## Failed Or Interesting Components", ""])
    for result in results:
        for component in result.components:
            if not component.issues:
                continue
            lines.append(f"### {result.plan.index}. {result.plan.title} / {component.plan.name}")
            lines.append("")
            lines.append(f"- Intent: {component.plan.intent}")
            lines.append(f"- Command: `{' '.join(component.command)}`")
            lines.append(f"- Target: `{component.target_path}`")
            lines.append(f"- Issues: {'; '.join(component.issues)}")
            if component.stdout.strip() or component.stderr.strip():
                lines.append(f"- Output: `{_compact_output(component.stdout, component.stderr)}`")
            lines.append("")

    path.write_text("\n".join(lines) + "\n")


def _finding_lines(results: tuple[ProjectResult, ...]) -> list[str]:
    issue_counts: dict[str, int] = {}
    for result in results:
        for issue in result.issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
    if not issue_counts:
        return ["- No issues found across generated projects."]
    return [f"- {count}x {issue}" for issue, count in sorted(issue_counts.items(), key=lambda item: (-item[1], item[0]))]


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a broad kickstart scaffold matrix eval.")
    parser.add_argument("--count", type=int, default=120)
    parser.add_argument("--seed", type=int, default=20260502)
    parser.add_argument("--max-components-per-project", type=int, default=9)
    parser.add_argument("--max-system-depth", type=int, default=1)
    parser.add_argument("--exclude-known-gaps", action="store_true")
    parser.add_argument("--output-root", type=Path, default=Path("/private/tmp/kickstart-scaffold-matrix"))
    parser.add_argument("--report", type=Path, default=Path("reports/scaffold-eval-120.md"))
    args = parser.parse_args()

    if args.max_components_per_project < 1:
        parser.error("--max-components-per-project must be at least 1")
    if args.max_system_depth < 1:
        parser.error("--max-system-depth must be at least 1")

    repo_root = Path(__file__).resolve().parents[1]
    plans = build_plans(
        args.count,
        args.seed,
        max_components_per_project=args.max_components_per_project,
        max_system_depth=args.max_system_depth,
        include_known_gaps=not args.exclude_known_gaps,
    )
    results = evaluate(plans, repo_root, args.output_root)
    write_report(args.report, results, args.output_root)

    failed_commands = sum(1 for result in results for component in result.components if component.returncode != 0)
    issue_components = sum(1 for result in results for component in result.components if component.issues)
    print(
        json.dumps(
            {
                "projects": len(results),
                "components": sum(len(result.components) for result in results),
                "failed_commands": failed_commands,
                "components_with_issues": issue_components,
                "report": str(args.report),
                "output_root": str(args.output_root),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
