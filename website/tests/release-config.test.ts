import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { describe, expect, it } from "vitest";

import { renderWranglerConfig, resolveReleaseConfig } from "../scripts/render-release-config";

describe("release config rendering", () => {
  it("reads the version from pyproject metadata by default", () => {
    const workspace = mkdtempSync(join(tmpdir(), "kickstart-website-release-"));
    const versionFile = join(workspace, "pyproject.toml");
    writeFileSync(versionFile, 'name = "kickstart"\nversion = "0.6.0"\n');

    try {
      const config = resolveReleaseConfig(
        ["--version-file", versionFile, "--repository-url", "https://github.com/example/kickstart"],
        {},
      );

      expect(config.version).toBe("0.6.0");
      expect(config.supportedFrom).toBe("0.4.0");
      expect(config.releaseUrl).toBe("https://github.com/example/kickstart/releases/tag/v0.6.0");
      expect(renderWranglerConfig(config)).toContain('PROJECT_VERSION = "0.6.0"');
      expect(renderWranglerConfig(config)).toContain('SUPPORTED_FROM_VERSION = "0.4.0"');
    } finally {
      rmSync(workspace, { force: true, recursive: true });
    }
  });

  it("allows the supported baseline to be configured", () => {
    const config = resolveReleaseConfig(["--version", "v0.7.0", "--supported-from", "v0.5.0"], {});

    expect(config.version).toBe("0.7.0");
    expect(config.supportedFrom).toBe("0.5.0");
    expect(renderWranglerConfig(config)).toContain('SUPPORTED_FROM_VERSION = "0.5.0"');
  });
});
