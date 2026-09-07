# How to Run `CLIENT-ORCHESTRATOR-SVC`

---

## 1. Initialize Database
```powershell
cd "C:\PRIVATE PROJECTS\CLIENT-ORCHESTRATOR-SVC"
python -m src.cli init-db
```

## 2. Check All 5 Platform Services
```powershell
python -m src.cli check-services
```

## 3. Run Pipeline Once
```powershell
python -m src.cli run-pipeline --min-score 75.0
```

## 4. Start Server or Background Daemon
```powershell
# REST API Server
python -m src.cli run-server --port 8004

# Background Continuous Daemon
python -m src.cli daemon --interval 15 --min-score 75
```

## 5. Run Tests
```powershell
pytest tests -v --cov=src
```
