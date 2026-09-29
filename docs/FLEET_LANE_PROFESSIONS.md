---
name: fleet-lane-professions
description: Defines the authoritative architectural professions, responsibilities, runtime hardware assignments, and execution boundaries across the NouGen 12-Lane Swarm and multi-node mesh (Phoebus, WhoArt, Blade).
---

# 🏛️ NouGen Fleet Lane Professions & Cognitive Specialization Matrix

This specification locks the canonical division of labor, architectural professions, operational planes, and hardware routing across the **12-Lane Swarm Matrix** and physical execution nodes (**Phoebus**, **WhoArt**, **Blade**).

---

## 🧭 The 6 Operational Planes

Every lane profession maps directly to one of the six foundational planes defined in `nougen_shards.verbs`:

1. **Memory Plane** (`shard`): Durable memory, vector/FTS embeddings, cross-session ground truth.
2. **Coordination Plane** (`relay`, `msg`, `live`): Handoff batons, IPC transport, mesh discovery.
3. **Observability Plane** (`track`): Metrics, hardware telemetry, token math, cost accounting.
4. **Intent Plane** (`destiny`, `wish`): North-star goal graphs and testable change requests.
5. **Execution Plane** (`build`, `harden`): Candidate generation, compiler enforcement, adversarial verification.
6. **Learning Plane** (`dream`, `evolve`): Offline REM consolidation, progressive skill synthesis.

---

## ⚡ The 12-Lane Swarm Professions

| Lane | Role / Profession | Cognitive Specialization | Target Engine / Model | Hardware & Authority |
| :---: | :--- | :--- | :--- | :--- |
| **01** | **Orchestration Sovereign** | Central query engine, context gating, soul injection | `kaedracode:e2b` | **Phoebus** (Local Mac Mini) — L0/L1 Context Gate |
| **02** | **Grand Architect** | Macro architecture, system-wide refactors, high-level planning | `gemma-4-31b-it:free` | Cloud Tier 1 (Free) — Multi-file architecture design |
| **03** | **Reasoning Strategist** | Deep chain-of-thought, mathematical proof, logic constraints | `nemotron-3-nano-30b` | Cloud Tier 1 (Reasoning) — Deductive truth verification |
| **04** | **Consensus Arbiter** | Multi-model evaluation, voting arbitration, tie-breaking | `nemotron-3-super-120b` | Cloud Tier 1 (Super LLM) — High-elevation governance |
| **05** | **Relevance Reranker** | Cross-shard retrieval ranking, semantic similarity filtering | `nemotron-rerank-vl-1b` | Cloud Tier 1 (Reranker) — Top-K precision filter |
| **06** | **Adversarial Hardener** | Security pentesting, fuzzing, secret scrubbing, edge cases | `laguna-xs-2.1` / `gemma4` | Execution Plane — Regression testing & failure injection |
| **07** | **Edge Reflex Runner** | Low-latency state dispatch, instant triage, regex parsing | `liquid-lfm-2.5` | Fast Edge — Immediate dispatch & validation |
| **08** | **Polyglot Code Synthesizer** | High-throughput code generation, AST transforms, diffs | `cohere/north-mini-code` | Execution Plane — Source code patch drafting |
| **09** | **Financial & Quota Auditor** | Token math, cloud billing, API cost bounding, token fuses | `ling-3.0-flash-fin` | Observability Plane — Ledger accounting & burn limits |
| **10** | **Integrity & Health Sentinel** | Heartbeat monitoring, thermal indices, socket latching | `ling-3.0-flash-sante` | Observability Plane — Hardware telemetry & daemon health |
| **11** | **Deep Synthesis Explorer** | Lore expansion, Veilverse worldbuilding, dialogue | `nemotron-3.5-lightning` | Intent Plane — Narrative canon & character voices |
| **12** | **Ground Truth Sharder** | Invariant extraction, REM sleep consolidation, SFT export | `gemma4:e2b` | **Phoebus / Blade** — Substrate cluster persistence |

---

## 🖥️ Physical Node Topology & Hardware Alignment

### 1. 🪐 Phoebus (Mac Mini M-Series)
- **Role**: Fleet Master, Substrate Cluster Custodian, and Context Gatekeeper.
- **Hardware Profile**: Unified Memory, 1,139 tokens/s prefill caching, 124.97 ms embedding latency.
- **Assigned Professions**:
  - `Orchestration Sovereign` (Lane 01)
  - `Ground Truth Sharder` (Lane 12)
  - Memory Substrate cluster (`nougen_shards_1.db` through `9.db`)
  - 24/7 Headless Daemon (`com.nougen.fleetcron20m`)

### 2. ⚡ WhoArt (Windows 11 / RTX 4050 Laptop GPU 6GB)
- **Role**: High-Speed Local CUDA Inference Engine & Multimedia Specialist.
- **Hardware Profile**: 80.53 tokens/s (`gemma2:2b`), 77.24 tokens/s (`Yukiai:e2b`), CUDA 13.0, Driver 581.57.
- **Assigned Professions**:
  - `Yukiai / Media Intelligence Runner`
  - High-speed visual & perceptual processing
  - Ephemeral rapid local inference worker (10x over CPU)

### 3. 🛡️ Blade (Razer Blade 15 / RTX 2080 Max-Q 8GB)
- **Role**: Sustained CUDA Worker & Heavy Offline Compute.
- **Hardware Profile**: 65.08 tokens/s (`gemma4:e2b`), 8 GB dedicated VRAM, 32 GB RAM.
- **Assigned Professions**:
  - Heavy batch embeddings & Whisper transcription
  - Local video rendering & frame interpolation pipelines
  - Secondary offline training / LoRA parameter burn-in

---

## 📜 The Non-Collapse Invariants

1. **A message is not memory merely because it was said.**
2. **A relay is not truth merely because it was accepted.**
3. **A relay leg cannot transition to closed or acked without verifiable Proof-of-Execution (PoE).**
4. **Simulating execution by modifying JSON metadata without physical artifacts is an anti-simulation breach.**
5. **No subsystem or lane may silently assume the authority of another plane.**
