# Workspace Projects Structure Analysis

## Overview
This document catalogs all projects found in ~/workspace, organized by language and structure.

---

## Python Projects

### kickstart
**Path:** `/Users/jm/workspace/projects/kickstart/`
**Type:** Python CLI Tool
**Structure:**
```
kickstart/
├── pyproject.toml          # Poetry project configuration
├── poetry.lock             # Dependency lock file  
├── Makefile               # Build automation
├── README.md              # Documentation
├── kickstart.py           # Entry point
├── src/
│   ├── __init__.py
│   ├── api.py            # API module
│   ├── cli/              # CLI interface
│   │   └── main.py
│   ├── generator/        # Project generators
│   │   ├── base.py      # Base generator class
│   │   ├── service.py   # Service generator
│   │   ├── frontend.py  # Frontend generator
│   │   ├── lib.py       # Library generator
│   │   └── monorepo.py  # Monorepo generator
│   └── utils/            # Utility modules
│       ├── fs.py        # File system operations
│       ├── updater.py   # Self-updater
│       └── template_registry.py
└── tests/                # Test suite
    ├── unit/
    └── integration/
```

### crm-ingestion
**Path:** `/Users/jm/workspace/projects/crm-ingestion/`
**Type:** Python Library
**Structure:**
```
crm-ingestion/
├── pyproject.toml         # Project configuration
├── uv.lock               # UV lock file
├── Makefile              # Build automation
├── README.md             # Documentation
├── src/
│   ├── __init__.py
│   └── py.typed          # Type hints marker
├── tests/                # Test suite
│   ├── __init__.py
│   ├── conftest.py      # Pytest configuration
│   ├── test_config.py
│   ├── test_formats.py
│   └── test_models.py
├── docs/                 # Documentation
│   └── crm_specific_field_handling.md
└── examples/             # Usage examples
    └── dao_usage.py
```

### kubitor
**Path:** `/Users/jm/workspace/projects/kubitor/`
**Type:** Python Kubernetes Scanner
**Structure:**
```
kubitor/
├── pyproject.toml        # Project configuration
├── requirements.txt      # Dependencies
├── requirements-dev.txt  # Dev dependencies
├── Makefile             # Build automation
├── README.md            # Documentation
├── src/
│   ├── __init__.py
│   └── main.py          # Entry point
├── tests/               # Test suite
│   ├── __init__.py
│   └── conftest.py     # Pytest configuration
├── docs/                # Documentation
│   ├── DATABASE_ARCHITECTURE.md
│   ├── INVENTORY.md
│   ├── MODELS.md
│   └── TESTING.md
└── examples/            # Usage examples
    └── annotation-config.yaml
```

### lang-chain-test
**Path:** `/Users/jm/workspace/syntin/lang-chain-test/`
**Type:** Python LangChain Application
**Structure:**
```
lang-chain-test/
├── pyproject.toml       # Project configuration
├── Makefile            # Build automation
├── README.md           # Documentation
├── env.example         # Environment template
├── src/
│   ├── __init__.py
│   ├── config.py       # Configuration
│   └── main.py         # Entry point
├── tests/              # Test suite
│   ├── __init__.py
│   ├── conftest.py    # Pytest configuration
│   ├── test_config.py
│   └── test_prompts.py
└── docker/             # Docker configuration
    └── Dockerfile
```

### otter-log-client
**Path:** `/Users/jm/workspace/syntin/otter-log-client/`
**Type:** Python API Client
**Structure:**
```
otter-log-client/
├── requirements.txt    # Dependencies
├── Makefile           # Build automation
├── main.py            # Entry point
├── auth.py            # Authentication module
└── put_data.py        # Data upload module
```

