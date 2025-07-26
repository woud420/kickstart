# Kickstart MCP Server

An MCP (Model Context Protocol) server that exposes kickstart's project scaffolding capabilities to AI models.

## What This Does

This MCP server allows AI models (like Claude) to directly use kickstart to generate projects through structured tool calls, rather than requiring manual CLI interaction.

## Quick Setup

### 1. Install Dependencies

```bash
cd tools/mcp-server
pip install -r requirements.txt
```

### 2. Configure Your MCP Client

#### For Claude Desktop
Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

#### For Claude Code CLI
```bash
claude-code config set mcp.servers.kickstart.command "python"
claude-code config set mcp.servers.kickstart.args "['/Users/jm/workspace/projects/kickstart/tools/mcp-server/mcp_server.py']"
```

### 3. Test the Setup

```bash
# Test the MCP server manually
cd /Users/jm/workspace/projects/kickstart
PYTHONPATH=. python tools/mcp-server/mcp_server.py
```

## Available Tools

### Project Creation Tools

- **`create_service`** - Backend services (Python/FastAPI, Rust/Actix, Go/Gin, TypeScript/Express)
- **`create_frontend`** - React frontends with modern tooling
- **`create_library`** - Library/package projects
- **`create_monorepo`** - Infrastructure monorepos with K8s/Terraform

### Discovery Tools

- **`list_templates`** - Show all available project templates and capabilities

## Example AI Interactions

Once configured, you can ask AI models:

> "Create a Python FastAPI service called 'user-service' in /tmp"

> "Generate a React frontend called 'dashboard' with TypeScript"

> "What project templates are available?"

> "Create a complete microservice stack with Go backend and React frontend"

## Architecture

```
tools/mcp-server/
├── mcp_server.py      # Main MCP server implementation
├── requirements.txt   # MCP dependencies
└── README.md         # This file
```

The server wraps your existing kickstart generators and exposes them as MCP tools with proper schemas and validation.

## Development

To modify or extend the MCP server:

1. Edit `mcp_server.py` to add new tools or modify existing ones
2. Update tool schemas in the `handle_list_tools()` function
3. Add corresponding logic in `handle_call_tool()`
4. Test with `python tools/mcp-server/mcp_server.py`

## Benefits

- **AI Integration**: Models can generate projects without CLI knowledge
- **Structured Input**: Tool schemas ensure proper parameter validation
- **Rich Output**: Detailed responses about created projects
- **Template Discovery**: AI can explore available templates dynamically
- **Error Handling**: Graceful error messages for debugging