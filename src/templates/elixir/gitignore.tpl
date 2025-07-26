# The directory Mix will write compiled artifacts to.
/_build/

# If you run "mix test --cover", coverage assets end up here.
/cover/

# The directory Mix downloads your dependencies sources to.
/deps/

# Where third-party dependencies like ExDoc output generated docs.
/doc/

# Ignore .fetch files in case you like to edit your project deps locally.
/.fetch

# If the VM crashes, it generates a dump, let's ignore it too.
erl_crash.dump

# Also ignore archive artifacts (built via "mix archive.build").
*.ez

# Ignore package tarball (built via "mix hex.build").
{{SERVICE_NAME_UNDERSCORE}}-*.tar

# Temporary files, for example, from tests.
/tmp/

# Environment files
.env
.env.local
.env.*.local

# Editor files
.vscode/
.idea/
*.swp
*.swo
*~

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Phoenix static assets
/priv/static/assets/

# Phoenix Live Dashboard history
/priv/plts/

# Ignore built assets
/assets/node_modules/

# Ignore Dialyzer cache
/priv/plts/*.plt
/priv/plts/*.plt.hash

# Ignore deployment files
/rel/

# Ignore development database
*.db
*.sqlite3

# Ignore logs
/log/
*.log

# If using Docker
docker-compose.override.yml

# If using npm/yarn in assets
/assets/node_modules/
/assets/.npm
/assets/.yarn-integrity

# Release artifacts
*.tar.gz

# Ignore Elixir Language Server
/.elixir_ls/