import { readFileSync } from "node:fs";

import { describe, expect, it } from "vitest";

import { versionFromPyproject } from "../scripts/render-release-config";
import { defaultProjectMeta, installCommand, installNotes, releaseNotes } from "../src/site/content";

describe("release notes content", () => {
  it("carries a changelog entry for the current package version", () => {
    const packageVersion = versionFromPyproject("../pyproject.toml");

    expect(packageVersion).toBeDefined();
    expect(defaultProjectMeta.latestVersion).toBe(packageVersion);
    expect(releaseNotes[0]?.version).toBe(packageVersion);
  });

  it("lists releases newest first with no duplicates", () => {
    const versions = releaseNotes.map((entry) => entry.version);
    const sorted = [...versions].sort((a, b) =>
      b.localeCompare(a, undefined, { numeric: true }),
    );

    expect(versions).toEqual(sorted);
    expect(new Set(versions).size).toBe(versions.length);
  });

  it("keeps every entry presentable", () => {
    for (const entry of releaseNotes) {
      expect(entry.version).toMatch(/^\d+\.\d+\.\d+$/);
      expect(entry.title).not.toBe("");
      expect(entry.body).not.toBe("");
      expect(entry.highlights.length).toBeGreaterThan(0);
      // Curated highlights, not a changelog: details belong in CHANGELOG.md.
      expect(entry.highlights.length).toBeLessThanOrEqual(3);
    }
  });
});

describe("install content", () => {
  const readme = readFileSync("../README.md", "utf8");

  it("advertises the README one-line installer", () => {
    expect(readme).toContain(installCommand);
  });

  it("only quotes commands the README documents", () => {
    const commands = installNotes
      .flatMap((note) => note.split("`").filter((_, index) => index % 2 === 1))
      .filter((span) => /^(kickstart|pipx|brew) /.test(span));

    expect(commands.length).toBeGreaterThan(0);
    for (const command of commands) {
      expect(readme).toContain(command);
    }
  });
});
