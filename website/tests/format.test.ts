import { describe, expect, it } from "vitest";

import { formatCommand, projectNameFromCommand, renderOutputTree, renderOutputTreeHtml } from "../src/site/format";

describe("example formatting", () => {
  it("renders advertised paths as a tree, collapsing single-child directories", () => {
    const tree = renderOutputTree("api", [
      "Dockerfile",
      "src/main.py",
      "src/routes/health.py",
      "src/routes/users.py",
      ".kickstart/scaffold.json",
      "apps/",
      "docs/architecture/README.md",
      "docs/contracts/README.md",
    ]);

    expect(tree).toBe(
      [
        "api/",
        "├── Dockerfile",
        "├── src/",
        "│   ├── main.py",
        "│   └── routes/",
        "│       ├── health.py",
        "│       └── users.py",
        "├── .kickstart/scaffold.json",
        "├── apps/",
        "└── docs/",
        "    ├── architecture/README.md",
        "    └── contracts/README.md",
      ].join("\n"),
    );
  });

  it("summarizes folders below the depth limit", () => {
    const tree = renderOutputTree(
      "platform",
      ["apps/", "infra/k8s/base/service.yaml", "infra/k8s/overlays/dev/", "infra/terraform/main.tf", "AGENTS.md"],
      1,
    );

    expect(tree).toBe(["platform/", "├── apps/", "├── infra/ (3 paths)", "└── AGENTS.md"].join("\n"));
    expect(renderOutputTreeHtml(tree)).toContain('├── infra/ <span class="tree-count">(3 paths)</span>');
  });

  it("names the tree root after the scaffolded project", () => {
    expect(projectNameFromCommand("kickstart create service edge-site --lang typescript")).toBe("edge-site");
  });

  it("puts one flag per line with shell continuations", () => {
    expect(formatCommand("kickstart create service api --lang python --auth jwt")).toBe(
      "kickstart create service api \\\n    --lang python \\\n    --auth jwt",
    );
    expect(formatCommand("kickstart create lib core")).toBe("kickstart create lib core");
  });

  it("highlights agent-facing paths and escapes everything else", () => {
    const html = renderOutputTreeHtml(renderOutputTree("a<b", ["AGENTS.md", ".agents/skills/README.md", "src/<x>.ts"]));

    expect(html).toBe(
      [
        "a&lt;b/",
        '├── <span class="agent-path">AGENTS.md</span>',
        '├── <span class="agent-path">.agents/skills/README.md</span>',
        "└── src/&lt;x&gt;.ts",
      ].join("\n"),
    );
  });
});
