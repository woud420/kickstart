# Build stage
FROM elixir:1.16-alpine AS build

# Install build dependencies
RUN apk add --no-cache build-base npm git python3

# Set working directory
WORKDIR /app

# Install hex and rebar
RUN mix local.hex --force && \
    mix local.rebar --force

# Set environment
ENV MIX_ENV=prod

# Copy mix files
COPY mix.exs mix.lock ./

# Install dependencies
RUN mix deps.get --only prod
RUN mix deps.compile

# Copy application code
COPY . .

# Build assets (if any)
RUN mix assets.deploy 2>/dev/null || echo "No assets to build"

# Compile application
RUN mix compile

# Build release
RUN mix release

# Runtime stage
FROM alpine:3.18 AS runtime

# Install runtime dependencies
RUN apk add --no-cache openssl ncurses-libs

# Create app user
RUN adduser -D -h /app app

# Set working directory
WORKDIR /app

# Copy release from build stage
COPY --from=build --chown=app:app /app/_build/prod/rel/{{SERVICE_NAME_UNDERSCORE}} ./

# Switch to app user
USER app

# Expose port
EXPOSE 4000

# Set environment
ENV PHX_SERVER=true
ENV PORT=4000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:4000/health || exit 1

# Start application
CMD ["./bin/{{SERVICE_NAME_UNDERSCORE}}", "start"]
