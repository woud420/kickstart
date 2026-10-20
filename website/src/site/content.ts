export interface CommandExample {
  key: string;
  label: string;
  title: string;
  command: string;
  summary: string;
  output: string[];
  components: GeneratedComponent[];
}

export interface GeneratedComponent {
  label: string;
  detail: string;
  agent?: boolean;
}

export interface PositioningPoint {
  title: string;
  body: string;
}

export interface ProjectMeta {
  latestVersion: string;
  supportedFrom: string;
  repositoryUrl: string;
  releaseUrl: string;
}

export interface ReleaseNote {
  version: string;
  title: string;
  body: string;
  highlights: string[];
}

export const defaultProjectMeta: ProjectMeta = {
  latestVersion: "0.4.5",
  supportedFrom: "0.4.0",
  repositoryUrl: "https://github.com/woud420/kickstart",
  releaseUrl: "https://github.com/woud420/kickstart/releases/tag/v0.4.5",
};

// Every example writes the same agent-facing files; the map names them so
// the "for agents" claim has a node of its own.
const agentContract: GeneratedComponent = {
  label: "Agent contract",
  detail: "AGENTS.md, CLAUDE.md, and .kickstart/scaffold.json describe layout, commands, and boundaries.",
  agent: true,
};

export const commandExamples: CommandExample[] = [
  {
    key: "service",
    label: "python service",
    title: "python service",
    command: "kickstart create service api --lang python --database postgres --cache redis --auth jwt",
    summary: "Writes a Python API with Dockerfile, Postgres/Redis clients, JWT hook, migrations, docs, and tests.",
    output: [
      "Dockerfile",
      "Makefile",
      "pyproject.toml",
      "requirements.txt",
      ".env.example",
      "src/main.py",
      "src/routes/health.py",
      "src/routes/users.py",
      "src/clients/database.py",
      "src/clients/cache.py",
      "src/handler/auth.py",
      "src/model/repository.py",
      "migrations/001_initial.sql",
      "tests/test_smoke.py",
      ".kickstart/scaffold.json",
      "AGENTS.md",
      "CLAUDE.md",
      ".agents/skills/README.md",
      "docs/architecture/README.md",
      "docs/contracts/README.md",
      "docs/operations/README.md",
      "docs/decisions/README.md",
    ],
    components: [
      {
        label: "API process",
        detail: "src/main.py and generated routes.",
      },
      {
        label: "Postgres client",
        detail: "src/clients/database.py plus migration SQL.",
      },
      {
        label: "Redis client",
        detail: "src/clients/cache.py and dependency entries.",
      },
      {
        label: "JWT auth",
        detail: "src/handler/auth.py extension hook.",
      },
      {
        label: "Container boundary",
        detail: "Dockerfile builds the app; services are explicit.",
      },
      agentContract,
    ],
  },
  {
    key: "worker",
    label: "cf worker",
    title: "cloudflare worker",
    command: "kickstart create service edge-site --lang typescript --runtime cloudflare-workers",
    summary: "Writes a TypeScript Worker with Wrangler config, strict TypeScript, tests, docs, and deploy commands.",
    output: [
      "wrangler.toml",
      ".dev.vars.example",
      "package.json",
      "tsconfig.json",
      "src/index.ts",
      "tests/worker.test.ts",
      "Makefile",
      ".kickstart/scaffold.json",
      "AGENTS.md",
      "CLAUDE.md",
      ".agents/skills/README.md",
      "docs/architecture/README.md",
      "docs/contracts/README.md",
      "docs/operations/README.md",
      "docs/decisions/README.md",
    ],
    components: [
      {
        label: "HTTP fetch handler",
        detail: "src/index.ts routes requests.",
      },
      {
        label: "Cloudflare runtime",
        detail: "wrangler.toml owns Worker config.",
      },
      {
        label: "Verification",
        detail: "Vitest and TypeScript scripts.",
      },
      agentContract,
    ],
  },
  {
    key: "system",
    label: "aws system",
    title: "aws kubernetes system",
    command: "kickstart create system platform --cloud aws --runtime kubernetes --knowledge none",
    summary: "Writes a language-neutral system root with AWS Terraform, Kubernetes manifests, GitHub Actions, docs, and agent notes.",
    output: [
      "apps/",
      "services/",
      "libs/",
      "tools/",
      "infra/docker/docker-compose.yml",
      "infra/terraform/env/dev/main.tf",
      "infra/terraform/modules/",
      "infra/k8s/base/deployment.yaml",
      "infra/k8s/base/service.yaml",
      "infra/k8s/overlays/dev/",
      ".github/workflows/build.yml",
      ".github/workflows/test.yml",
      ".github/workflows/deploy.yml",
      "data/postgres/schema.sql",
      ".kickstart/scaffold.json",
      "AGENTS.md",
      "CLAUDE.md",
      ".agents/skills/README.md",
      "docs/architecture/README.md",
      "docs/contracts/README.md",
      "docs/operations/README.md",
      "docs/decisions/0001-stack-profile.md",
      "docs/agents/recommended-agents.md",
    ],
    components: [
      {
        label: "Applications",
        detail: "apps/ and services/ hold deployable projects.",
      },
      {
        label: "Reusable code",
        detail: "libs/ holds shared code; tools/ holds automation and CLIs.",
      },
      {
        label: "Infrastructure",
        detail: "Terraform envs target AWS resources.",
      },
      {
        label: "Kubernetes runtime",
        detail: "Kustomize manifests render deploy shape.",
      },
      {
        label: "CI contract",
        detail: "Workflows define build/test/deploy.",
      },
      agentContract,
    ],
  },
  {
    key: "cli",
    label: "rust cli",
    title: "rust cli",
    command: "kickstart create cli ops-tool --lang rust",
    summary: "Writes a Rust CLI with Cargo metadata, source entrypoint, Makefile, README, docs, and an agent scaffold contract.",
    output: [
      "Cargo.toml",
      "src/main.rs",
      "tests/",
      "Makefile",
      "README.md",
      ".kickstart/scaffold.json",
      "AGENTS.md",
      "CLAUDE.md",
      ".agents/skills/README.md",
      "docs/architecture/README.md",
      "docs/contracts/README.md",
      "docs/operations/README.md",
      "docs/decisions/README.md",
    ],
    components: [
      {
        label: "CLI entrypoint",
        detail: "src/main.rs owns execution.",
      },
      {
        label: "Cargo project",
        detail: "Cargo.toml defines metadata.",
      },
      {
        label: "Review notes",
        detail: "docs/ explains structure, contracts, and operations.",
      },
      agentContract,
    ],
  },
];

