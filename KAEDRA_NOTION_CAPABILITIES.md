# KAEDRA + Notion: Capability Rundown

KAEDRA v7.15 serves as an **Active Intelligence Layer** that sits on top of your static Notion databases. Instead of just storing data, she actively manages, cleans, and evolves your universe using the same logic you would build into Notion 2.0 formulas—but with Agentic reasoning.

## 🧠 Core Philosophy: "The Agent is the Database Manager"

KAEDRA treats your `lore/worlds/` files as a local mirror of a high-fidelity Notion workspace. She performs operations that would normally require complex Integromat/Make scenarios.

---

## ⚡ Automations (The "High Value" Suite)

KAEDRA natively runs the **VeilVerse Logic Layer**, replacing passive database rows with active state management.

### 1. Canon Management (The "Gatekeeper")
*   **Canon Promotion Pipeline**: Automatically detects when you mark an item as `Canon`.
    *   *Action*: Promotes Production Status from `Concept` -> `In Development`.
    *   *Action*: Stamps `Last Updated` to today.
*   **Retcon Safety Net**: Watches for `Retconned` status.
    *   *Action*: Renames entry to `[RETCONNED] Name`.
    *   *Action*: Sets status to `Inactive`.

### 2. Worldbuilding Consistency (The "Lorekeeper")
*   **Timeline Validator**: Parses years (e.g., `-500`, `2026`, `2150`).
    *   *Action*: Auto-assigns the correct **Universe Era** (`Ancient`, `Classical`, `Modern`, `Future/Entropy`).
*   **Power Scaling**: Reads natural language `Power Level` text.
    *   *Action*: Computes numerical `Importance Score` (30-95) for sorting/filtering.

### 3. Production & Media (The "Producer")
*   **Release Closeout**: Detects `Released` media.
    *   *Action*: Marks status `Completed`, adds `Phase 1` tag.
    *   *Action*: Upgrades related `Semi-Canon` items to full `Canon`.
*   **Social Webhooks**: Detects new releases.
    *   *Action*: Pings social scheduler (Notification Log).
*   **Concept Reviews**: Weekly scheduled checks.
    *   *Action*: Generates a "punch list" of `Canon` concepts that are stuck in `Concept` phase.

### 4. Relationship Intelligence (The "Showrunner")
*   **Major Character Alert**: Monitors `Importance: Major`.
    *   *Action*: Flags new majors without connection maps for review.
*   **Franchise Tracking**: Watches for `Shadow Dweller Saga` franchise tag.
    *   *Action*: Auto-tags appearances (`Shadow Dweller`, `Phase 1`).

---

## 📥 Ingestion & Logging

### The "Notion Log" Pattern
During conversation or writing, KAEDRA can structure output specifically for Notion capture:

```json
{
  "notion_log": {
    "title": "The Glass Cliff",
    "type": "Location",
    "tags": ["Mars", "Hazard"],
    "details": "A jagged obsidian ridge overlooking the Olympus Mons base."
  }
}
```

### Ingestion Pipeline
*   **Source**: `ingestion.json` (acting as your "Inbox" database).
*   **Logic**: Items marked `Approved`.
*   **Action**: KAEDRA moves them to the **World Bible** (`world_bible.json`), creates the entity, and marks the inbox item as `Imported`.

---

## 🛠️ Technical Implementation

| Feature | Kaedra Implementation | Notion Equivalent |
| :--- | :--- | :--- |
| **Logic** | `kaedra/worlds/automations.py` | Formulas / Buttons / Automations |
| **Storage** | `lore/worlds/{id}/world_bible.json` | Master Database |
| **Trigger** | `:automate` command | "Database Updated" Trigger |
| **Output** | `notifications.md` | Slack/Email Notification |

### How to use with Notion
Currently, Kaedra operates on her **local registry**. To sync this with actual Notion:
1.  **Export**: We can build a `json_to_csv` exporter to upload your `world_bible.json` to Notion.
### Future-Proofing: API 2025-09-03 (Multi-Source Databases)

The Kaedra architecture (`lore/worlds/world_id/`) is designed to align with Notion's massive **2025-09-03** API overhaul.
*   **The Container**: The `world_id` folder acts as the **Notion Database** (Container).
*   **Data Sources**: The individual JSON files (`world_bible.json`, `timeline.json`) act as distinct **Data Sources** within that container.

This means when we eventually build the sync bridge, Kaedra will map 1:1 to the new "Multi-Source" paradigm, treating the "World" as the parent and the specific JSON files as the specialized schemas (Character Source, Location Source, etc.)—avoiding the legacy limitation of "One Database = One Schema".
