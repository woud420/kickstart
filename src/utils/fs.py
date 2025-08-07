from pathlib import Path
import re


def write_file(path: Path, template: Path | str, **vars):
    """Write ``path`` from a template using UTF-8 encoding.

    Templates can be provided as a :class:`~pathlib.Path` or a string. When a
    path is supplied, the file is read as UTF-8 and ``{{INCLUDE:filename}}``
    directives within the template are processed. The resulting content is
    written to ``path`` using UTF-8.
    """
    if isinstance(template, Path):
        content = template.read_text(encoding="utf-8")
    else:
        content = template

    # Handle template composition (includes)
    content = _process_includes(content, template if isinstance(template, Path) else None, **vars)
    
    # Replace variables
    for key, value in vars.items():
        content = content.replace(f"{{{{{key.upper()}}}}}", str(value))

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _process_includes(content: str, template_path: Path | None, **vars) -> str:
    """Process ``{{INCLUDE:filename}}`` directives, reading files as UTF-8."""
    if template_path is None:
        return content
        
    template_dir = template_path.parent
    shared_dir = template_dir.parent / "_shared"
    
    # Find all include directives
    include_pattern = r'\{\{INCLUDE:([^}]+)\}\}'
    
    def replace_include(match):
        include_file = match.group(1)
        
        # Try shared directory first, then local
        for include_dir in [shared_dir, template_dir]:
            include_path = include_dir / include_file
            if include_path.exists():
                include_content = include_path.read_text(encoding="utf-8")
                # Recursively process includes in the included file
                return _process_includes(include_content, include_path, **vars)
        
        return f"<!-- Include not found: {include_file} -->"
    
    return re.sub(include_pattern, replace_include, content)

def compose_template(parts: list[str], template_dir: Path, **vars) -> str:
    """Compose a template from multiple parts, reading each as UTF-8."""
    shared_dir = template_dir.parent / "_shared"
    content_parts = []
    
    for part_name in parts:
        # Try shared directory first, then local
        for part_dir in [shared_dir, template_dir]:
            part_path = part_dir / f"{part_name}.tpl"
            if part_path.exists():
                part_content = part_path.read_text(encoding="utf-8")
                # Process includes within each part
                part_content = _process_includes(part_content, part_path, **vars)
                content_parts.append(part_content)
                break
        else:
            content_parts.append(f"<!-- Part not found: {part_name} -->")
    
    content = "\n\n".join(content_parts)
    
    # Replace variables
    for key, value in vars.items():
        content = content.replace(f"{{{{{key.upper()}}}}}", str(value))
    
    return content
