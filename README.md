# Client Orchestrator Service (`CLIENT-ORCHESTRATOR-SVC`)

Multi-service pipeline coordination, automated end-to-end client acquisition workflows, platform service topology discovery, and domain event bus (Port 8004).

---

## 🚀 Quickstart

### 1. Initialize Database
```powershell
cd "C:\PRIVATE PROJECTS\CLIENT-ORCHESTRATOR-SVC"
python -m src.cli init-db
```

### 2. Start REST API Server
```powershell
python -m src.cli run-server --port 8004
```

- Swagger UI: [http://localhost:8004/docs](http://localhost:8004/docs)
- Health Check: [http://localhost:8004/health](http://localhost:8004/health)

### 3. Check All 5 Platform Services Status
```powershell
python -m src.cli check-services
```

### 4. Trigger End-to-End Pipeline
```powershell
python -m src.cli run-pipeline --min-score 75.0 --limit 20
```

### 5. Run Continuous Daemon
```powershell
python -m src.cli daemon --interval 15 --min-score 75
```

### 6. Run Tests
```powershell
pytest tests -v --cov=src
```
