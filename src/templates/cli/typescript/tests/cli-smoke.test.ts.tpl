import { describe, expect, it } from "vitest";
import { runCommand } from "@oclif/test";

describe("generated oclif CLI", () => {
  it("runs the check command", async () => {
    const { stdout } = await runCommand("check");

    expect(stdout.trim()).toBe("ok: local");
  });

  it("shows root help", async () => {
    const { stdout } = await runCommand("--help");

    expect(stdout).toContain("COMMANDS");
    expect(stdout).toContain("check");
  });

  it("shows version", async () => {
    const { stdout } = await runCommand("--version");

    expect(stdout).toContain("{{ package_name }}/0.1.0");
  });
});
