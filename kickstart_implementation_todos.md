# Kickstart Template Implementation TODOs

## Phase 1: Python Template Improvements

### TODO 1: Create Python Repository Pattern Templates
- [ ] Create `/templates/python/repository/base.py.tpl` with BaseRepository abstract class
  - Generic type support with TypeVar
  - Abstract methods: get, list, create, update, delete
  - Async/await support
- [ ] Create `/templates/python/repository/user_repo.py.tpl` with example UserRepository
  - Inherits from BaseRepository
  - Composition with DAO injection
  - Domain-specific methods (e.g., get_by_email)
- [ ] Create `/templates/python/repository/__init__.py.tpl` with exports

### TODO 2: Create Python DAO Layer Templates
- [ ] Create `/templates/python/dao/base.py.tpl` with BaseDAO abstract class
  - Database-specific operations
  - Connection management
- [ ] Create `/templates/python/dao/postgres/user_dao.py.tpl` with PostgreSQL implementation
  - Raw SQL queries using asyncpg or psycopg3
  - Connection pool usage
  - Error handling and transaction support
- [ ] Create `/templates/python/dao/postgres/__init__.py.tpl`

### TODO 3: Create Python Service Layer Templates
- [ ] Create `/templates/python/core/services/base_service.py.tpl` with base service patterns
- [ ] Create `/templates/python/core/services/user_service.py.tpl` with UserService example
  - Repository injection via constructor
  - Business logic methods
  - Transaction coordination
- [ ] Create `/templates/python/core/validators/user_validator.py.tpl` with validation logic

### TODO 4: Create Python Model Templates with 4-Level Structure
- [ ] Create `/templates/python/models/entities/user/user.py.tpl` with User entity
  - Dataclass or Pydantic model
  - Business entity representation
- [ ] Create `/templates/python/models/entities/user/profile.py.tpl` (example of 4-level depth)
- [ ] Create `/templates/python/models/dto/requests.py.tpl` with request DTOs
- [ ] Create `/templates/python/models/dto/responses.py.tpl` with response DTOs
- [ ] Create `/templates/python/models/schemas.py.tpl` with Pydantic schemas

### TODO 5: Create Python API Layer Templates
- [ ] Create `/templates/python/api/routes/user_routes.py.tpl` with FastAPI/Flask routes
  - Service injection
  - DTO transformation
  - Error handling
- [ ] Create `/templates/python/api/middleware/auth.py.tpl` with authentication middleware
- [ ] Create `/templates/python/api/middleware/logging.py.tpl` with logging middleware

### TODO 6: Create Python Infrastructure Templates
- [ ] Create `/templates/python/infrastructure/database/connection.py.tpl`
  - Connection pool setup
  - Database configuration
- [ ] Create `/templates/python/infrastructure/cache/redis_cache.py.tpl`
- [ ] Create `/templates/python/infrastructure/external/payment_client.py.tpl` (example external service)

### TODO 7: Create Python Configuration Templates
- [ ] Create `/templates/python/config/settings.py.tpl` with environment-based config
  - Using python-dotenv or pydantic-settings
  - Validation on startup
- [ ] Create `/templates/python/config/constants.py.tpl` with app constants

### TODO 8: Update Python Main Entry Point
- [ ] Create `/templates/python/main.py.tpl` with proper dependency injection setup
  - Wire up DAO → Repository → Service → API layers
  - Application startup/shutdown hooks
  - Graceful shutdown handling

### TODO 9: Create Python Test Structure Templates
- [ ] Create `/templates/python/tests/unit/services/test_user_service.py.tpl`
- [ ] Create `/templates/python/tests/integration/repository/test_user_repo.py.tpl`
- [ ] Create `/templates/python/tests/fixtures/users.json.tpl`

---

## Phase 2: Rust Template Improvements

### TODO 10: Create Rust Repository Pattern Templates
- [ ] Create `/templates/rust/repository/traits.rs.tpl` with Repository trait
  - Async trait with associated Error type
  - Generic over entity type
