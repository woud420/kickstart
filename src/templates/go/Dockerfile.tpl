FROM golang:{{ go_docker_tag }} AS builder

WORKDIR /app
COPY . .
RUN go mod tidy && go build -o {{ service_name }} ./src

FROM debian:bookworm-slim
WORKDIR /app
COPY --from=builder /app/{{ service_name }} .
EXPOSE 8080
CMD ["./{{ service_name }}"]
