FROM rust:1.74

WORKDIR /usr/src/{{service_name}}
COPY . .

RUN cargo build --release

CMD ["./target/release/{{service_name}}"]
