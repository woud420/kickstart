# 🚀 Kickstart v0.1.0

The first public release of **Kickstart**, an opinionated scaffolding tool for full-stack projects with strong infra and CI/CD support.

## ✨ Features

- 🔧 Create structured **backend services** (`python`, `rust`, `ts-node`, `cpp`)
- 🖥️ Generate modern **frontend apps** (React/TS)
- 📦 Define **libraries** and **CLI tools** as standalone modules
- 🏗️ Spin up an entire **infrastructure monorepo**:
  - Kustomize overlays OR Helm charts (via `--helm`)
  - Docker Compose for local dev
  - Terraform for cloud provisioning
  - GitHub Actions for CI/CD pipelines
- 🛠️ Built-in **Makefiles**, `.gitignore`, `.env.example`, `README.md`, `architecture/`
- 🧪 Supports unit, integration, and e2e test layout
- 📦 Package as a **single binary** using `shiv`
- 🔄 Self-updating with `kickstart upgrade`
- 🔁 Shell autocompletion with `kickstart completion [bash|zsh]`

## 📦 Installation

```bash
curl -L https://github.com/YOUR_USERNAME/kickstart/releases/download/v0.1.0/kickstart -o /usr/local/bin/kickstart
chmod +x /usr/local/bin/kickstart
****
