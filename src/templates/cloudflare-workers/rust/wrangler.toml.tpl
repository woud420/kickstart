name = "{{ service_name }}"
main = "build/worker/shim.mjs"
compatibility_date = "2026-05-02"

[build]
command = "make worker-build-release"

[vars]
SERVICE_NAME = "{{ service_name }}"
