FROM gcc:latest as builder

WORKDIR /usr/src/{{service_name}}
COPY . .

RUN mkdir build && cd build && \
    cmake .. && \
    make

FROM debian:bullseye-slim

WORKDIR /usr/local/bin/{{service_name}}
COPY --from=builder /usr/src/{{service_name}}/build/{{service_name}} .

CMD ["./{{service_name}}"] 