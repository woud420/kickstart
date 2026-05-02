# Architecture Context

```mermaid
flowchart LR
  UI[TypeScript UI or edge app] -->|HTTP| API[Service API]
  API -->|SQL| DB[(PostgreSQL)]
  API -->|cache| Redis[(Redis)]
{% if uses_kubernetes %}
  API -->|container| K8s[Kubernetes]
  K8s -->|provisions| Cloud[{{ cloud_label }}]
{% endif %}
{% if uses_cloudflare_workers %}
  UI -->|edge route| Worker[Cloudflare Worker]
  Worker -->|calls| API
{% endif %}
{% if not uses_kubernetes %}
  API -->|cloud resources| Cloud[{{ cloud_label }}]
{% endif %}

  classDef ui fill:#E0F7FA,stroke:#00ACC1,color:#006064;
  classDef service fill:#E8F5E9,stroke:#43A047,color:#1B5E20;
  classDef db fill:#FFF3E0,stroke:#FB8C00,color:#E65100;
  classDef cache fill:#F1F8E9,stroke:#7CB342,color:#33691E;
  classDef infra fill:#ECEFF1,stroke:#607D8B,color:#263238;

  class UI ui;
  class API{% if uses_cloudflare_workers %},Worker{% endif %} service;
  class DB db;
  class Redis cache;
  class {% if uses_kubernetes %}K8s,{% endif %}Cloud infra;
```

Update this diagram when new services, queues, object stores, or external APIs are added.
