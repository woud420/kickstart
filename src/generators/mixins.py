"""Mixins for common generator functionality."""

from src.utils.github import create_repo


class GitHubMixin:
    """Mixin for generators that support GitHub repository creation."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Expect gh and name attributes to be set by the concrete class
    
    def create_github_repo_if_requested(self) -> None:
        """Create GitHub repository if the gh flag is set."""
        if hasattr(self, 'gh') and self.gh and hasattr(self, 'name'):
            create_repo(self.name)


class CommonTemplatesMixin:
    """Mixin for generators that use common template patterns."""
    
    def write_common_service_templates(self, language: str) -> None:
        """Write common templates for service projects."""
        if not hasattr(self, 'write_template'):
            raise AttributeError("Mixin requires write_template method")
        
        self.write_template(".gitignore", f"{language}/gitignore.tpl")
        self.write_template("Dockerfile", f"{language}/Dockerfile.tpl")
        self.write_template("Makefile", f"{language}/Makefile.tpl")
    
    def write_common_lib_templates(self, language: str) -> None:
        """Write common templates for library projects."""
        if not hasattr(self, 'write_template'):
            raise AttributeError("Mixin requires write_template method")
            
        self.write_template(".gitignore", f"{language}/gitignore.tpl")
        self.write_template("Makefile", f"{language}/Makefile.tpl")
        self.write_template("README.md", f"{language}/README.md.tpl")