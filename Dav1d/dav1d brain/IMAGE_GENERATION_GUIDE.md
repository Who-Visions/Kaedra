# DAV1D Image Generation - Quick Reference

## 🎨 How to Generate Images

### Method 1: Natural Language (Auto-Selects Model)
```bash
generate an image of a sunset over the ocean
create a cyberpunk cityscape
make me an image of a futuristic robot
```
DAV1D will automatically choose the best model based on your prompt.

### Method 2: Force Specific Model
```bash
/vision          # Force Imagen 4 (fast, cost-effective)
/vision_pro      # Force Gemini 3 Pro Image (premium quality)
```

## 📁 Where Images are Saved

**Directory**: `c:/Users/super/Watchtower/Dav1d/dav1d brain/images/`

This directory is created automatically when you generate your first image.

## 📝 Filename Format

Images are saved with descriptive filenames:

```
{model_name}_{timestamp}_{number}.png
```

**Examples**:
- `imagen_20251128_150530_1.png` - Imagen 4 generated at 3:05:30 PM
- `gemini_20251128_203442_1.png` - Gemini 3 Pro Image generated at 8:34:42 PM

## 🔍 Finding Your Images

### Option 1: Click the Path in Console
When DAV1D generates an image, it prints the full path:
```
[IMAGE GENERATED] Saved 1 image(s):
  📁 c:\Users\super\Watchtower\Dav1d\dav1d brain\images\imagen_20251128_150530_1.png
```

### Option 2: Open in File Explorer
Navigate to:
```
c:\Users\super\Watchtower\Dav1d\dav1d brain\images
```

### Option 3: Command (Windows)
```cmd
explorer "c:\Users\super\Watchtower\Dav1d\dav1d brain\images"
```

## ⚙️ Model Comparison

| Model | ID | Speed | Quality | Cost | Best For |
|-------|-----|-------|---------|------|----------|
| **Imagen 4** | `imagen-4.0-generate-001` | ⚡ Fast | ⭐⭐⭐⭐ | $0.04 | Quick generation, batch processing |
| **Gemini 3 Pro** | `gemini-3-pro-image-preview` | 🐌 Slower | ⭐⭐⭐⭐⭐ | $0.13 | Complex prompts, artistic detail, branding |

## 💡 Tips

1. **Check the images folder regularly** - it can fill up quickly!
2. **Images are named by timestamp** - no overwrites, every image is preserved
3. **Model prefix helps sorting** - easily separate Imagen vs Gemini generations
4. **Full paths are clickable** in most terminals - Ctrl+Click to open

## 🗑️ Managing Images

The `.gitignore` is configured to exclude `images/` from version control, so:
- ✅ Generated images stay local (not pushed to Git)
- ✅ Safe to delete the folder anytime to free space
- ✅ Folder auto-recreates on next generation

## Example Workflow

```bash
# 1. Start DAV1D
python dav1d.py

# 2. Generate an image
[YOU|AUTO] >> create a futuristic city with neon lights

# 3. DAV1D responds
[AUTO] 🎨 vision (Image generation task)
[DAV1D] Consulting the data streams (imagen-4.0-generate-001)...
[IMAGE GENERATED] Saved 1 image(s):
  📁 c:\Users\super\Watchtower\Dav1d\dav1d brain\images\imagen_20251128_150530_1.png

# 4. Open the image
# Click the path or navigate to images/ folder
```

## 🎯 Quick Commands

```bash
# Open images folder
cd "c:\Users\super\Watchtower\Dav1d\dav1d brain\images"
dir                    # List all images
explorer .             # Open in File Explorer

# Count images
dir /b | find /c ".png"

# Delete all images (careful!)
del *.png
```
