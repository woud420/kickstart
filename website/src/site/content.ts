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
  latestVersion: "0.4.0",
  supportedFrom: "0.4.0",
  repositoryUrl: "https://github.com/woud420/kickstart",
  releaseUrl: "https://github.com/woud420/kickstart/releases/tag/v0.4.0",
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
    version: "0.4.0",
    title: "First supported baseline",
    body: "First supported release line for typed scaffolds, release assets, and Worker website deployment.",
    highlights: [
      "Modern Python metadata, validation commands, and Linux/macOS binary release workflow.",
      "Cloudflare provider and Worker scaffolding, including TypeScript and Rust Workers.",
      "Typed specs, layout plans, stack registry, template plans, and agent-readable scaffold docs.",
    ],
  },
];
