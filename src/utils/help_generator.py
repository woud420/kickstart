"""
Dynamic Help Generation for Kickstart CLI

This module automatically generates help text by scanning templates and generators,
with manual overrides for better descriptions.
"""

import json
from pathlib import Path
from typing import Dict, List, Set, Optional

class KickstartHelpGenerator:
    """Generates CLI help dynamically from project structure."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            # Auto-detect from this file's location
            base_dir = Path(__file__).parent.parent
        
        self.base_dir = base_dir
        self.templates_dir = base_dir / "templates"
        self.generators_dir = base_dir / "generators"
        
        # Manual overrides for better descriptions
        self.language_overrides = {
            "python": {
                "framework": "FastAPI",
                "description": "FastAPI service with uv, ruff, mypy, pytest",
                "project_types": ["service", "lib"]
            },
            "rust": {
                "framework": "Actix-web", 
                "description": "Actix-web service with cargo-watch, clippy, rustfmt",
                "project_types": ["service", "lib"]
            },
            "go": {
                "framework": "Gin",
                "description": "Gin service with air, staticcheck, go fmt",
                "project_types": ["service", "lib"]
            },
            "typescript": {
                "framework": "Express.js",
                "description": "Express.js service with tsx, ESLint, Prettier, Jest",
                "project_types": ["service", "lib"]
            },
            "react": {
                "framework": "React",
                "description": "React app with Vite, TypeScript, Tailwind CSS",
                "project_types": ["frontend"]
            }
        }
        
        self.project_type_descriptions = {
            "service": "Backend API service",
            "frontend": "React frontend with modern tooling", 
            "lib": "Library/package project",
            "cli": "Command-line interface tool",
            "monorepo": "Infrastructure monorepo with Kubernetes and Terraform"
        }
    
    def get_available_languages(self) -> List[str]:
        """Get languages by scanning template directories."""
        if not self.templates_dir.exists():
            return list(self.language_overrides.keys())
        
        languages = []
        for item in self.templates_dir.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                languages.append(item.name)
        
        return sorted(languages)
    
    def get_available_project_types(self) -> List[str]:
        """Get project types by scanning generator files."""
        if not self.generators_dir.exists():
            return list(self.project_type_descriptions.keys())
        
        types = []
        for file in self.generators_dir.glob("*.py"):
            if file.name not in ["__init__.py", "base.py"]:
                types.append(file.stem)
        
        return sorted(types)
    
    def get_language_info(self, language: str) -> Dict[str, any]:
        """Get information about a specific language."""
        # Start with override if available
        if language in self.language_overrides:
            return self.language_overrides[language].copy()
        
        # Try to infer from templates
        template_dir = self.templates_dir / language
        if template_dir.exists():
            return self._infer_language_info(template_dir)
        
        # Fallback
        return {
            "framework": "Unknown",
            "description": f"{language.title()} project",
            "project_types": ["service"]
        }
    
    def _infer_language_info(self, template_dir: Path) -> Dict[str, any]:
        """Infer language info from template files."""
        info = {
            "framework": "Unknown",
            "description": f"{template_dir.name.title()} project",
            "project_types": ["service"]
        }
        
        # Look for framework clues in template files
        template_files = list(template_dir.glob("*.tpl"))
        
        for file in template_files:
            try:
                content = file.read_text().lower()
                if "fastapi" in content:
                    info["framework"] = "FastAPI"
                elif "actix" in content:
                    info["framework"] = "Actix-web"
                elif "gin" in content:
                    info["framework"] = "Gin"
                elif "express" in content:
                    info["framework"] = "Express.js"
                elif "react" in content:
                    info["framework"] = "React"
                    info["project_types"] = ["frontend"]
            except:
                continue
        
        return info
    
    def generate_language_help_text(self) -> str:
        """Generate help text for language option."""
        languages = self.get_available_languages()
        return f"Programming language: {' | '.join(languages)}"
    
    def generate_project_type_help_text(self) -> str:
        """Generate help text for project type argument."""
        types = self.get_available_project_types()
        return f"Project type: {' | '.join(types)}"
    
    def generate_examples(self) -> List[str]:
        """Generate usage examples."""
        languages = self.get_available_languages()
        types = self.get_available_project_types()
        
        examples = []
        
        # Service examples
        if "service" in types:
            if "python" in languages:
                examples.append("kickstart create service my-api --lang python")
            if "rust" in languages:
                examples.append("kickstart create lib my-utils --lang rust --gh")
        
        # Frontend examples  
        if "frontend" in types:
            examples.append("kickstart create frontend my-app --root /tmp")
        
        # Monorepo examples
        if "monorepo" in types:
            examples.append("kickstart create monorepo my-platform --helm")
        
        return examples
    
    def generate_detailed_help_docstring(self) -> str:
        """Generate the detailed docstring for the create command."""
        examples = self.generate_examples()
        languages = self.get_available_languages()
        types = self.get_available_project_types()
        
        docstring = """Create a new project with modern tooling and best practices.
    
Examples:"""
        
        for example in examples:
            docstring += f"\n        {example}"
        
        docstring += f"""
    
Supported project types:"""
        
        for ptype in types:
            desc = self.project_type_descriptions.get(ptype, f"{ptype.title()} project")
            docstring += f"\n        {ptype:<10} - {desc}"
        
        docstring += f"""
    
Supported languages:"""
        
        for lang in languages:
            info = self.get_language_info(lang)
            desc = info.get("description", f"{lang.title()} project")
            docstring += f"\n        {lang:<10} - {desc}"
        
        return docstring
    
    def generate_list_command_output(self) -> str:
        """Generate output for the 'kickstart list' command."""
        languages = self.get_available_languages()
        
        # Group by project type
        type_groups = {}
        for lang in languages:
            info = self.get_language_info(lang)
            for ptype in info.get("project_types", ["service"]):
                if ptype not in type_groups:
                    type_groups[ptype] = []
                type_groups[ptype].append((lang, info))
        
        output = "Available Kickstart Templates\n\n"
        
        for ptype in sorted(type_groups.keys()):
            output += f"{ptype.title()}:\n"
            for lang, info in sorted(type_groups[ptype]):
                desc = info.get("description", f"{lang.title()} project")
                output += f"  • {lang}: {desc}\n"
            output += "\n"
        
        output += "All templates include:\n"
        features = [
            "Modern development toolchain",
            "Comprehensive Makefiles with colored output", 
            "Working tests and CI setup",
            "Docker configuration",
            "Environment configuration",
            "Rich documentation"
        ]
        
        for feature in features:
            output += f"  • {feature}\n"
        
        return output

# Singleton instance
_help_generator = None

def get_help_generator() -> KickstartHelpGenerator:
    """Get the global help generator instance."""
    global _help_generator
    if _help_generator is None:
        _help_generator = KickstartHelpGenerator()
    return _help_generator