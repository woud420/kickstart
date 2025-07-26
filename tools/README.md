# Tools

This directory contains additional tooling and integrations for kickstart.

## Available Tools

### MCP Server (`mcp-server/`)
Model Context Protocol server that exposes kickstart functionality to AI models like Claude.

- **Purpose**: Allow AI models to generate projects directly through structured tool calls
- **Setup**: See `mcp-server/README.md` for configuration instructions
- **Usage**: Once configured, AI models can create services, frontends, libraries, and monorepos

## Adding New Tools

When adding new tools to this directory:

1. Create a dedicated subdirectory (e.g., `tools/new-tool/`)
2. Include a README.md explaining the tool's purpose and setup
3. Add any dependencies in the tool's directory
4. Update this README to list the new tool

## Project Structure Philosophy

The `tools/` directory follows the principle of keeping auxiliary tooling separate from core kickstart functionality:

- **Core**: `src/` contains the main kickstart library and CLI
- **Tools**: `tools/` contains integrations, utilities, and extensions
- **Templates**: `src/templates/` contains project scaffolding templates

This structure makes it easy to:
- Find and manage different types of tooling
- Package tools independently if needed
- Maintain clear separation of concerns