- [ ] Create `/templates/rust/repository/user_repo.rs.tpl` with UserRepository implementation
- [ ] Create `/templates/rust/repository/mod.rs.tpl` with module exports

### TODO 11: Create Rust DAO Layer Templates
- [ ] Create `/templates/rust/dao/postgres/user_dao.rs.tpl` with sqlx implementation
- [ ] Create `/templates/rust/dao/postgres/mod.rs.tpl`
- [ ] Create `/templates/rust/dao/mod.rs.tpl`

### TODO 12: Create Rust Service Layer Templates
- [ ] Create `/templates/rust/core/services/user_service.rs.tpl`
  - Repository struct field
  - impl new() for dependency injection
- [ ] Create `/templates/rust/core/services/mod.rs.tpl`
- [ ] Create `/templates/rust/core/validators/mod.rs.tpl`

### TODO 13: Create Rust Model Templates with Proper Module Structure
- [ ] Create `/templates/rust/models/entities/user.rs.tpl` with User struct
- [ ] Create `/templates/rust/models/entities/mod.rs.tpl`
- [ ] Create `/templates/rust/models/dto/requests.rs.tpl`
- [ ] Create `/templates/rust/models/dto/responses.rs.tpl`
- [ ] Create `/templates/rust/models/dto/mod.rs.tpl`
- [ ] Create `/templates/rust/models/mod.rs.tpl`

### TODO 14: Create Rust API Layer Templates
- [ ] Create `/templates/rust/api/routes/user_routes.rs.tpl` with axum/actix handlers
- [ ] Create `/templates/rust/api/routes/mod.rs.tpl`
- [ ] Create `/templates/rust/api/middleware/auth.rs.tpl`
- [ ] Create `/templates/rust/api/middleware/mod.rs.tpl`
- [ ] Create `/templates/rust/api/mod.rs.tpl`

### TODO 15: Create Rust Infrastructure Templates
- [ ] Create `/templates/rust/infrastructure/database.rs.tpl` with connection pool
- [ ] Create `/templates/rust/infrastructure/cache.rs.tpl`
- [ ] Create `/templates/rust/infrastructure/mod.rs.tpl`

### TODO 16: Create Rust Configuration Templates
- [ ] Create `/templates/rust/config/settings.rs.tpl` with serde-based config
- [ ] Create `/templates/rust/config/mod.rs.tpl`

### TODO 17: Update Rust Entry Points
- [ ] Create `/templates/rust/main.rs.tpl` with tokio runtime and dependency wiring
- [ ] Create `/templates/rust/lib.rs.tpl` with module declarations

---

## Phase 3: Go Template Improvements

### TODO 18: Create Go Repository Pattern Templates
- [ ] Create `/templates/go/internal/repository/interfaces.go.tpl` with UserRepository interface
- [ ] Create `/templates/go/internal/repository/user_repo.go.tpl` with implementation
  - Struct with dao field (composition)
  - Constructor function NewUserRepository

### TODO 19: Create Go DAO Layer Templates
- [ ] Create `/templates/go/internal/dao/interfaces.go.tpl` with DAO interfaces
- [ ] Create `/templates/go/internal/dao/postgres/user_dao.go.tpl` with SQL implementation
- [ ] Create `/templates/go/internal/dao/postgres/conn.go.tpl` with connection management

### TODO 20: Create Go Service Layer Templates
- [ ] Create `/templates/go/internal/core/services/user_service.go.tpl`
  - Struct with repository fields
  - NewUserService constructor
  - Context propagation in all methods
- [ ] Create `/templates/go/internal/core/validators/user_validator.go.tpl`

### TODO 21: Create Go Model Templates with Proper Package Structure
- [ ] Create `/templates/go/internal/models/entities/user.go.tpl`
- [ ] Create `/templates/go/internal/models/entities/product.go.tpl`
- [ ] Create `/templates/go/internal/models/dto/requests.go.tpl`
- [ ] Create `/templates/go/internal/models/dto/responses.go.tpl`

