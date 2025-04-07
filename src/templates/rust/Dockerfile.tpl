FROM rust:1.74

WORKDIR /usr/src/{{SERVICE_NAME}}
COPY . .

RUN cargo build --release

CMD ["./target/release/{{SERVICE_NAME}}"]
