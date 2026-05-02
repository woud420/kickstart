FROM gcc:14 AS builder

WORKDIR /usr/src/{{ service_name }}
COPY . .

RUN apt-get update \
    && apt-get install -y --no-install-recommends cmake make \
    && rm -rf /var/lib/apt/lists/*

RUN cmake -S . -B build && cmake --build build --config Release

FROM debian:bookworm-slim

WORKDIR /usr/local/bin/{{ service_name }}
COPY --from=builder /usr/src/{{ service_name }}/build/{{ service_name }} .

CMD ["./{{ service_name }}"]
