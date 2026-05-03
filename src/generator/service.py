from collections.abc import Sequence
from pathlib import Path
import logging
from src.generator.base import BaseGenerator
from src.generator.language_setup import (
    ContentFile,
    cpp_service_content_files,
    go_service_content_files,
    rust_service_content_files,
    typescript_service_content_files,
    typescript_service_templates,
)
from src.generator.template_plans import python_service_core_template_plan
from src.utils.logger import success, warn
from src.utils.github import create_repo
from src.utils.extension_manager import ExtensionManager
from src.stack.profile import stack_registry
from src.stack.types import TemplateConfig
from src.generator.layouts import python_package_directories, service_directories, worker_directories
from src.generator.scaffold_contract import ScaffoldArtifacts, ScaffoldContract, ScaffoldServiceExtensions
from src.generator.service_capabilities import ServiceExtensionSelection, validate_service_extensions
from src.generator.specs import ServiceSpec
from src.generator.template_plan import TemplatePlan
from src.utils.types import GeneratorConfig
from src.utils.error_handling import (
    safe_operation_context, LanguageNotSupportedError
)

logger = logging.getLogger(__name__)


class ServiceGenerator(BaseGenerator):
    """Generator for creating microservice projects.
    
    This generator creates a complete microservice project structure with
    language-specific templates, Docker configuration, testing framework,
    and optional Helm charts for Kubernetes deployment.
    
    Attributes:
        lang: Programming language for the service (python, rust, typescript, cpp, go)
        gh: Whether to create a GitHub repository
        helm: Whether to include Helm chart scaffolding
        lang_template_dir: Path to language-specific templates
    """
    
    lang: str
    runtime: str
    gh: bool
    helm: bool
    database: str | None
    cache: str | None
    auth: str | None
    framework: str | None
    lang_template_dir: Path
    extension_manager: ExtensionManager
    spec: ServiceSpec

    def __init__(
        self,
        name: str,
        lang: str,
        gh: bool,
        config: GeneratorConfig,
        helm: bool = False,
        root: str | None = None,
        database: str | None = None,
        cache: str | None = None,
        auth: str | None = None,
        framework: str | None = None,
        runtime: str = "container",
    ) -> None:
        """Initialize the ServiceGenerator.
        
        Args:
            name: Name of the service to create
            lang: Programming language (python, rust, typescript/ts, cpp, go)
            gh: Whether to create a GitHub repository
            config: Configuration dictionary with user preferences
            helm: Whether to include Helm chart scaffolding
            root: Root directory for project creation (optional)
            database: Database extension (postgres, mysql, sqlite)
            cache: Cache extension (redis, memcached)
            auth: Authentication extension (jwt, oauth)
            framework: HTTP framework (None for FastAPI default, minimal for standard library)
            runtime: Runtime target (container or cloudflare-workers)
            
        Raises:
            ValueError: If unsupported language is specified
        """
        spec = ServiceSpec.from_options(
            name=name,
            language=lang,
            gh=gh,
            config=config,
            helm=helm,
            root=root,
            database=database,
            cache=cache,
            auth=auth,
            framework=framework,
            runtime=runtime,
        )
        super().__init__(spec.name, spec.config, spec.root)
        self.spec = spec
        self.lang = spec.language
        self.runtime = spec.runtime
        self.gh = spec.gh
        self.helm = spec.helm
        self.database = spec.database
        self.cache = spec.cache
        self.auth = spec.auth
        self.framework = spec.framework
        self.lang_template_dir = self.template_dir / self.lang
        self.extension_manager = ExtensionManager()

    def _normalize_runtime(self, runtime: str) -> str:
        """Normalize runtime aliases to canonical service runtime ids."""
        return stack_registry.normalize_service_runtime(runtime)

    def create(self) -> None:
        """Create a complete microservice project.

        This method orchestrates the entire service creation process using the
        standardized create flow from BaseGenerator:
        1. Validates project can be created (directory doesn't exist)
        2. Checks language template availability
        3. Creates directory structure
        4. Writes common template files (README, Dockerfile, etc.)
        5. Sets up language-specific files and dependencies
        6. Creates Helm charts if requested
        7. Optionally creates GitHub repository

        Returns:
            None

        Raises:
            LanguageNotSupportedError: If unsupported language is specified
        """
        extension_selection = self._validate_extension_selection()
        profile = stack_registry.service_selection(self.lang, self.runtime, helm=self.helm)

        if profile.runtime == "cloudflare-workers":
            self._create_cloudflare_worker_project()
            return

        # Check if templates exist for the language
        if not self.lang_template_dir.exists():
            raise LanguageNotSupportedError(f"No templates found for language: {self.lang}")

        directories = service_directories()

        template_plan = TemplatePlan.from_templates(profile.templates)

        # Configuration for the common create flow
        architecture_title: str = f"{self.name} Architecture Notes"
        success_message: str = f"{self.lang.title()} service '{self.name}' created successfully in '{self.project}'!"
        def github_create_fn() -> bool | None:
            return create_repo(self.name) if self.gh else None

        # Execute common create flow with service-specific setup
        success = self.execute_create_flow(
            directories=directories,
            template_plan=template_plan,
            architecture_title=architecture_title,
            scaffold_contract=ScaffoldContract(
                project_kind="service",
                execution_models=("container",),
                runtime_platforms=("kubernetes",) if self.helm else ("local",),
                artifacts=ScaffoldArtifacts(
                    image="dockerfile",
                    kubernetes="helm" if self.helm else None,
                ),
                service_extensions=self._scaffold_service_extensions(extension_selection),
            ),
            success_message=success_message,
            language_setup_fn=self._setup_service_specific,
            additional_setup_fn=self._setup_helm_if_requested,
            github_create_fn=github_create_fn if self.gh else None
        )

        if not success:
            warn(f"Failed to create {self.lang} service '{self.name}'")

    def _validate_extension_selection(self) -> ServiceExtensionSelection:
        """Validate database, cache, and auth extensions for this service."""
        return validate_service_extensions(
            language=self.lang,
            runtime=self.runtime,
            framework=self.framework,
            database=self.database,
            cache=self.cache,
            auth=self.auth,
        )

    def _scaffold_service_extensions(
        self,
        selection: ServiceExtensionSelection,
    ) -> ScaffoldServiceExtensions:
        """Convert validated extension selections to manifest metadata."""
        return ScaffoldServiceExtensions(
            database=selection.database,
            cache=selection.cache,
            auth=selection.auth,
        )

    def _create_cloudflare_worker_project(self) -> None:
        """Create a Cloudflare Worker service project."""
        stack_registry.service_selection(self.lang, self.runtime, helm=self.helm)

        worker_template_dir = self.template_dir / "cloudflare-workers" / self.lang
        if not worker_template_dir.exists():
            raise LanguageNotSupportedError(f"No Cloudflare Worker templates found for language: {self.lang}")

        directories = worker_directories()
        template_plan = self._cloudflare_worker_template_plan()

        architecture_title = f"{self.name} Cloudflare Worker Architecture Notes"
        success_message = f"{self.lang.title()} Cloudflare Worker '{self.name}' created successfully in '{self.project}'!"

        def github_create_fn() -> bool | None:
            return create_repo(self.name) if self.gh else None

        success = self.execute_create_flow(
            directories=directories,
            template_plan=template_plan,
            architecture_title=architecture_title,
            scaffold_contract=ScaffoldContract(
                project_kind="worker",
                execution_models=("cloudflare-worker",),
                runtime_platforms=("cloudflare-workers",),
                artifacts=ScaffoldArtifacts(worker="wrangler"),
                provider_targets=("cloudflare",),
            ),
            success_message=success_message,
            github_create_fn=github_create_fn if self.gh else None,
        )

        if not success:
            warn(f"Failed to create {self.lang} Cloudflare Worker '{self.name}'")

    def _cloudflare_worker_template_configs(self) -> list[dict[str, str]]:
        """Return template mappings for Cloudflare Worker services."""
        return stack_registry.service_template_configs(self.lang, "cloudflare-workers")

    def _cloudflare_worker_template_plan(self) -> TemplatePlan:
        """Return a typed template plan for Cloudflare Worker services."""
        selection = stack_registry.service_selection(self.lang, "cloudflare-workers")
        return TemplatePlan.from_templates(selection.templates)
    
    def _setup_service_specific(self) -> bool:
        """Setup service-specific files and structure.

        Creates language-specific project files, directory structure,
        and dependency configuration.

        This method dispatches to language-specific setup methods based
        on the configured language.

        Returns:
            True if setup was successful, False otherwise
        """
        with safe_operation_context("Service-specific setup", log_errors=True):
            # Write direct content
            self.write_content(".env.example", "EXAMPLE_ENV_VAR=value\n")

            # Language-specific files and structure
            if self.lang == "python":
                self._create_python_structure()
            elif self.lang == "rust":
                self._create_rust_structure()
            elif self.lang == "cpp":
                self._create_cpp_structure()
            elif self.lang == "go":
                self._create_go_structure()
            elif self.lang == "typescript":
                self._create_typescript_structure()
            else:
                raise LanguageNotSupportedError(f"Unsupported language: {self.lang}")

            return True

    def _setup_helm_if_requested(self) -> bool:
        """Setup Helm charts if requested.

        Returns:
            True if Helm setup was successful or not requested, False if failed
        """
        if not self.helm:
            return True

        with safe_operation_context("Helm chart creation", log_errors=True):
            self._create_helm_chart()
            return True

    def _create_python_structure(self) -> None:
        """Create Python-specific project structure.

        Sets up a Python microservice with:
        - FastAPI framework by default (modern, async, type-safe)
        - Minimal http.server framework when --framework minimal is used
        - Optional extensions (database, cache, auth) via progressive enhancement
        - Clean architecture with proper separation of concerns
        - Type hints and proper error handling
        """
        # Create __init__.py files for all Python packages
        for package_path in python_package_directories():
            self.write_content(f"{package_path}/__init__.py", "")

        for template in python_service_core_template_plan(self.framework).entries():
            self.write_template(template.target, template.template, **template.vars)
        
        # Add extensions based on flags (only for FastAPI framework)
        if self.framework != "minimal":
            self._add_python_extensions()
        
        # Create environment example
        self.write_content(".env.example", self._read_template_text("python/core/env.example.tpl"))
        
        # Create basic migration file as example
        self.write_content("migrations/001_initial.sql", self._read_template_text("python/core/migrations/001_initial.sql.tpl"))
        self.write_content("tests/test_smoke.py", "def test_generated_scaffold() -> None:\n    assert True\n")
        
        self.create_directories(["migrations"])

    def _read_template_text(self, template_path: str) -> str:
        """Read source text from a scaffold template."""
        return (self.template_dir / template_path).read_text(encoding="utf-8")

    def _add_python_extensions(self) -> None:
        """Add extension functionality based on flags.

        This method uses ExtensionManager to add database, cache, and authentication
        extensions based on the flags provided during initialization.
        """
        # Apply extensions using the extension manager
        extensions_added, all_extension_requirements = self.extension_manager.apply_extensions(
            writer=self,
            database=self.database,
            cache=self.cache,
            auth=self.auth
        )

        # Update requirements.txt with extensions
        if all_extension_requirements:
            extension_requirements = "\n\n# Extension requirements\n" + "\n".join(all_extension_requirements) + "\n"

            # Read core requirements and append extensions
            try:
                with open(self.project / "requirements.txt", "r") as f:
                    current_requirements = f.read()
                enhanced_requirements = current_requirements + extension_requirements
                self.write_content("requirements.txt", enhanced_requirements)
            except FileNotFoundError:
                # If core requirements don't exist, create with extensions only
                self.write_content("requirements.txt", "\n".join(all_extension_requirements))

        # Log what was added
        if extensions_added:
            from src.utils.logger import success
            success(f"Extensions added: {', '.join(extensions_added)}")

    def _create_rust_structure(self) -> None:
        """Create Rust-specific project structure.
        
        Sets up a Rust microservice with:
        - mod.rs files for module organization
        - Actix-web-based main.rs with basic HTTP server
        - Cargo.toml with common dependencies
        - Proper crate structure
        """
        include_postgres_database = self.database == "postgres"
        include_redis_cache = self.cache == "redis"
        include_jwt_auth = self.auth == "jwt"
        self._write_content_files(
            rust_service_content_files(
                include_postgres_database=include_postgres_database,
                include_redis_cache=include_redis_cache,
                include_jwt_auth=include_jwt_auth,
            )
        )
        if include_postgres_database:
            self.write_template("src/clients/database.rs", "rust/extensions/database/postgres.rs.tpl")
            self.create_directories(["migrations"])
            self.write_template("migrations/001_initial.sql", "rust/extensions/database/migrations.sql.tpl")
        if include_redis_cache:
            self.write_template("src/clients/cache.rs", "rust/extensions/cache/redis.rs.tpl")
        if include_jwt_auth:
            self.write_template("src/handler/auth.rs", "rust/extensions/auth/jwt.rs.tpl")

        if include_postgres_database or include_redis_cache or include_jwt_auth:
            env_content = "EXAMPLE_ENV_VAR=value\n"
            if include_postgres_database:
                env_content += "DATABASE_URL=postgres://postgres:postgres@127.0.0.1:5432/postgres\n"
            if include_redis_cache:
                env_content += "REDIS_URL=redis://127.0.0.1:6379/0\n"
            if include_jwt_auth:
                env_content += f"JWT_SECRET=change-me-change-me\nJWT_ISSUER={self.name}\n"
            self.write_content(".env.example", env_content)

        cargo_vars: dict[str, str] = {}
        if include_postgres_database:
            cargo_vars["database"] = "postgres"
        if include_redis_cache:
            cargo_vars["cache"] = "redis"
        if include_jwt_auth:
            cargo_vars["auth"] = "jwt"
        self.write_template("Cargo.toml", "rust/Cargo.toml.tpl", **cargo_vars)

    def _create_cpp_structure(self) -> None:
        """Create C++-specific project structure.

        Sets up a C++ service with CMake, a small executable, and header files
        that match the generated source layout.
        """
        self._write_content_files(cpp_service_content_files())
        self.write_template("CMakeLists.txt", "cpp/CMakeLists.txt.tpl")

    def _create_go_structure(self) -> None:
        """Create Go-specific project structure.
        
        Sets up a Go microservice with:
        - main.go with basic HTTP server using net/http
        - go.mod file for module definition
        - .gitkeep files for empty directories
        - Standard Go project layout
        """
        self._write_content_files(go_service_content_files())
        self.write_template("go.mod", "go/go.mod.tpl")

    def _create_typescript_structure(self) -> None:
        """Create TypeScript-specific service structure.

        Sets up a Fastify service with strict TypeScript, environment parsing,
        a health route, and a small test harness.
        """
        include_postgres_database = self.database == "postgres"
        include_redis_cache = self.cache == "redis"
        include_jwt_auth = self.auth == "jwt"
        self._write_template_configs(
            typescript_service_templates(
                include_postgres_database=include_postgres_database,
                include_redis_cache=include_redis_cache,
                include_jwt_auth=include_jwt_auth,
            )
        )
        jwt_issuer = self.name if include_jwt_auth else None
        self._write_content_files(
            typescript_service_content_files(
                include_postgres_database=include_postgres_database,
                include_redis_cache=include_redis_cache,
                jwt_issuer=jwt_issuer,
            )
        )
        if include_postgres_database:
            self.write_template("src/clients/database.ts", "typescript/src/clients/database.ts.tpl")
            self.create_directories(["migrations"])
            self.write_template("migrations/001_initial.sql", "typescript/extensions/database/migrations.sql.tpl")
        if include_redis_cache:
            self.write_template("src/clients/cache.ts", "typescript/src/clients/cache.ts.tpl")
        if include_jwt_auth:
            self.write_template("src/handler/auth.ts", "typescript/src/handler/auth.ts.tpl")
        if include_postgres_database or include_redis_cache or include_jwt_auth:
            package_vars: dict[str, str] = {}
            if include_postgres_database:
                package_vars["database"] = "postgres"
            if include_redis_cache:
                package_vars["cache"] = "redis"
            if include_jwt_auth:
                package_vars["auth"] = "jwt"
            self.write_template("package.json", "typescript/package.json.tpl", **package_vars)

    def _write_content_files(self, files: Sequence[ContentFile]) -> None:
        """Write direct content files from a typed setup plan."""
        for file in files:
            self.write_content(file.target, file.content)

    def _write_template_configs(self, templates: Sequence[TemplateConfig]) -> None:
        """Write template files from typed template configs."""
        for template in templates:
            self.write_template(template.target, template.template, **template.vars)

    def _create_helm_chart(self) -> None:
        """Create Helm chart structure and files.
        
        Generates a complete Helm chart for Kubernetes deployment including:
        - Chart.yaml with metadata
        - values.yaml with default configuration
        - deployment.yaml template for application deployment
        - Proper Helm chart directory structure
        
        The chart is created in helm/{service_name}/ directory.
        """
        chart_root = f"helm/{self.name}"
        self.create_directories([f"{chart_root}/templates"])

        for template in stack_registry.helm_template_configs():
            target = template.target.removeprefix("infra/helm/example-service/")
            self.write_template(f"{chart_root}/{target}", f"monorepo/{template.template}")

        success("Helm chart scaffolded")