export const isPoints: PositioningPoint[] = [
  {
    title: "Scaffold factory",
    body: "Turns a stack profile into a deterministic starter repo.",
  },
  {
    title: "Agent contract",
    body: "Writes layout, docs, commands, and boundaries.",
  },
  {
    title: "Repeatable bootstrap",
    body: "Same input, same starting shape.",
  },
];

export const isNotPoints: PositioningPoint[] = [
  {
    title: "Universal create-app",
    body: "It is intentionally narrow.",
  },
  {
    title: "Product architect",
    body: "It does not design the domain model.",
  },
  {
    title: "Runtime platform",
    body: "It does not run every dependency for you.",
  },
];

export const releaseNotes: ReleaseNote[] = [
  {
    version: "0.4.5",
    title: "Staged self-upgrades and legacy layout repair",
    body: "`kickstart upgrade` no longer replaces a managed install from inside its own running payload, and it repairs layouts left by older updaters.",
    highlights: [
      "Upgrades hand off to a staged copy of the new release, which swaps the install with rollback.",
      "Installs nested by pre-v0.4.4 updaters are repaired, even when no newer release exists.",
      "Upgrading from v0.4.4 can exit non-zero once; running `kickstart upgrade` again verifies the install.",
    ],
  },
  {
    version: "0.4.4",
    title: "Managed docs, catalog export, and reliable self-upgrades",
    body: "kickstart reports drift in the docs it manages, exports a Backstage catalog entry, and upgrades installs onto one managed layout.",
    highlights: [
      "`kickstart plan` shows managed-doc drift without touching your own content.",
      "`kickstart export backstage` writes a `catalog-info.yaml` that keeps your owner and lifecycle fields.",
      "Release builds send pseudonymous usage telemetry by default; `kickstart telemetry disable` opts out.",
    ],
  },
  {
    version: "0.4.3",
    title: "Sandbox bootstrap, tiered eval runner, coverage and badges",
    body: "A release for kickstart's own development; generated projects and the installed CLI are unchanged.",
    highlights: [
      "Claude Code on the web sets up Python and Bun automatically, so checks run right away.",
      "`scripts/run_evals.py --tier smoke|pr|full` runs every eval from one entrypoint.",
      "Coverage is published to Codecov, and generated-output size is guarded against regressions.",
    ],
  },
  {
    version: "0.4.2",
    title: "Trustworthy releases, leaner manifests, adopt preview",
    body: "Installed binaries report the release they came from, and generated metadata is cheaper for agents to read.",
    highlights: [
      "`kickstart version` reports the installed release.",
      "Invalid project names and failures exit non-zero instead of passing silently.",
      "`kickstart adopt --check` inspects an existing repo against the scaffold standard (read-only, `--json` for agents).",
    ],
  },
  {
    version: "0.4.1",
    title: "Scaffold contract convergence",
    body: "Generated projects behave the way their scaffold contract says across languages, and binaries install with one command.",
    highlights: [
      "Every generated Makefile exposes the same verbs in Python, Rust, Go, TypeScript and C++.",
      "Python service containers install their dependencies, expose their port and bind to `0.0.0.0`.",
      "A one-line install script verifies the SHA-256 checksum of the binary it downloads.",
    ],
  },
  {
    version: "0.4.0",
    title: "First supported baseline",
    body: "First supported release line for typed scaffolds, release assets, and Worker website deployment.",
    highlights: [
      "Modern Python metadata, validation commands, and a Linux/macOS binary release workflow.",
      "Cloudflare provider and Worker scaffolding, including TypeScript and Rust Workers.",
      "Typed specs, layout plans, stack registry, template plans, and agent-readable scaffold docs.",
    ],
  },
];

// Mirrors the README "Install" section; website/tests/content.test.ts fails
// when these drift from it.
export const installCommand =
  "curl -fsSL https://raw.githubusercontent.com/woud420/kickstart/master/scripts/install.sh | bash";

export const installPlatforms = "Linux x64/arm64 · macOS arm64";

export const installNotes: string[] = [
  "Verifies the release archive's SHA-256 checksum, puts the launcher at `~/.local/bin/kickstart`, and offers to add it to your `PATH`.",
  "Other platforms, including Intel macOS: `pipx install git+https://github.com/woud420/kickstart`. The PyPI name `kickstart` belongs to an unrelated project.",
  "Release builds send pseudonymous usage telemetry by default; `kickstart telemetry disable` opts out.",
  "Update in place with `kickstart upgrade`.",
];
