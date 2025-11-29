# 🎬 Veo Video Generation - All Models Available

## ✅ 5 Veo Models Ready

| Model | Code | Speed | Quality | Audio | Best For |
|-------|------|-------|---------|-------|----------|
| **Veo 3.1** | `veo-3.1` | Slow (3-5 min) | Highest | ✅ Yes | Final production |
| **Veo 3.1 Fast** | `veo-3.1-fast` | Fast (1-2 min) | High | ✅ Yes | **Default - best balance** |
| **Veo 3** | `veo-3` | Slow (3-5 min) | High | ✅ Yes | Stable version |
| **Veo 3 Fast** | `veo-3-fast` | Fast (1-2 min) | High | ✅ Yes | Fast + stable |
| **Veo 2** | `veo-2` | Medium (2-3 min) | Good | ❌ No | Legacy/silent videos |

---

## 🚀 Quick Usage

### Generate One Video

```python
from tools.veo_video import generate_video

# Default (Veo 3.1 Fast)
generate_video("A cyberpunk cityscape at night")

# Specify model
generate_video(
    "Ocean waves at sunset",
    model="veo-3.1",      # Highest quality
    resolution="4K",
    duration=8
)

# Fast generation
generate_video(
    "Futuristic AI lab",
    model="veo-3.1-fast"  # Default
)
```

### Use in Dav1d Chat

```
"generate a video of a cyberpunk city using veo-3.1-fast"
"create a 4K video of ocean waves with veo-3.1"
"make a video of a futuristic lab"  # Uses default (3.1-fast)
```

### Batch Generate

```python
from tools.veo_video import generate_video_batch

prompts = [
    "A serene mountain landscape",
    "A bustling city street",
    "A peaceful forest path"
]

generate_video_batch(
    prompts,
    model="veo-3.1-fast",  # Fast batch generation
    resolution="1080p"
)
```

---

## 💰 Cost & Speed Comparison

| Model | 1080p Cost | 4K Cost | Generation Time |
|-------|------------|---------|-----------------|
| Veo 3.1 | $1.88 | $3.13 | 3-5 minutes |
| Veo 3.1 Fast | $1.88 | $3.13 | **1-2 minutes** ⚡ |
| Veo 3 | $1.88 | $3.13 | 3-5 minutes |
| Veo 3 Fast | $1.88 | $3.13 | **1-2 minutes** ⚡ |
| Veo 2 | $1.50 | N/A | 2-3 minutes |

**Recommendation:** Use `veo-3.1-fast` for most tasks - same cost, 2-3x faster!

---

## 🔥 Credit Burning Strategy

**To burn $50 in credits using Veo 3.1 Fast:**

```python
# Option 1: 16 videos at 1080p + 10 at 4K = $50.06
generate_video_batch(
    prompts_1080p,  # 16 prompts
    model="veo-3.1-fast",
    resolution="1080p"
)  # $30.08

generate_video_batch(
    prompts_4k,  # 10 prompts  
    model="veo-3.1-fast",
    resolution="4K"
)  # $31.30

# Total time: ~26 minutes (vs ~80 minutes with standard 3.1)
```

**Fastest burn:** Use Fast models, generate during off-peak hours

---

## 🎯 When to Use Each Model

### Veo 3.1 (Slow, High Quality)
- Final production videos
- Client deliverables
- Portfolio pieces
- When you have time

### Veo 3.1 Fast (DEFAULT) ⭐
- **Most use cases**
- Testing and iteration
- Content creation
- Social media
- Same quality as 3.1, just faster

### Veo 3 (Stable)
- When you want stable/GA version
- Enterprise deployments
- Predictable behavior

### Veo 3 Fast
- Fast + stable combo
- Good for production at scale

### Veo 2
- **Only if you need silent videos**
- Legacy compatibility
- Slightly cheaper ($1.50 vs $1.88)

---

## 📋 Complete Example

```python
from tools.veo_video import generate_video

# High quality, worth the wait
result = generate_video(
    prompt="A cinematic shot of a futuristic AI data center with glowing holographic displays and robots working",
    model="veo-3.1",
    resolution="4K",
    duration=8
)

if result['success']:
    print(f"Video: {result['video_path']}")
    print(f"Cloud: {result['gcs_url']}")
    print(f"Cost: ${result['cost']}")
```

---

**Default is `veo-3.1-fast` - best balance of speed and quality!**
