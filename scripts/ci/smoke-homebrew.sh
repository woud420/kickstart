#!/usr/bin/env bash
# Run only in a disposable Homebrew environment with no kickstart installation.
set -euo pipefail

candidate="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
previous="${2:-}"
formula="kickstart-ci/tap/kickstart"
export HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_CLEANUP=1 HOMEBREW_NO_ANALYTICS=1
export KICKSTART_TELEMETRY_DISABLED=1

if brew list --versions kickstart >/dev/null 2>&1; then
  echo "Refusing to replace an existing kickstart installation." >&2
  exit 1
fi

scratch="$(mktemp -d)"
tap="$(brew --repository)/Library/Taps/kickstart-ci/homebrew-tap"
if [[ -e "$tap" ]]; then
  echo "Refusing to replace an existing kickstart-ci/tap checkout." >&2
  rmdir "$scratch"
  exit 1
fi

cleanup() {
  brew uninstall --force "$formula" || true
  rm -rf "$tap" "$scratch"
}
trap cleanup EXIT
mkdir -p "$tap/Formula"
git -C "$tap" init --quiet
git -C "$tap" remote add origin https://github.com/woud420/homebrew-tap

if [[ -n "$previous" ]]; then
  cp "$previous" "$tap/Formula/kickstart.rb"
  brew install --formula "$formula"
  brew test "$formula"
fi

cp "$candidate" "$tap/Formula/kickstart.rb"
brew readall --os=all --arch=all kickstart-ci/tap
brew style "$formula"
brew audit --formula "$formula"
if [[ -n "$previous" ]]; then
  brew upgrade --formula "$formula"
else
  brew install --formula "$formula"
fi
brew test "$formula"
brew uninstall --force "$formula"
test ! -e "$(brew --prefix)/bin/kickstart"
test ! -d "$(brew --cellar)/kickstart"
echo "Homebrew install, scaffold, ownership guards, and uninstall passed."
