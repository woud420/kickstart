interface ReleaseConfig {
  output: string;
  releaseLabel: string;
  releaseUrl: string;
  repositoryUrl: string;
  serviceName: string;
  version: string;
}

const defaultConfig: ReleaseConfig = {
  output: "wrangler.release.toml",
  releaseLabel: "Latest",
  releaseUrl: "https://github.com/woud420/kickstart/releases/tag/v0.4.0",
  repositoryUrl: "https://github.com/woud420/kickstart",
  serviceName: "kickstart-site",
  version: "0.4.0",
};

function argumentValue(args: string[], name: string): string | undefined {
  const prefix = `${name}=`;
  const inline = args.find((arg) => arg.startsWith(prefix));

  if (inline !== undefined) {
    return inline.slice(prefix.length);
  }

  const index = args.indexOf(name);
  if (index === -1) {
    return undefined;
  }

  return args[index + 1];
}

function trimVersionPrefix(version: string): string {
  return version.startsWith("v") ? version.slice(1) : version;
}

function repositoryUrlFromEnv(env: Record<string, string | undefined>): string | undefined {
  return env.GITHUB_REPOSITORY === undefined ? undefined : `https://github.com/${env.GITHUB_REPOSITORY}`;
}

function tomlString(value: string): string {
  return JSON.stringify(value);
}

export function resolveReleaseConfig(
  args: string[],
  env: Record<string, string | undefined>,
): ReleaseConfig {
  const repositoryUrl =
    argumentValue(args, "--repository-url") ?? repositoryUrlFromEnv(env) ?? defaultConfig.repositoryUrl;
  const version = trimVersionPrefix(
    argumentValue(args, "--version") ?? env.GITHUB_REF_NAME ?? defaultConfig.version,
  );
  const releaseUrl =
    argumentValue(args, "--release-url") ?? `${repositoryUrl}/releases/tag/v${version}`;

  return {
    output: argumentValue(args, "--output") ?? defaultConfig.output,
    releaseLabel: argumentValue(args, "--release-label") ?? defaultConfig.releaseLabel,
    releaseUrl,
    repositoryUrl,
    serviceName: argumentValue(args, "--service-name") ?? defaultConfig.serviceName,
    version,
  };
}

export function renderWranglerConfig(config: ReleaseConfig): string {
  return `name = ${tomlString(config.serviceName)}
main = "src/index.ts"
compatibility_date = "2026-05-02"

[vars]
SERVICE_NAME = ${tomlString(config.serviceName)}
PROJECT_VERSION = ${tomlString(config.version)}
REPOSITORY_URL = ${tomlString(config.repositoryUrl)}
RELEASE_URL = ${tomlString(config.releaseUrl)}
RELEASE_LABEL = ${tomlString(config.releaseLabel)}
`;
}

if (import.meta.main) {
  const config = resolveReleaseConfig(Bun.argv.slice(2), process.env);
  await Bun.write(config.output, renderWranglerConfig(config));
  console.log(`Wrote ${config.output} for v${config.version}`);
}
