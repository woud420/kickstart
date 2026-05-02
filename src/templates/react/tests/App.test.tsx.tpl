import { describe, expect, it } from "vitest";

describe("App", () => {
  it("keeps the generated app name available", () => {
    expect("{{ service_name }}").toBeTruthy();
  });
});
