FROM gcc:latest as builder

WORKDIR /usr/src/{{SERVICE_NAME}}
COPY . .

RUN mkdir build && cd build && \
    cmake .. && \
    make

FROM debian:bullseye-slim

WORKDIR /usr/local/bin/{{SERVICE_NAME}}
COPY --from=builder /usr/src/{{SERVICE_NAME}}/build/{{SERVICE_NAME}} .

CMD ["./{{SERVICE_NAME}}"] 