### TODO 22: Create Go API Layer Templates
- [ ] Create `/templates/go/internal/api/handlers/user_handler.go.tpl`
  - Handler struct with service injection
  - HTTP handler methods
- [ ] Create `/templates/go/internal/api/handlers/health.go.tpl`
- [ ] Create `/templates/go/internal/api/middleware/auth.go.tpl`
- [ ] Create `/templates/go/internal/api/middleware/logging.go.tpl`
- [ ] Create `/templates/go/internal/api/router.go.tpl` with route setup

### TODO 23: Create Go Infrastructure Templates
- [ ] Create `/templates/go/internal/infrastructure/database/postgres.go.tpl`
- [ ] Create `/templates/go/internal/infrastructure/cache/redis.go.tpl`

### TODO 24: Create Go Configuration Templates
- [ ] Create `/templates/go/internal/config/config.go.tpl` with viper or env-based config

### TODO 25: Create Go Entry Point
- [ ] Create `/templates/go/cmd/server/main.go.tpl` with dependency wiring
  - Create all layers and wire them together
  - Graceful shutdown handling

---

## Phase 4: Generator Updates

### TODO 26: Update ServiceGenerator Class
- [ ] Modify `ServiceGenerator._create_python_structure()` to create new directory structure:
  ```python
  directories = [
      "models/entities", "models/dto",
      "core/services", "core/validators",
      "repository", "dao/postgres",
      "api/routes", "api/middleware",
      "infrastructure/database", "infrastructure/cache",
      "config", "tests/unit", "tests/integration", "tests/fixtures"
  ]
  ```
- [ ] Update template mappings to use new template files
- [ ] Add support for 4-level directory creation

### TODO 27: Update LibraryGenerator Class
- [ ] Add repository pattern templates for library projects
- [ ] Include example service layer for libraries
- [ ] Add proper test structure

### TODO 28: Update CLIGenerator Class
- [ ] Add command pattern templates
- [ ] Include configuration management
- [ ] Add progress indicator templates

### TODO 29: Create Template Registry Enhancements
- [ ] Add method to handle 4-level template paths
- [ ] Create template categories: "repository", "dao", "service", "api", "infrastructure"
- [ ] Add template composition support (base + additions)

### TODO 30: Add Progressive Enhancement Flags
- [ ] Add `--minimal` flag to create bare-bones structure
- [ ] Add `--with-docker` flag to include Docker templates
- [ ] Add `--with-k8s` flag to include Kubernetes templates
- [ ] Add `--with-ci` flag to include GitHub Actions templates
- [ ] Add `--pattern` flag with options: "repository", "simple", "microservice"

---

## Phase 5: Infrastructure Templates

### TODO 31: Create Docker Templates
- [ ] Create `/templates/docker/Dockerfile.python.tpl` with multi-stage build
- [ ] Create `/templates/docker/Dockerfile.rust.tpl` with cargo caching
- [ ] Create `/templates/docker/Dockerfile.go.tpl` with module caching
- [ ] Create `/templates/docker/docker-compose.yml.tpl` with service + database

### TODO 32: Create Kubernetes Templates
- [ ] Create `/templates/k8s/deployment.yaml.tpl` with simple deployment
- [ ] Create `/templates/k8s/service.yaml.tpl` with service definition
- [ ] Create `/templates/k8s/configmap.yaml.tpl` for configuration
- [ ] Create `/templates/k8s/secret.yaml.tpl` for secrets (sealed)

### TODO 33: Create CI/CD Templates
- [ ] Create `/templates/ci/github-actions.yml.tpl` with test + build + deploy
- [ ] Create `/templates/ci/gitlab-ci.yml.tpl` as alternative