### ragserver
**Path:** `/Users/jm/workspace/syntin/ragserver/`
**Type:** Python RAG Server
**Structure:**
```
ragserver/
├── Dockerfile         # Container configuration
├── Makefile          # Build automation
├── README            # Documentation
├── env.txt.sample    # Environment template
├── src/
│   ├── ragserver.py  # Main server
│   ├── rag.py        # RAG implementation
│   ├── misc.py       # Utilities
│   └── universal.py  # Common functions
├── tests/            # Test files
│   ├── dirtest.json
│   ├── filetest.json
│   ├── metadata.json
│   └── rawtest.json
├── corpus/           # Document corpus
└── documentation/    # Documentation
    └── RAGSERVER.txt
```

### weather-ingestion / weather-gov-ingestion
**Path:** `/Users/jm/workspace/syntin/weather-ingestion/` and `/Users/jm/workspace/syntin/weather-gov-ingestion/`
**Type:** Python Data Ingestion Service
**Structure:**
```
weather-ingestion/
├── pyproject.toml       # Project configuration
├── requirements.txt     # Dependencies
├── Dockerfile          # Container configuration
├── Makefile           # Build automation
├── README.md          # Documentation
├── src/
│   ├── __init__.py
│   ├── cli.py         # CLI interface
│   └── main.py        # Entry point
├── tests/             # Test suite
│   ├── __init__.py
│   ├── run_all_tests.py
│   ├── test_config.py
│   ├── test_ingestion.py
│   ├── test_openapi_models.py
│   ├── test_rate_limiter.py
│   ├── test_sinks.py
│   └── test_smart_ingestion.py
├── schema/            # Database schemas
│   ├── README.md
│   └── weather_schema.sql
├── docs/              # Documentation
│   ├── polling-strategy.md
│   └── smart-ingestion-architecture.md
└── examples/          # Usage examples
    ├── basic_ingestion.py
    └── custom_sink_example.py
```

### velox-integrations
**Path:** `/Users/jm/workspace/hatch/velox-integrations/`
**Type:** Python Integration Library
**Structure:**
```
velox-integrations/
├── setup.py           # Setup configuration
├── requirements.txt   # Dependencies
├── Makefile          # Build automation
├── README.md         # Documentation
├── CLAUDE.md         # Claude AI documentation
├── src/
│   ├── __init__.py
│   ├── client_config.py
│   ├── config.py
│   ├── main.py
│   └── setup_hooks.py
├── tests/            # Test suite
│   └── __init__.py
└── velox_documentation.pdf/txt
```

---

## TypeScript/React Projects

### claudia
**Path:** `/Users/jm/workspace/projects/claudia/`
**Type:** Tauri Desktop App (React + Rust)
**Structure:**
```
claudia/
├── package.json          # Node dependencies
├── bun.lock             # Bun lock file
├── tsconfig.json        # TypeScript config
├── vite.config.ts       # Vite configuration
├── index.html           # Entry HTML
├── src/                 # React source
│   ├── App.tsx         # Main component
│   ├── main.tsx        # Entry point
│   ├── styles.css      # Styles
│   └── vite-env.d.ts   # Type definitions
├── src-tauri/           # Rust backend
│   ├── Cargo.toml      # Rust dependencies
│   ├── Cargo.lock      # Lock file
│   ├── build.rs        # Build script
│   └── tauri.conf.json # Tauri config
├── public/              # Static assets
│   ├── tauri.svg
│   └── vite.svg
├── cc_agents/           # Claude agents
│   ├── README.md
│   ├── git-commit-bot.claudia.json
│   ├── security-scanner.claudia.json
│   └── unit-tests-bot.claudia.json
└── scripts/             # Utility scripts
    └── bump-version.sh
```

