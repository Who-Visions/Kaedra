# Notion Integration Map: "Kaedra-notes"

This document maps the accessible Notion databases to Kaedra's local file registry (`lore/worlds/`).
**Integration Status**: Enabled via `Kaedra-notes` bot.

## 🗺️ Database Mapping

| Notion Database Name | Kaedra Local File | Purpose |
| :--- | :--- | :--- |
| **VeilVerse Codex – World Bible** | `world_bible.json` | The core registry of Characters, Lore, and Locations. |
| **Timeline Nodes** | `timeline.json` | Chronological events and era definitions. |
| **VeilVerse Ingestion Queue** | `ingestion.json` | Raw ideas waiting for approval/import. |
| **Lore Laws** | `canon.json` | Hard rules and axiomatic truths of the universe. |
| **Scenes** | `scenes/` (Directory) | Narrative prose and scene beats. |
| **Cosmic Wounds & Veil Decay** | `world_bible.json` (Section: Wounds) | Tracking entropy and veil stability. |
| **Shadow Dweller Vol. 1** | *See Note 1* | Specific narrative arc / draft content. |
| **VeilVerse Build Ops** | `notifications.md` | System alerts and task tracking. |

## 🛠️ Specialized Mappings

### 📥 Ingestion Pipeline
*   **Source**: [VeilVerse Ingestion Queue]
*   **Logic**: Items marked `Status: Approved`.
*   **Target**: [VeilVerse Codex – World Bible] (and local `world_bible.json`).

### 🌑 Shadow Dweller Saga
*   **Source**: [Shadow Dweller Vol. 1 — 2026 Draft]
*   **Logic**: Tagged content.
*   **Target**: mapped to `Series/Franchise: Shadow Dweller Saga` in local metadata.

### ⚖️ Canon Verification
*   **Source**: [Lore Laws]
*   **Logic**: Source of Truth for the `check_retcons` automation.

## 🚀 Next Steps for Integration
To activate the live bridge:
1.  **Retrieve IDs**: We need the UUIDs for these specific pages/databases.
2.  **Config**: Create `kaedra/config/notion.toml` with the mappings.
3.  **Sync Script**: Python script to pull from Notion -> Update JSON -> Run Automations -> Push back to Notion.
