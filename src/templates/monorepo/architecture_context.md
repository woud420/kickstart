# Architecture Context

```mermaid
flowchart LR
  UI[TypeScript UI or edge app] -->|HTTP| API[Service API]
  API -->|SQL| DB[(PostgreSQL)]
  API -->|cache| Redis[(Redis)]
  API -->|container| K8s[Kubernetes]
  K8s -->|provisions| Cloud[{{ cloud_label }}]

  classDef ui fill:#E0F7FA,stroke:#00ACC1,color:#006064;
  classDef service fill:#E8F5E9,stroke:#43A047,color:#1B5E20;
  classDef db fill:#FFF3E0,stroke:#FB8C00,color:#E65100;
  classDef cache fill:#F1F8E9,stroke:#7CB342,color:#33691E;
  classDef infra fill:#ECEFF1,stroke:#607D8B,color:#263238;

  class UI ui;
  class API service;
  class DB db;
  class Redis cache;
  class K8s,Cloud infra;
```

Update this diagram when new services, queues, object stores, or external APIs are added.