### TODO 34: Create Makefile Templates
- [ ] Create `/templates/Makefile.python.tpl` with common Python commands
- [ ] Create `/templates/Makefile.rust.tpl` with Cargo commands
- [ ] Create `/templates/Makefile.go.tpl` with Go commands
- [ ] Include: run, test, build, migrate, lint, format, clean

### TODO 35: Create Migration Templates
- [ ] Create `/templates/migrations/001_init.sql.tpl` with initial schema
- [ ] Create `/templates/migrations/README.md.tpl` with migration instructions

---

## Phase 6: Documentation Templates

### TODO 36: Create README Templates
- [ ] Create `/templates/README.python.tpl` with Python-specific setup
- [ ] Create `/templates/README.rust.tpl` with Rust-specific setup
- [ ] Create `/templates/README.go.tpl` with Go-specific setup
- [ ] Include: Quick start (3 commands), API docs, Architecture overview

### TODO 37: Create Architecture Documentation
- [ ] Create `/templates/docs/ARCHITECTURE.md.tpl` explaining the layers
- [ ] Create `/templates/docs/API.md.tpl` with API documentation template
- [ ] Create `/templates/docs/DATABASE.md.tpl` with schema documentation

### TODO 38: Create Example Files
- [ ] Create `/templates/examples/basic_usage.py.tpl` for Python libraries
- [ ] Create `/templates/examples/basic_usage.rs.tpl` for Rust libraries
- [ ] Create `/templates/examples/basic_usage.go.tpl` for Go libraries

---

## Phase 7: Testing and Validation

### TODO 39: Create Integration Tests for Generators
- [ ] Test that Python service generator creates all expected directories
- [ ] Test that templates are properly rendered with variables
- [ ] Test that generated projects can build and run
- [ ] Test progressive enhancement flags

### TODO 40: Create Template Validation
- [ ] Ensure each template compiles/runs in its language
- [ ] Validate that repository pattern works with different databases
- [ ] Test that services can be mocked for testing
- [ ] Verify 4-level directory paths work correctly

### TODO 41: Update Existing Tests
- [ ] Update `test_service_generator.py` for new structure
- [ ] Update `test_library_generator.py` for new patterns
- [ ] Update `test_cli_generator.py` for new templates

---

## Phase 8: TypeScript/React and Java Templates (Lower Priority)

### TODO 42: Create TypeScript Service Templates
- [ ] Repository pattern with TypeORM or Prisma
- [ ] Service layer with dependency injection
- [ ] Express/Fastify route handlers
- [ ] Proper TypeScript types throughout

### TODO 43: Create React Application Templates
- [ ] Feature-based folder structure
- [ ] Custom hooks for business logic
- [ ] API client with proper typing
- [ ] No Redux by default, just Context

### TODO 44: Create Java Templates
- [ ] Repository pattern without unnecessary interfaces
- [ ] Service layer with constructor injection
- [ ] REST controllers with Spring Boot (optional)
- [ ] Records for DTOs (Java 14+)

---

## Implementation Order

1. Start with TODO 26 (Update ServiceGenerator) - Core infrastructure
2. Then TODOs 1-9 (Python templates) - Most common use case
3. Then TODO 30 (Progressive enhancement flags) - Better UX
4. Then TODOs 10-17 (Rust templates) - Second priority language
5. Then TODOs 18-25 (Go templates) - Third priority language
6. Then TODOs 31-35 (Infrastructure templates) - Deployment support
7. Then TODOs 36-38 (Documentation) - Better developer experience
8. Then TODOs 39-41 (Testing) - Ensure quality
9. Then TODOs 42-44 (TypeScript/Java) - Additional language support

## Success Criteria

- [ ] Generated Python project follows Repository/DAO/Service pattern
- [ ] Generated Rust project has proper module structure with traits
- [ ] Generated Go project uses internal packages correctly
- [ ] All projects support 4-level directory depth where appropriate
- [ ] Composition over inheritance is default in all templates
- [ ] Generated projects can be built and run immediately
- [ ] Tests in generated projects actually test business logic
- [ ] Documentation is comprehensive and helpful