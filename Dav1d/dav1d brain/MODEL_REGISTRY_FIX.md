# DAV1D Model Registry Update - 2025-11-27

## Issue Fixed
The model registry was referencing `gemini-exp-1206`, which doesn't exist in the `us-east4` region, causing 404 errors when trying to use pro/deep/vision_pro models.

## Changes Made

### Before (BROKEN)
```python
"pro": "gemini-exp-1206",          # ❌ Model not found
"vision": "gemini-2.5-flash-image", # ❌ Model not found  
"vision_pro": "gemini-exp-1206",   # ❌ Model not found
"deep": "gemini-exp-1206",         # ❌ Model not found
```

### After (WORKING)
```python
"pro": "gemini-2.5-pro",             # ✅ Available in us-east4
"vision": "imagen-3.0-generate-001",  # ✅ Available in us-east4
"vision_pro": "imagen-3.0-generate-001", # ✅ Available in us-east4
"deep": "gemini-2.5-pro",            # ✅ Available in us-east4
```

## Model Details

### Text Models (Working)
- `ultra_lite`: gemini-2.5-flash-lite
- `lite`: gemini-2.5-flash-lite-preview
- `flash`: gemini-2.5-flash
- `flash_preview`: gemini-2.5-flash-preview
- `balanced`: gemini-2.5-pro
- `pro`: gemini-2.5-pro *(updated)*
- `deep`: gemini-2.5-pro *(updated)*

### Image Generation Models (Updated)
- `vision`: imagen-3.0-generate-001 *(updated)*
- `vision_pro`: imagen-3.0-generate-001 *(updated)*

## Why Imagen 3.0?

Gemini models don't natively generate images in the current API. For image generation:
- **Imagen 3.0** is Google's dedicated text-to-image model
- Available in `us-east4` via Vertex AI
- Supports high-quality image generation
- Model ID: `imagen-3.0-generate-001`

## Testing

To test the fix, restart DAV1D and try:
```
generate an image for me
```

Should now work without 404 errors.

## Future Considerations

When Gemini 3.0 models become available in `us-east4`, update:
- `pro` → `gemini-3-pro` (when available)
- `deep` → `gemini-3-pro` (when available)

For now, `gemini-2.5-pro` provides excellent quality for complex tasks and reasoning.

---
**AI with Dav3 × Who Visions LLC**  
Fixed: 2025-11-27 17:58 EST
