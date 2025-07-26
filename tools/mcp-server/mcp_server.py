#!/usr/bin/env python3
"""
Kickstart MCP Server

Model Context Protocol server that exposes kickstart's project scaffolding 
capabilities to AI models through structured tool calls.

Location: tools/mcp-server/mcp_server.py
Purpose: Enable AI models to generate projects using kickstart without CLI interaction
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# Import your existing kickstart modules
from src.generators.service import ServiceGenerator
from src.generators.frontend import FrontendGenerator
from src.generators.lib import LibGenerator
from src.generators.monorepo import MonorepoGenerator
from src.utils.config import load_config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kickstart-mcp")

# Initialize the MCP server
server = Server("kickstart")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools for project scaffolding."""
    return [
        Tool(
            name="create_service",
            description="Create a new backend service project with modern toolchain",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Service name (will be used for project folder)",
                    },
                    "language": {
                        "type": "string",
                        "enum": ["python", "rust", "go", "typescript", "ts", "node"],
                        "description": "Programming language for the service",
                    },
                    "root_path": {
                        "type": "string",
                        "description": "Root directory where project should be created (optional)",
                        "default": ".",
                    },
                    "github_repo": {
                        "type": "boolean",
                        "description": "Create GitHub repository automatically",
                        "default": False,
                    },
                    "helm_chart": {
                        "type": "boolean", 
                        "description": "Include Helm chart for Kubernetes deployment",
                        "default": False,
                    },
                },
                "required": ["name", "language"],
            },
        ),
        Tool(
            name="create_frontend",
            description="Create a new React frontend project",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Frontend project name",
                    },
                    "root_path": {
                        "type": "string",
                        "description": "Root directory where project should be created (optional)",
                        "default": ".",
                    },
                    "github_repo": {
                        "type": "boolean",
                        "description": "Create GitHub repository automatically", 
                        "default": False,
                    },
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="create_library",
            description="Create a new library/package project",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Library name",
                    },
                    "language": {
                        "type": "string",
                        "enum": ["python", "rust", "go", "typescript"],
                        "description": "Programming language for the library",
                    },
                    "root_path": {
                        "type": "string",
                        "description": "Root directory where project should be created (optional)",
                        "default": ".",
                    },
                    "github_repo": {
                        "type": "boolean",
                        "description": "Create GitHub repository automatically",
                        "default": False,
                    },
                },
                "required": ["name", "language"],
            },
        ),
        Tool(
            name="create_monorepo",
            description="Create a new monorepo with infrastructure tooling",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Monorepo name",
                    },
                    "root_path": {
                        "type": "string", 
                        "description": "Root directory where project should be created (optional)",
                        "default": ".",
                    },
                    "github_repo": {
                        "type": "boolean",
                        "description": "Create GitHub repository automatically",
                        "default": False,
                    },
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="list_templates",
            description="List available project templates and their capabilities",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls for project generation."""
    try:
        config = load_config()
        
        if name == "create_service":
            # Extract arguments
            service_name = arguments["name"]
            language = arguments["language"]
            root_path = arguments.get("root_path", ".")
            github_repo = arguments.get("github_repo", False)
            helm_chart = arguments.get("helm_chart", False)
            
            # Create service generator
            generator = ServiceGenerator(
                name=service_name,
                lang=language,
                gh=github_repo,
                config=config,
                helm=helm_chart,
                root=root_path if root_path != "." else None
            )
            
            # Generate the project
            generator.create()
            
            project_path = Path(root_path) / service_name
            
            return [
                TextContent(
                    type="text",
                    text=f"✅ {language.title()} service '{service_name}' created successfully!\n\n"
                         f"📁 Location: {project_path.absolute()}\n"
                         f"🚀 Language: {language}\n"
                         f"📦 GitHub Repo: {'Yes' if github_repo else 'No'}\n"
                         f"⛵ Helm Chart: {'Yes' if helm_chart else 'No'}\n\n"
                         f"Next steps:\n"
                         f"1. cd {service_name}\n"
                         f"2. make install\n"
                         f"3. make dev"
                )
            ]
            
        elif name == "create_frontend":
            service_name = arguments["name"]
            root_path = arguments.get("root_path", ".")
            github_repo = arguments.get("github_repo", False)
            
            generator = FrontendGenerator(
                name=service_name,
                gh=github_repo,
                config=config,
                root=root_path if root_path != "." else None
            )
            
            generator.create()
            project_path = Path(root_path) / service_name
            
            return [
                TextContent(
                    type="text",
                    text=f"✅ React frontend '{service_name}' created successfully!\n\n"
                         f"📁 Location: {project_path.absolute()}\n"
                         f"⚛️ Framework: React\n"
                         f"📦 GitHub Repo: {'Yes' if github_repo else 'No'}\n\n"
                         f"Next steps:\n"
                         f"1. cd {service_name}\n"
                         f"2. npm install\n" 
                         f"3. npm run dev"
                )
            ]
            
        elif name == "create_library":
            service_name = arguments["name"]
            language = arguments["language"]
            root_path = arguments.get("root_path", ".")
            github_repo = arguments.get("github_repo", False)
            
            generator = LibGenerator(
                name=service_name,
                lang=language,
                gh=github_repo,
                config=config,
                root=root_path if root_path != "." else None
            )
            
            generator.create()
            project_path = Path(root_path) / service_name
            
            return [
                TextContent(
                    type="text",
                    text=f"✅ {language.title()} library '{service_name}' created successfully!\n\n"
                         f"📁 Location: {project_path.absolute()}\n"
                         f"📚 Type: Library/Package\n"
                         f"🚀 Language: {language}\n"
                         f"📦 GitHub Repo: {'Yes' if github_repo else 'No'}"
                )
            ]
            
        elif name == "create_monorepo":
            service_name = arguments["name"]
            root_path = arguments.get("root_path", ".")
            github_repo = arguments.get("github_repo", False)
            
            generator = MonorepoGenerator(
                name=service_name,
                gh=github_repo,
                config=config,
                root=root_path if root_path != "." else None
            )
            
            generator.create()
            project_path = Path(root_path) / service_name
            
            return [
                TextContent(
                    type="text",
                    text=f"✅ Monorepo '{service_name}' created successfully!\n\n"
                         f"📁 Location: {project_path.absolute()}\n"
                         f"🏗️ Type: Infrastructure Monorepo\n"
                         f"📦 GitHub Repo: {'Yes' if github_repo else 'No'}\n\n"
                         f"Includes: Kubernetes, Terraform, CI/CD pipelines"
                )
            ]
            
        elif name == "list_templates":
            template_info = {
                "services": {
                    "python": "FastAPI service with uv, ruff, mypy, pytest",
                    "rust": "Actix-web service with cargo-watch, clippy, rustfmt",
                    "go": "Gin service with air, staticcheck, go fmt",
                    "typescript": "Express.js service with tsx, ESLint, Prettier, Jest"
                },
                "frontend": {
                    "react": "React app with Vite, TypeScript, Tailwind CSS"
                },
                "libraries": {
                    "python": "Python package with uv and pytest",
                    "rust": "Rust crate with standard tooling",
                    "go": "Go module with testing setup",
                    "typescript": "TypeScript library with build pipeline"
                },
                "infrastructure": {
                    "monorepo": "Kubernetes + Terraform + CI/CD monorepo"
                }
            }
            
            template_text = "# Available Kickstart Templates\n\n"
            
            for category, templates in template_info.items():
                template_text += f"## {category.title()}\n\n"
                for name, description in templates.items():
                    template_text += f"- **{name}**: {description}\n"
                template_text += "\n"
            
            template_text += "All templates include:\n"
            template_text += "- Modern development toolchain\n"
            template_text += "- Comprehensive Makefiles with colored output\n"
            template_text += "- Working tests and CI setup\n"
            template_text += "- Docker configuration\n"
            template_text += "- Environment configuration\n"
            template_text += "- Rich documentation\n"
            
            return [
                TextContent(
                    type="text",
                    text=template_text
                )
            ]
            
        else:
            return [
                TextContent(
                    type="text",
                    text=f"❌ Unknown tool: {name}"
                )
            ]
            
    except Exception as e:
        logger.error(f"Error handling tool call {name}: {e}")
        return [
            TextContent(
                type="text",
                text=f"❌ Error: {str(e)}"
            )
        ]

async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="kickstart",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())