### date-trust-score
**Path:** `/Users/jm/workspace/projects/date-trust-score/`
**Type:** React TypeScript Application
**Structure:**
```
date-trust-score/
├── package.json         # Dependencies
├── bun.lockb           # Bun lock file
├── tsconfig.json       # TypeScript config
├── vite.config.ts      # Vite configuration
├── tailwind.config.ts  # Tailwind CSS config
├── postcss.config.js   # PostCSS config
├── eslint.config.js    # ESLint config
├── components.json     # Component configuration
├── index.html          # Entry HTML
├── src/                # Source code
│   ├── App.tsx        # Main component
│   ├── App.css        # App styles
│   ├── main.tsx       # Entry point
│   ├── index.css      # Global styles
│   └── vite-env.d.ts  # Type definitions
├── backend/            # Backend service
│   ├── README.md
│   ├── package.json
│   └── tsconfig.json
└── public/             # Static assets
    ├── favicon.ico
    ├── placeholder.svg
    └── robots.txt
```

### otter-log-dashboard
**Path:** `/Users/jm/workspace/syntin/otter-log-dashboard/`
**Type:** React TypeScript Dashboard
**Structure:**
```
otter-log-dashboard/
├── package.json         # Dependencies
├── bun.lockb           # Bun lock file
├── tsconfig.json       # TypeScript config
├── vite.config.ts      # Vite configuration
├── vitest.config.ts    # Vitest configuration
├── tailwind.config.ts  # Tailwind CSS config
├── postcss.config.js   # PostCSS config
├── eslint.config.js    # ESLint config
├── components.json     # Component configuration
├── index.html          # Entry HTML
├── src/                # Source code
│   ├── App.tsx        # Main component
│   ├── main.tsx       # Entry point
│   ├── index.css      # Global styles
│   └── vite-env.d.ts  # Type definitions
├── tests/              # Test suite
│   ├── README.md
│   ├── commands.md
│   ├── setupTests.ts
│   └── vitest.config.ts
├── docker/             # Docker configuration
│   ├── Dockerfile
│   ├── Dockerfile.nginx
│   ├── nginx.conf
│   └── env.example
└── public/             # Static assets
    ├── favicon.ico
    ├── mockServiceWorker.js
    ├── placeholder.svg
    └── robots.txt
```

---

## Go Projects

### audit-log-service
**Path:** `/Users/jm/workspace/hatch/audit-log-service/`
**Type:** Go Microservice
**Structure:**
```
audit-log-service/
├── go.mod              # Go module file
├── go.sum              # Dependency checksums
├── Dockerfile          # Container configuration
├── docker-compose.yml  # Docker compose
├── Makefile           # Build automation
├── README.md          # Documentation
├── main.go            # Entry point
├── cmd/               # Command line tools
│   └── ingest/
│       └── main.go
├── src/               # Source code
│   ├── api/
│   │   └── audit_api.go
│   ├── handler/
│   │   ├── audit_handler.go
│   │   └── utils.go
│   ├── model/         # Data models
│   ├── modules/       # Application modules
│   │   ├── api.go
│   │   ├── app.go
│   │   ├── config.go
│   │   ├── handler.go
│   │   ├── repository.go
│   │   └── server.go
│   ├── routes/
│   │   └── routes.go
│   └── service/       # Business logic
├── test/              # Tests
│   ├── integration/
│   │   └── api_integration_test.go
│   └── unit/
├── scripts/           # Utility scripts
│   ├── generate_large_test_data.py
│   ├── ingest-data.sh
│   ├── recreate-opensearch-index.sh
│   └── run_tests.sh
└── examples/          # Example data
    └── users.json
```

