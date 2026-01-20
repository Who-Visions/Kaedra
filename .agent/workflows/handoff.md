---
description: Read agent handoff notes before starting work
---

# Agent Handoff Protocol

Before starting any work on Kaedra, read your handoff file:

## If you are Blade (Flutter/UI)

1. Read `.agent/handoff/BLADE_HANDOFF.md`
2. Act on NEXT ACTIONS
3. Add `REQUEST:` lines for backend needs
4. Update when complete

## If you are Nyx (Backend/Python)

1. Read `.agent/handoff/NYX_HANDOFF.md`
2. Check BLADE_HANDOFF.md for `REQUEST:` items
3. Implement requested endpoints
4. Update both files when complete

## Notion Sync (Internal Flow)

After updating handoffs, sync to Notion for cross-agent visibility:

```bash
// turbo
python scripts/sync_handoffs_to_notion.py
```

Notion DB: <https://www.notion.so/2e7ca671311e80e6ae14eded33870f70>

## Handoff File Locations

- Blade: `c:\Users\super\Watchtower\Kaedra_Local\.agent\handoff\BLADE_HANDOFF.md`
- Nyx: `c:\Users\super\Watchtower\Kaedra_Local\.agent\handoff\NYX_HANDOFF.md`
- GCP Inventory: `c:\Users\super\Watchtower\Kaedra_Local\.agent\handoff\GCP_INVENTORY.md`
