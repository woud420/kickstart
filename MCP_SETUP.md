# Kickstart MCP Server Setup

This guide shows you how to set up Kickstart as an MCP (Model Context Protocol) server so AI models can use it directly to generate projects.

## Quick Setup

### 1. Install MCP Dependencies

```bash
# Install MCP server dependencies
make mcp-setup
```

### 2. Configure Claude Desktop (Recommended)

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "kickstart": {
      "command": "python",
      "args": ["/path/to/your/kickstart/tools/mcp-server/mcp_server.py"],
      "env": {
        "PYTHONPATH": "/path/to/your/kickstart"
      }
    }
  }
}
```

Replace `/path/to/your/kickstart` with the actual path to your kickstart installation.

### 3. Restart Claude Desktop

The kickstart tools will now be available to Claude!

## Available Tools

Once configured, AI models can use these tools:

### `create_service`
Create backend services in Python (FastAPI), Rust (Actix-web), Go (Gin), or TypeScript (Express.js)

**Parameters:**
- `name` (required): Service name
- `language` (required): "python", "rust", "go", "typescript" 
- `root_path` (optional): Directory to create project in
- `github_repo` (optional): Auto-create GitHub repo
- `helm_chart` (optional): Include Kubernetes Helm chart

### `create_frontend` 
Create React frontend projects with Vite and TypeScript

**Parameters:**
- `name` (required): Project name
- `root_path` (optional): Directory to create project in
- `github_repo` (optional): Auto-create GitHub repo

### `create_library`
Create library/package projects

**Parameters:**
- `name` (required): Library name
- `language` (required): "python", "rust", "go", "typescript"
- `root_path` (optional): Directory to create project in
- `github_repo` (optional): Auto-create GitHub repo

### `create_monorepo`
Create infrastructure monorepos with Kubernetes, Terraform, and CI/CD

**Parameters:**
- `name` (required): Monorepo name
- `root_path` (optional): Directory to create project in
- `github_repo` (optional): Auto-create GitHub repo

### `list_templates`
List all available templates and their features

## Alternative Setup Methods

### Option 2: Claude Code (CLI)

If you're using Claude Code CLI, you can configure MCP servers in settings:

```bash
# Add to your Claude Code settings
claude-code config set mcp.servers.kickstart.command "python"
claude-code config set mcp.servers.kickstart.args "['/path/to/kickstart/mcp_server.py']"
```

### Option 3: Other MCP Clients

For other MCP clients, use the server directly:

```bash
# Run the MCP server manually
python /Users/jm/workspace/projects/kickstart/mcp_server.py
```

## Testing the Setup

Once configured, you can test by asking Claude:

> "Create a new Python FastAPI service called 'my-api' in /tmp"

> "List all available project templates"

> "Create a React frontend called 'my-app' with GitHub repository"

## Troubleshooting

### Common Issues

1. **Module not found errors**: Ensure PYTHONPATH includes kickstart directory
2. **Permission errors**: Make sure the MCP server script is executable
3. **Path issues**: Use absolute paths in the MCP configuration

### Debug Mode

To enable debug logging, set environment variable:

```bash
export KICKSTART_MCP_DEBUG=1
```

### Manual Testing

Test the MCP server manually:

```bash
cd /Users/jm/workspace/projects/kickstart
source .venv/bin/activate
python mcp_server.py
```

## Benefits of MCP Integration

- **Direct AI Access**: Models can generate projects without manual CLI commands
- **Structured Interaction**: Tools have clear schemas and validation
- **Rich Responses**: Detailed feedback about created projects
- **Error Handling**: Graceful error messages for debugging
- **Template Discovery**: Models can explore available templates

## Security Considerations

- The MCP server runs with your user permissions
- It can create files and directories anywhere specified
- GitHub integration uses your configured Git credentials
- Consider running in restricted environments for production use