# DAV1D Tooling Registry
**Philosophy:** CLI-First, Progressive Disclosure.

## Core Tools

### 1. Meta Agent (The Builder)
*   **Command:** `python tools/meta_agent.py "Description of tool to build"`
*   **Description:** Uses the "Recursive Mirror" philosophy to build *new* tools for you. Generates self-contained Python CLI scripts based on your requirements.
*   **Use Case:** When you need a tool that doesn't exist yet.
*   **From inside Dav1d:** Just say what you need (e.g., "build a tool to check stock prices") and he will run `[EXEC: python tools/meta_agent.py "<description>"]` automatically, then use the new tool.
*   **Workflow reminder:** Generate ➜ run `--help` ➜ execute ➜ summarize what was built.

### 2. Gmail Integration
*   **Command:** `python tools/gmail_api.py` (Importable as module)
*   **Description:** Read-only access to Gmail inbox.
*   **Status:** Requires authentication via `fix_gmail_auth.bat`.

### 3. Notion Integration
*   **Command:** `python notion_integration.py` (Server)
*   **Description:** Webhook receiver for Notion events. Analyzes pages with Gemini and updates them.

### 4. PDF Processor
*   **Command:** `python tools/pdf_processor.py "path/to/pdf_or_dir"`
*   **Description:** Extracts text from PDFs and creates AI-generated digests (Summary + Key Takeaways).
*   **Output:** `resources/digests/`

### 5. Evolution Tool (Self-Improvement)
*   **Command:** `python tools/evolve_persona.py`
*   **Description:** Reads recent session logs, analyzes user feedback/corrections, and permanently rewrites `resources/profiles/dav1d.txt` to improve future behavior.
*   **Recursive:** This allows Dav1d to reprogram his own personality.

## Generated Tools
*(New tools built by Meta Agent will appear here)*

### lyrics_fetcher.py
*   **Command:** `python tools/lyrics_fetcher.py`
*   **Description:** A CLI tool to fetch song lyrics from URLs and save them to a JSON file.
