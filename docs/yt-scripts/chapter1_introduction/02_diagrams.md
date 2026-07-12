# Chapter 1: Architecture Diagrams

*Use these Mermaid diagrams to visually explain the architecture and observability stack during your video.*

## Diagram 1: The Ultimate Observability Stack

```mermaid
graph TD
    %% Styling
    classDef client fill:#bbf,stroke:#333,stroke-width:2px;
    classDef app fill:#f9f,stroke:#333,stroke-width:2px;
    classDef metrics fill:#ffb,stroke:#333,stroke-width:2px;
    classDef dashboard fill:#bfb,stroke:#333,stroke-width:2px;
    classDef proxy fill:#fbb,stroke:#333,stroke-width:2px;

    %% Nodes
    User([End User / Client]):::client
    Proxy{OpenResty Reverse Proxy}:::proxy
    
    subgraph Kubernetes Cluster
        Backend[Python Backend App]:::app
        OTEL[OpenTelemetry Collector]:::metrics
        
        Prom[(Prometheus<br/>Metrics)]:::metrics
        Loki[(Loki<br/>Logs)]:::metrics
        Tempo[(Tempo<br/>Traces)]:::metrics
        
        Grafana[Grafana Dashboard]:::dashboard
    end

    %% Flow
    User -->|HTTPS Request| Proxy
    Proxy -->|Load Balances| Backend
    
    Backend -.->|Exports Telemetry| OTEL
    
    OTEL -->|Metrics| Prom
    OTEL -->|Logs| Loki
    OTEL -->|Distributed Traces| Tempo
    
    Prom -.-> Grafana
    Loki -.-> Grafana
    Tempo -.-> Grafana
```

## Diagram 2: Backend Auth vs Frontend Auth

```mermaid
sequenceDiagram
    participant Browser
    participant Hacker as Malicious JS (XSS)
    participant Server as Python Backend
    
    Note over Browser,Server: Scenario: Secure Backend Auth
    Browser->>Server: 1. Login Request
    Server-->>Browser: 2. Return Set-Cookie: SessionToken (HTTPOnly, Secure)
    Note over Browser: Browser stores cookie safely.
    
    Hacker->>Browser: 3. Try to read document.cookie
    Browser-->>Hacker: 4. BLOCKED! (HTTPOnly prevents JS access)
    
    Browser->>Server: 5. Next API Call (Cookie sent automatically)
```
