# Gemini Model Migration Guide (Reference)

## Model Comparison
| Feature | 2.5 Flash | 2.5 Pro | 3.0 Pro (Preview) |
| :--- | :--- | :--- | :--- |
| **Status** | GA | GA | Preview |
| **Context** | 1M Tokens | 1M Tokens | 1M Tokens |
| **Output** | 65k Tokens | 65k Tokens | 65k Tokens |
| **Best For** | Speed, Cost, Gen-Purpose | Complex Reasoning, Coding | Agentic Workflows, Advanced Reasoning |

## Key Migration Notes
1.  **SDK**: Must use `Google Gen AI SDK` (already migrated).
2.  **Thinking**: Gemini 3.0 Pro uses `thinking_level` instead of `thinking_budget`.
3.  **Temperature**: Keep at **1.0** (default) for Gemini 3.0 Pro. Lowering it may cause looping.
4.  **Media**: Variable sequence length for tokenization.
5.  **Search**: Use "Grounding with Google Search" (Dynamic Retrieval is deprecated).

## Breaking Changes to Watch
- **Top-K**: Not supported on newer models.
- **OCR**: Not used by default on PDFs for 3.0 Pro.
- **Image Segmentation**: Not supported on 3.0 Pro.

## Recommended Strategy
1.  **Evaluate**: Run offline tests with current prompts.
2.  **Upgrade**: Switch model IDs (Done).
3.  **Refine**: Adjust prompts if performance drops (Hill Climbing).
4.  **Load Test**: Ensure throughput meets needs (Quota management).
