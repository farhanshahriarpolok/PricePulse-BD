# CLAUDE.md — Agent Quick Reference & Context Entry Point

This file provides a fast, lightweight context entry point for Claude and compatible agentic workflows in the **PricePulse BD** repository.

---

## 1. Project Governance & Master Documentation

Before initiating any development or refactoring, refer to the authoritative project governance files:

- **[AGENTS.md](file:///d:/PricePulse%20BD/AGENTS.md)**: Master operational contract, architectural invariants, code standards, and forbidden behaviors.
- **[BRAIN.md](file:///d:/PricePulse%20BD/BRAIN.md)**: Compressed durable project intelligence, architecture state, taxonomy, algorithms, and active risk register.
- **[TASKS.md](file:///d:/PricePulse%20BD/TASKS.md)**: Active task execution queue (`## NOW`, `## NEXT`, `## BLOCKED`, `## DONE RECENTLY`).
- **[docs/ARCHITECTURE.md](file:///d:/PricePulse%20BD/docs/ARCHITECTURE.md)**: System topology, ingestion pipeline, and database schema.
- **[docs/API_SPEC.md](file:///d:/PricePulse%20BD/docs/API_SPEC.md)**: Complete OpenAPI/REST v1 endpoint specifications.
- **[docs/ALGORITHMS.md](file:///d:/PricePulse%20BD/docs/ALGORITHMS.md)**: Mathematical formulas (SMA, Z-score, Haversine freight arbitrage, CPI shift).
- **[docs/VIVA_DEFENSE_GUIDE.md](file:///d:/PricePulse%20BD/docs/VIVA_DEFENSE_GUIDE.md)**: Academic examiner Q&A defense playbook and demonstration walkthrough.

---

## 2. Common Windows PowerShell Commands

Always execute commands from the repository root (`D:\PricePulse BD`):

### Test Execution
```powershell
# Run entire test suite quietly
venv\Scripts\python.exe -m pytest tests/ -q

# Run specific test file
venv\Scripts\python.exe -m pytest tests/test_saved_baskets.py -v

# Run with verbose stdout output
venv\Scripts\python.exe -m pytest tests/ -v -s
```

### Backend Runtime
```powershell
# Run master orchestration server
venv\Scripts\python.exe run_system.py

# Or launch FastAPI directly with live reload
venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend Runtime & Compilation
```powershell
# Start Vite development server
cd frontend; npm run dev

# Compile production bundle
cd frontend; cmd /c "npm run build"
```

### Database & Ingestion Tasks
```powershell
# Re-initialize SQLite schema with seed data
venv\Scripts\python.exe scripts/init_db.py

# Sync daily prices from live harvesters and fallback fixtures
venv\Scripts\python.exe scripts/sync_daily_prices.py

# Regenerate calibrated 30-day market history
venv\Scripts\python.exe scripts/generate_demo_history.py
```

### Git Status & Verification
```powershell
git status -s
git log -n 5 --oneline
```
