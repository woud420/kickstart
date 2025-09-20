FROM golang:1.22 as builder

WORKDIR /app
COPY . .
RUN go mod tidy && go build -o {{service_name}} ./src

FROM debian:bullseye-slim
WORKDIR /app
COPY --from=builder /app/{{service_name}} .
CMD ["./{{service_name}}"] 