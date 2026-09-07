# Architecture & Workflow Orchestration Reference
## Client Orchestrator Service (`CLIENT-ORCHESTRATOR-SVC`)

---

## 1. Role & System Responsibility
The **Client Orchestrator Service (`CLIENT-ORCHESTRATOR-SVC`)** (Port 8004) is the central conductor that automates the end-to-end client acquisition lifecycle across all microservices:

1. **Pipeline Runner**: Coordinates the multi-service flow:
   - Queries `CLIENT-FINDER-SVC` (8000) for new discovered gigs
   - Sends leads to `CLIENT-INTELLIGENCE-SVC` (8002) for deep enrichment & scoring
   - Persists leads into `CLIENT-CORE-SVC` (8003)
   - Forwards qualified leads ($\ge 75$) to `CLIENT-MESSAGER-SVC` (8001) for proposal drafting
2. **Platform Topology & Service Discovery**: Real-time heartbeat monitoring of all 5 platform services.
3. **Event Bus**: Event publisher & subscriber for domain transitions.
4. **Execution Audit Log**: Persistent database records of every pipeline run and step-by-step trace.

---

## 2. End-to-End Orchestrated Pipeline Flow

```mermaid
sequenceDiagram
    autonumber
    actor Cron as Orchestrator Runner
    participant Finder as Client Finder (8000)
    participant Intel as Client Intelligence (8002)
    participant Core as Client Core CRM (8003)
    participant Messager as Client Messager (8001)
    actor Human as Operator

    Cron->>Finder: GET /api/projects (Fetch raw leads)
    Finder-->>Cron: Returns raw leads list

    loop For each lead
        Cron->>Intel: POST /api/v1/analyze/project (Deep cognitive analysis)
        Intel-->>Cron: Returns requirements, client info, score & pitch angle

        Cron->>Core: POST /api/v1/leads (Save enriched lead in CRM)
        Core-->>Cron: Lead saved (ID created)

        alt Score >= 75 (Qualified)
            Cron->>Messager: POST /api/v1/ingest/project (Trigger proposal generation)
            Messager-->>Cron: Draft generated in Approval Queue
        end
    end

    Human->>Messager: Review & Approve proposal in Queue
    Messager->>Core: Update lead status to 'contacted'
```
