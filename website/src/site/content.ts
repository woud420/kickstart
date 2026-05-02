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
    summary: "Writes a Python API with Dockerfile, Postgres/Redis clients, JWT hook, migrations, docs, and tests. Dependency containers remain explicit.",
    output: [
      "Dockerfile",
      "Makefile",
      "pyproject.toml",
      "requirements.txt",
      ".env.example",
      "src/main.py",
      "src/config/settings.py",
      "src/routes/health.py",
      "src/routes/users.py",
      "src/clients/database.py",
      "src/clients/cache.py",
      "src/handler/auth.py",
      "src/model/repository.py",
      "migrations/001_initial.sql",
      "tests/unit/",
      "tests/integration/",
      "AGENTS.md",
      ".kickstart/scaffold.json",
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
    summary: "Writes a TypeScript Worker with Wrangler config, strict TypeScript, tests, and deploy commands.",
    output: [
      "wrangler.toml",
      "package.json",
      "tsconfig.json",
      "src/index.ts",
      "tests/worker.test.ts",
      "README.md",
      "Makefile",
      "AGENTS.md",
      ".kickstart/scaffold.json",
      "docs/architecture/README.md",
      "docs/contracts/README.md",
      "docs/operations/README.md",
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
    key: "mono",
    label: "aws k8s",
    title: "aws kubernetes workspace",
    command: "kickstart create mono platform --cloud aws --runtime kubernetes --knowledge none",
    summary: "Writes a TypeScript/Bun workspace with apps, packages, AWS Terraform, Kubernetes manifests, GitHub Actions, docs, and agent notes.",
    output: [
      "apps/",
      "packages/",
      "infra/terraform/",
      "infra/terraform/env/dev/main.tf",
      "infra/k8s/base/deployment.yaml",
      "infra/k8s/base/service.yaml",
      "infra/k8s/overlays/dev/kustomization.yaml",
      ".github/workflows/build.yml",
      ".github/workflows/test.yml",
      ".github/workflows/deploy.yml",
      "AGENTS.md",
      ".kickstart/scaffold.json",
      "docs/architecture/README.md",
      "docs/architecture/context.md",
      "docs/contracts/README.md",
      "docs/operations/README.md",
      "docs/decisions/0001-stack-profile.md",
      "docs/agents/recommended-agents.md",
      "package.json",
      "turbo.json",
      "config/tsconfig/base.json",
    ],
    components: [
      {
        label: "Applications",
        detail: "apps/ holds deployable projects.",
      },
      {
        label: "Shared packages",
        detail: "packages/ holds reusable code.",
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
    summary: "Writes a Rust CLI with Cargo metadata, source entrypoint, tests, Makefile, README, docs, and an agent scaffold contract.",
    output: [
      "Cargo.toml",
      "src/main.rs",
      "tests/",
      "Makefile",
      "README.md",
      "AGENTS.md",
      ".kickstart/scaffold.json",
      "docs/architecture/README.md",
      "docs/contracts/README.md",
      "docs/operations/README.md",
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
    body: "v0.4.0 is the first supported kickstart release line.",
    highlights: [
      "Modern Python metadata, validation commands, and Linux/macOS binary release workflow.",
      "Cloudflare cloud/runtime scaffolding, including TypeScript and Rust Workers.",
      "Typed specs, layout plans, stack registry, template plans, and agent-readable scaffold docs.",
    ],
  },
];
