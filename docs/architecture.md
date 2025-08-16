# Architecture

The 3Agenteers CLI is composed of modular subsystems bound by a simple message bus. The design follows H-Net principles of dynamic chunking and hierarchical processing to keep agents responsive and scalable.

## Core Subsystems

### Orchestrator
- Acts as the control plane and admin TUI.
- Dispatches tasks, aggregates results, and updates the knowledge base.

### Agents
- Specialized workers that subscribe to topics on the bus.
- Each agent manages its own short-term memory while H-Net chunking promotes long-horizon context.

### Message Bus
- Lightweight publish/subscribe server for decoupled communication.
- Enforces bearer-token authentication and logs unauthorized access.

### Profile Service
- Persists agent credentials and role-based policies.
- Provides profile lookup and updates during task execution.

## Setup Diagram
```mermaid
flowchart LR
    O[Orchestrator] -- publish/subscribe --> B[(Message Bus)]
    A1[Agent A] -- subscribe --> B
    A2[Agent B] -- subscribe --> B
    B --> KB[(Knowledge Base)]
    O --> P[(Profile Store)]
    A1 --> P
    A2 --> P
```

## Task Sequence
```mermaid
sequenceDiagram
    participant U as User
    participant O as Orchestrator
    participant B as Bus
    participant A as Agent
    participant P as Profile

    U->>O: issue command
    O->>P: load profile
    O->>B: publish task
    B->>A: deliver job
    A->>B: send result
    B->>O: forward result
    O->>P: update profile
    O->>U: respond
```

## Extensibility
- New agents register on the bus and integrate with the profile store.
- Additional transports or storage layers can replace defaults as long as interfaces remain stable.
