FROM golang:1.26.2-bookworm AS builder

WORKDIR /app
COPY . .
RUN go mod tidy && go build -o {{ service_name }} ./src

FROM debian:bookworm-slim
WORKDIR /app
COPY --from=builder /app/{{ service_name }} .
CMD ["./{{ service_name }}"]