### hatch-server
**Path:** `/Users/jm/workspace/hatch/hatch-server/`
**Type:** Go Backend Service
**Structure:**
```
hatch-server/
├── go.mod               # Go module file
├── go.sum               # Dependency checksums
├── Dockerfile           # Container configuration
├── docker-compose.yaml  # Docker compose
├── Makefile            # Build automation
├── README.md           # Documentation
├── config.toml         # Configuration file
├── business/           # Business logic layer
│   ├── acl.go
│   ├── audit.go
│   ├── boards.go
│   ├── campaigns.go
│   ├── contacts.go
│   ├── organizations.go
│   ├── users.go
│   └── ... (40+ business modules)
├── cfg/                # Configuration
│   └── model.go
├── clients/            # External clients
│   └── client.go
├── di/                 # Dependency injection
│   ├── provider.go
│   ├── backends.go
│   ├── biz.go
│   ├── clients.go
│   └── ... (8+ DI modules)
├── persistence/        # Data persistence layer
├── monitoring/         # Monitoring & telemetry
│   ├── init.go
│   ├── newrelic.go
│   └── trace.go
├── internal/           # Internal packages
├── tests/              # Python test suite
│   ├── conftest.py
│   ├── test_conftest.py
│   └── ... (test modules)
├── testFixtures/       # Test fixtures
│   ├── cleanup.go
│   ├── interfaces.go
│   └── phone.go
├── work/               # Background workers
│   ├── groupCounts.go
│   ├── looper.go
│   └── scheduled_message_worker.go
└── docs/               # Documentation
    ├── campaignLaunching.md
    ├── contactImporting.md
    ├── scheduled.md
    └── workflows.md
```

---

## Rust Projects

### otter-log
**Path:** `/Users/jm/workspace/syntin/otter-log/`
**Type:** Rust Web Service
**Structure:**
```
otter-log/
├── Cargo.toml          # Rust dependencies
├── Cargo.lock          # Lock file
├── Makefile           # Build automation
├── README.md          # Documentation
├── docker-compose.yml # Docker compose
├── env.example        # Environment template
├── src/               # Source code
│   ├── main.rs       # Entry point
│   ├── lib.rs        # Library root
│   ├── mod.rs        # Module definitions
│   ├── config.rs     # Configuration
│   └── config_test.rs # Config tests
├── tests/             # Integration tests
│   ├── auth_workflow.rs
│   └── workflow.rs
├── migrations/        # Database migrations
│   ├── 0001_consolidated_schema.sql
│   └── ... (7+ migration files)
├── docker/            # Docker configuration
│   ├── Dockerfile
│   └── entrypoint.sh
├── k8s/               # Kubernetes manifests
└── scripts/           # Utility scripts
    ├── Makefile
    ├── README.md
    └── test_api.py
```

---

## Elixir Projects

### hatch-elixir
**Path:** `/Users/jm/workspace/hatch/hatch-elixir/`
**Type:** Elixir Phoenix Application
**Structure:**
```
hatch-elixir/
├── mix.exs             # Mix project file
├── mix.lock            # Dependency lock
├── Dockerfile          # Container configuration
├── docker-compose.yaml # Docker compose
├── README.md           # Documentation
├── config/             # Configuration
│   ├── config.exs
│   ├── dev.exs
│   ├── prod.exs
│   ├── runtime.exs
│   └── test.exs
├── lib/                # Application code
│   ├── hatch.ex       # Application module
│   ├── hatch/         # Core modules
│   │   ├── application.ex
│   │   ├── accounts.ex
│   │   ├── campaigns.ex
│   │   ├── messaging.ex
│   │   ├── repo.ex
│   │   └── ... (15+ modules)
│   ├── hatch_web.ex   # Web module
│   └── hatch_web/     # Web components
│       ├── api_spec.ex
│       ├── channels.ex
│       ├── endpoint.ex
│       ├── router.ex
│       └── ... (10+ web modules)
├── priv/               # Private resources
├── rel/                # Release configuration
├── assets/             # Frontend assets
│   ├── css/
│   ├── js/
│   ├── package.json
│   └── tailwind.config.js
├── test/               # Test suite
│   └── test_helper.exs
└── documentation/      # Documentation
    ├── assistant/
    ├── billing/
    └── rabbitmq.md
```

### hatch-integrations
**Path:** `/Users/jm/workspace/hatch/hatch-integrations/`
**Type:** Elixir Microservice
**Structure:**
```
hatch-integrations/
├── mix.exs             # Mix project file
├── mix.lock            # Dependency lock
├── Dockerfile          # Container configuration
├── docker-compose.yaml # Docker compose
├── README.md           # Documentation
├── config/             # Configuration
│   ├── config.exs
│   ├── dev.exs
│   ├── prod.exs
│   ├── runtime.exs
│   └── test.exs
├── lib/                # Application code
│   ├── hatch_integrations.ex
│   └── hatch_integrations_web.ex
├── priv/               # Private resources
├── rel/                # Release configuration
├── src/                # Erlang source
│   └── otel_baggage_processor.erl
└── test/               # Test suite
    └── test_helper.exs
```

