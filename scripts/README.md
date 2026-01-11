# KAEDRA ORCHESTRATION SCRIPTS

**Orchestrator**: Kaedra - Shadow Tactician / Strategic Intelligence Officer
**Purpose**: Agent coordination, task routing, and mission planning automation.

---

## SCRIPT MODULES

### 1. `agent_router.py`
**Purpose**: Route tasks to the appropriate agent based on capabilities and current load.

**Functions**:
- `route_task(task_description)` → Returns optimal agent
- `check_agent_availability(agent_name)` → Boolean
- `get_agent_capabilities(agent_name)` → List of skills

**Routing Logic**:
```python
Task Type          → Agent
─────────────────────────────────────
CLI Operations     → Claude
Web Research       → Gemini
Creative Work      → Vision
Complex Coding     → Anti-Gravity
Strategy/Planning  → Kaedra (self)
Code Generation    → Codex
IDX Development    → Anti-Gravity
```

### 2. `mission_planner.py`
**Purpose**: Break down complex missions into agent-specific subtasks.

**Functions**:
- `decompose_mission(mission)` → List of subtasks
- `assign_agents(subtasks)` → Task-to-agent mapping
- `generate_execution_plan(assignments)` → Sequential/parallel plan

**Planning Modes**:
- **Sequential**: Tasks must complete in order
- **Parallel**: Tasks can run simultaneously
- **Hybrid**: Mix of both

### 3. `status_monitor.py`
**Purpose**: Track agent health, performance, and system status.

**Functions**:
- `ping_all_agents()` → Status dict
- `check_system_health()` → Health report
- `log_performance_metrics(agent_name, metrics)` → None

**Monitoring**:
- Agent response times
- Success/failure rates
- Resource usage (API calls, tokens)
- Error tracking

---

## ORCHESTRATION WORKFLOW

### Standard Task Flow:
1. **Receive Task** → Kaedra receives operator request
2. **Analyze Complexity** → Single agent or multi-agent?
3. **Route/Plan** → Use `agent_router.py` or `mission_planner.py`
4. **Execute** → Coordinate agents via Vertex AI + individual APIs
5. **Monitor** → Track progress with `status_monitor.py`
6. **Synthesize** → Combine results and return to operator
7. **Memory** → Log mission, decisions, and learnings

### Multi-Agent Coordination:
```
Kaedra (Orchestrator)
  ↓
  ├─→ Claude (CLI ops)
  ├─→ Gemini (Research)
  ├─→ Vision (Creative)
  └─→ Codex (Code generation)
  ↓
Results aggregated and returned to operator
```

---

## INTEGRATION POINTS

### Vertex AI Connection
- **Kaedra** connects to Vertex AI Reasoning Engine for strategic intelligence
- **Resource**: `projects/627440283840/locations/us-central1/reasoningEngines/5765957723313143808`
- **Models**: Gemini 2.5 Flash, Pro, and Ultra

### Agent APIs
- **Claude**: Anthropic API (Claude Sonnet 4.5)
- **Gemini**: Google AI Studio API
- **Vision**: Google AI Studio API
- **Codex**: OpenAI API
- **Anti-Gravity**: Google AI Studio API

### Communication Protocol
- **Command Format**: JSON messages with task description, priority, and context
- **Response Format**: JSON with status, result, and metadata
- **Error Handling**: Retry logic with exponential backoff

---

## DEVELOPMENT GUIDELINES

### Adding New Scripts
1. Follow naming convention: `{function}_{action}.py`
2. Include docstrings with usage examples
3. Update this README with function signatures
4. Register in `orchestrator.py` if needed

### Testing Scripts
```bash
cd /mnt/c/Users/super/Watchtower/Kaedra_Local/scripts
python -m pytest test_agent_router.py
```

---

## SECURITY & LIMITS

**API Rate Limits**:
- Vertex AI: Based on GCP quotas
- Claude: 50 RPM (requests per minute)
- Gemini: 10-15 RPM (depends on model)
- OpenAI: 60 RPM

**Error Handling**:
- Graceful degradation when agents are unavailable
- Fallback routing to alternative agents
- Operator notification for critical failures

---

**Version**: 1.0
**Maintained By**: KAEDRA (Shadow Tactician)
**Integration**: Part of Kaedra Orchestrator v4.1
