FROM rust:1.85-bookworm AS builder

WORKDIR /usr/src/{{service_name}}
COPY . .

RUN cargo build --release

FROM debian:bookworm-slim AS runtime

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd --system --gid app --home-dir /app --create-home app

WORKDIR /app
COPY --from=builder /usr/src/{{service_name}}/target/release/{{service_name}} /usr/local/bin/{{service_name}}
USER app

CMD ["/usr/local/bin/{{service_name}}"]