---

## C++ Projects

### cpp-code (Syntin)
**Path:** `/Users/jm/workspace/syntin/cpp-code/`
**Type:** C++ Multi-Component System
**Structure:**
```
cpp-code/
├── Makefile            # Build automation
├── README.md           # Documentation
├── Dockerfile          # Container configuration
├── docker-compose.yml  # Docker compose
├── aerozine/           # Component: Analytics Bridge
│   ├── Makefile
│   ├── Dockerfile
│   ├── main.cpp
│   ├── analytics.cpp/h
│   └── bridge.cpp/h
├── ammonium/           # Component: Aggregator
│   ├── Makefile
│   ├── main.cpp
│   └── aggregator.cpp/h
├── fluorine/           # Component: ML/AI Engine
│   ├── Makefile
│   ├── Dockerfile
│   ├── main.cpp
│   ├── encoder.cpp/h
│   ├── decoder.cpp/h
│   ├── embedding.cpp/h
│   ├── kalman.cpp/h
│   └── ... (20+ modules)
├── gasoline/           # Component: Flag Generator
│   ├── Makefile
│   ├── main.cpp
│   └── flaggen.cpp/h
├── hydrazine/          # Component: Processor
│   ├── Makefile
│   ├── Dockerfile
│   ├── main.cpp
│   ├── processor.cpp/h
│   ├── CE.cpp/h
│   └── timer.cpp/h
├── methane/            # Component: Database
│   ├── Makefile
│   ├── Dockerfile
│   ├── main.cpp
│   ├── db.cpp/h
│   └── cassconsumer.cpp/h
├── nitric/             # Component: Profiler
│   ├── Makefile
│   ├── main.cpp
│   ├── catalog.cpp/h
│   ├── profile.cpp/h
│   └── kde.cpp/h
├── utilities/          # Shared utilities
│   └── utilities.h
├── external/           # External dependencies
├── examples/           # Usage examples
│   ├── basic_usage.cpp
│   ├── pipeline_demo.cpp
│   └── health_demo.cpp
└── monitoring/         # Monitoring config
    └── prometheus.yml
```

---

## Infrastructure Projects

### helm-hatch-server
**Path:** `/Users/jm/workspace/hatch/helm-hatch-server/`
**Type:** Helm Chart
**Structure:**
```
helm-hatch-server/
├── Chart.yaml          # Chart metadata
├── Chart.lock          # Dependency lock
├── README.md           # Documentation
├── values.yaml         # Default values
├── values-prod.yaml    # Production values
├── values-staging.yaml # Staging values
├── templates/          # K8s templates
│   ├── _helpers.tpl
│   ├── rollout.yaml
│   ├── services.yaml
│   ├── secrets.yaml
│   ├── hpa.yaml
│   └── serviceaccount.yaml
└── charts/             # Dependency charts
    ├── mongodb-11.0.6.tgz
    ├── rabbitmq-8.30.0.tgz
    └── redis-16.5.5.tgz
```

### helm-hatch-integrations
**Path:** `/Users/jm/workspace/hatch/helm-hatch-integrations/`
**Type:** Helm Chart
**Structure:**
```
helm-hatch-integrations/
├── Chart.yaml          # Chart metadata
├── README.md           # Documentation
├── values.yaml         # Default values
├── values-prod.yaml    # Production values
├── values-staging.yaml # Staging values
├── templates/          # K8s templates
│   ├── _helpers.tpl
│   ├── deployment.yaml
│   ├── rollout.yaml
│   ├── service.yaml
│   ├── secrets.yaml
│   ├── hpa.yaml
│   └── serviceaccount.yaml
└── upsert-sealed-secret.sh
```

