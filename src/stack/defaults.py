"""Default stack profile registry data."""

from src.stack.types import (
    ArtifactToolProfile,
    CloudProfile,
    KnowledgeProfile,
    LanguageProfile,
    RuntimeProfile,
)

environments = ("dev", "staging", "prod")

languages: dict[str, LanguageProfile] = {
    "python": LanguageProfile(
        id="python",
        display_name="Python",
        service_runtimes=("container",),
        library=True,
        cli=True,
        smoke_commands={
            "container": ("make install", "make test", "make check"),
        },
    ),
    "rust": LanguageProfile(
        id="rust",
        display_name="Rust",
        service_runtimes=("container", "cloudflare-workers"),
        library=True,
        cli=True,
        smoke_commands={
            "container": ("make install", "make test", "make check", "make build"),
            "cloudflare-workers": ("make install", "make check", "make build"),
        },
    ),
    "typescript": LanguageProfile(
        id="typescript",
        display_name="TypeScript",
        aliases=("ts",),
        service_runtimes=("container", "cloudflare-workers"),
        smoke_commands={
            "container": ("make install", "make test", "make check", "make build"),
            "cloudflare-workers": ("make install", "make test", "make check"),
        },
    ),
    "cpp": LanguageProfile(
        id="cpp",
        display_name="C++",
        aliases=("c++", "cxx"),
        service_runtimes=("container",),
        smoke_commands={
            "container": ("make install", "make test", "make check", "make build"),
        },
    ),
    "go": LanguageProfile(
        id="go",
        display_name="Go",
        service_runtimes=("container",),
        library=True,
        cli=True,
        smoke_commands={
            "container": ("make install", "make test", "make check", "make build"),
        },
    ),
}

service_runtimes: dict[str, RuntimeProfile] = {
    "container": RuntimeProfile(
        id="container",
        display_name="Container",
        aliases=("docker", "containers"),
        service_languages=("python", "rust", "typescript", "cpp", "go"),
        artifact_tools=("docker", "helm"),
    ),
    "cloudflare-workers": RuntimeProfile(
        id="cloudflare-workers",
        display_name="Cloudflare Workers",
        aliases=("cloudflare-worker", "cf-worker", "cf-workers", "worker", "workers"),
        service_languages=("typescript", "rust"),
        artifact_tools=("wrangler",),
        uses_cloudflare_workers=True,
    ),
}

monorepo_runtimes: dict[str, RuntimeProfile] = {
    "kubernetes": RuntimeProfile(
        id="kubernetes",
        display_name="Kubernetes",
        aliases=("k8s",),
        artifact_tools=("kustomize", "helm"),
        smoke_commands=("make install", "make test", "make check", "make k8s-render ENV=dev", "make tf-plan ENV=dev"),
        uses_kubernetes=True,
    ),
    "cloudflare-workers": RuntimeProfile(
        id="cloudflare-workers",
        display_name="Cloudflare Workers",
        aliases=("cloudflare-worker", "cf-worker", "cf-workers", "worker", "workers"),
        artifact_tools=("wrangler",),
        smoke_commands=("make install", "make test", "make check", "make cf-worker-notes", "make tf-plan ENV=dev"),
        uses_cloudflare_workers=True,
    ),
    "hybrid": RuntimeProfile(
        id="hybrid",
        display_name="Kubernetes and Cloudflare Workers",
        artifact_tools=("kustomize", "helm", "wrangler"),
        smoke_commands=(
            "make install",
            "make test",
            "make check",
            "make k8s-render ENV=dev",
            "make cf-worker-notes",
            "make tf-plan ENV=dev",
        ),
        uses_kubernetes=True,
        uses_cloudflare_workers=True,
    ),
}

clouds: dict[str, CloudProfile] = {
    "aws": CloudProfile(id="aws", display_name="AWS", providers=("aws",)),
    "gcp": CloudProfile(id="gcp", display_name="GCP", providers=("gcp",), aliases=("google",)),
    "cloudflare": CloudProfile(
        id="cloudflare",
        display_name="Cloudflare",
        providers=("cloudflare",),
        aliases=("cf",),
    ),
    "multi": CloudProfile(
        id="multi",
        display_name="Multi-cloud",
        providers=("aws", "gcp", "cloudflare"),
        aliases=("all",),
    ),
    "none": CloudProfile(id="none", display_name="Local only", providers=(), aliases=("local", "local-only")),
}

knowledge: dict[str, KnowledgeProfile] = {
    "none": KnowledgeProfile(id="none", display_name="None", include_obsidian=False, include_backstage=False),
    "obsidian": KnowledgeProfile(
        id="obsidian",
        display_name="Obsidian",
        include_obsidian=True,
        include_backstage=False,
    ),
    "backstage": KnowledgeProfile(
        id="backstage",
        display_name="Backstage",
        include_obsidian=False,
        include_backstage=True,
    ),
    "both": KnowledgeProfile(
        id="both",
        display_name="Backstage and Obsidian",
        include_obsidian=True,
        include_backstage=True,
    ),
}

artifact_tools: dict[str, ArtifactToolProfile] = {
    "docker": ArtifactToolProfile(id="docker", display_name="Docker"),
    "kustomize": ArtifactToolProfile(id="kustomize", display_name="Kustomize"),
    "helm": ArtifactToolProfile(id="helm", display_name="Helm"),
    "wrangler": ArtifactToolProfile(id="wrangler", display_name="Wrangler"),
}
