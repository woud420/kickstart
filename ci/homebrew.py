"""Render the tap formula from verified stable-release binary archives."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re


STABLE_TAG = re.compile(r"v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")
REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
PLATFORMS = ("macos-arm64", "linux-arm64", "linux-x64")


@dataclass(frozen=True)
class Archive:
    name: str
    sha256: str


def verified_archive(directory: Path, platform: str) -> Archive:
    name = f"kickstart-{platform}-py3.14.tar.gz"
    archive = directory / name
    checksum = (directory / f"{name}.sha256").read_text(encoding="utf-8").split()
    if len(checksum) != 2 or Path(checksum[1]).name != name or not re.fullmatch(r"[0-9a-f]{64}", checksum[0]):
        raise ValueError(f"Invalid checksum file for {name}")
    with archive.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if checksum[0] != actual:
        raise ValueError(f"Checksum mismatch for {name}")
    return Archive(name, actual)


def render_formula(tag: str, directory: Path, repository: str = "woud420/kickstart") -> str:
    if STABLE_TAG.fullmatch(tag) is None or REPOSITORY.fullmatch(repository) is None:
        raise ValueError("Expected a stable vX.Y.Z tag and an owner/repository")
    mac, arm, intel = (verified_archive(directory, platform) for platform in PLATFORMS)
    base = f"https://github.com/{repository}/releases/download/{tag}"
    return f'''class Kickstart < Formula
  desc "Deterministic starter repos for humans and coding agents"
  homepage "https://kickstart-cli.org"

  on_macos do
    depends_on arch: :arm64
    depends_on macos: :sequoia
    on_arm do
      url "{base}/{mac.name}"
      sha256 "{mac.sha256}"
    end
    # Keep metadata loadable on Intel so the architecture requirement explains the failure.
    on_intel do
      url "{base}/{mac.name}"
      sha256 "{mac.sha256}"
    end
  end

  on_linux do
    on_arm do
      url "{base}/{arm.name}"
      sha256 "{arm.sha256}"
    end
    on_intel do
      url "{base}/{intel.name}"
      sha256 "{intel.sha256}"
    end
  end

  def install
    libexec.install Dir["*"]
    # Older releases have no package-manager guard, so keep it in the launcher.
    (bin/"kickstart").write <<~SH
      #!/bin/sh
      command="${{1-}}"
      if [ "$command" = "--" ]; then command="${{2-}}"; fi
      case "$command" in
        install|upgrade|uninstall|_managed-layout-handoff)
          echo "Homebrew manages this installation. Use brew upgrade woud420/tap/kickstart or brew uninstall woud420/tap/kickstart." >&2
          exit 1
          ;;
      esac
      exec "#{{libexec}}/kickstart" "$@"
    SH
  end

  def caveats
    <<~EOS
      Homebrew owns this installation. Use brew upgrade and brew uninstall.
      Release builds enable pseudonymous usage telemetry by default.
      Run kickstart telemetry disable to opt out.
      Remove any older ~/.local/bin/kickstart launcher if it shadows this one.
    EOS
  end

  test do
    ENV["KICKSTART_TELEMETRY_DISABLED"] = "1"
    assert_match version.to_s, shell_output("#{{bin}}/kickstart version")
    system bin/"kickstart", "create", "lib", "brew-smoke", "--root", testpath, "--lang", "python"
    assert_path_exists testpath/"brew-smoke/.kickstart/scaffold.json"
    %w[install upgrade uninstall _managed-layout-handoff].each do |command|
      assert_match "Homebrew manages", shell_output("#{{bin}}/kickstart #{{command}} 2>&1", 1)
      assert_match "Homebrew manages", shell_output("#{{bin}}/kickstart -- #{{command}} 2>&1", 1)
    end
  end
end
'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--repository", default="woud420/kickstart")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    formula = render_formula(args.tag, args.artifacts, args.repository)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(formula, encoding="utf-8")
    print(f"Wrote {args.output} for {args.tag}")


if __name__ == "__main__":
    main()
