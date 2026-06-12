import { describe, expect, it } from "vitest";

import { versionFromPyproject } from "../scripts/render-release-config";
import { defaultProjectMeta, releaseNotes } from "../src/site/content";

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
    }
  });
});
