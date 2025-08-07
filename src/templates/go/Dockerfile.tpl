FROM golang:1.22 as builder

WORKDIR /app
COPY . .
RUN go mod tidy && go build -o {{SERVICE_NAME}} ./src

FROM debian:bullseye-slim
WORKDIR /app
COPY --from=builder /app/{{SERVICE_NAME}} .
CMD ["./{{SERVICE_NAME}}"] 