### infrastructure
**Path:** `/Users/jm/workspace/hatch/infrastructure/`
**Type:** Infrastructure as Code
**Structure:**
```
infrastructure/
├── README.md           # Documentation
├── kubernetes/         # K8s configurations
│   ├── README.md
│   ├── clusterissuer.yaml
│   ├── clustersetup.sh
│   ├── prod-eks.yaml
│   └── staging-eks.yaml
└── terraform/          # Terraform modules
```

---

## Configuration/Utility Projects

### dotfiles
**Path:** `/Users/jm/workspace/projects/dotfiles/`
**Type:** Shell Configuration
**Structure:**
```
dotfiles/
├── Makefile            # Installation automation
├── README.md           # Documentation
├── install.sh          # Installation script
├── bash/               # Bash configurations
│   ├── prompt
│   ├── 16bit.colors
│   └── escape_functions.default
├── config/             # Application configs
│   ├── kitty.conf
│   └── current-theme.conf
├── darwin/             # macOS specific
│   ├── Brewfile
│   └── kitty.conf
├── linux/              # Linux specific
│   └── README.md
├── git/                # Git configurations
├── shell/              # Shell configurations
├── scripts/            # Utility scripts
│   ├── minimal-bashrc.sh
│   ├── quick-install.sh
│   ├── ssh-copy-dotfiles.sh
│   └── update_cursor_tools.py
└── prompts/            # AI prompts
    ├── cursor_generator.md
    └── md-file-aggregator.md
```

---

## Documentation Projects

### jm
**Path:** `/Users/jm/workspace/projects/jm/`
**Type:** Personal Documentation
**Structure:**
```
jm/
├── childhood-incident-analysis.md
├── life-timeline.md
└── relationship-timeline.md
```

### website
**Path:** `/Users/jm/workspace/syntin/website/`
**Type:** Static Website
**Structure:**
```
website/
├── index.html          # Main page
├── syntin.css          # Styles
├── blog/               # Blog posts
│   └── ai-revolution-advertising-machine-learning-marketing-roi.html
└── images/             # Assets
    ├── syntin-logo-tag.png
    ├── syntin-icons_*.svg
    └── ... (15+ images)
```

---

## Multi-Language Projects

### interview/hatch
**Path:** `/Users/jm/workspace/interview/hatch/`
**Type:** Python Interview Project
**Structure:**
```
hatch/
├── Makefile           # Build automation
├── README.md          # Documentation
├── requirements.txt   # Dependencies
├── pytest.ini         # Test configuration
├── src/               # Source code
│   ├── __init__.py
│   └── main.py
├── tests/             # Test suite
└── dev/               # Development environment
    └── pyvenv.cfg
```

---

## Summary Statistics

### Language Distribution:
- **Python**: 10 projects
- **TypeScript/React**: 3 projects  
- **Go**: 2 projects
- **Rust**: 1 project (+ 1 hybrid with React)
- **Elixir**: 2 projects
- **C++**: 1 project (multi-component)
- **Helm/K8s**: 3 projects
- **Static/Config**: 3 projects

### Project Types:
- **Web Services/APIs**: 8 projects
- **CLI Tools**: 3 projects
- **Libraries**: 3 projects
- **Frontend Applications**: 3 projects
- **Infrastructure/DevOps**: 3 projects
- **Data Processing**: 3 projects
- **Documentation**: 2 projects

### Key Technologies:
- **Containerization**: Docker (12 projects)
- **Orchestration**: Kubernetes/Helm (3 projects)
- **Testing**: Pytest, Jest, Vitest, Go test
- **Build Tools**: Make (15 projects), Poetry, Cargo, Mix
- **Databases**: PostgreSQL, MongoDB, Redis, Cassandra
- **Message Queues**: RabbitMQ
- **Monitoring**: Prometheus, NewRelic, OpenTelemetry