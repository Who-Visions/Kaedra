# Razer Chroma SDK REST API - Complete Documentation

## Base URIs

- **Local:** `http://localhost:54235/razer/chromasdk`
- **Remote (Secure):** `https://chromasdk.io:54236/razer/chromasdk`

## Session Management

### Initialization

**Endpoint:** `POST /razer/chromasdk`

```json
{
    "title": "App Name",
    "description": "App Description",
    "author": { "name": "Author", "contact": "contact" },
    "device_supported": ["keyboard", "mouse", "headset", "mousepad", "keypad", "chromalink"],
    "category": "application"
}
```

**Response:** Returns `sessionid` and `uri` (e.g., `http://localhost:123456/chromasdk`)

### Uninitialization

**Method:** `DELETE` to session URI

### Heartbeat

**Method:** `PUT` to `{uri}/heartbeat`
**Response:** `{"tick": <number>}`
**Required:** Every 1 second to keep session alive

---

## Device Endpoints

### ChromaLink

- **Endpoint:** `/chromalink`
- **LED Count:** 5 Virtual LEDs
- **Effects:** `CHROMA_NONE`, `CHROMA_STATIC`, `CHROMA_CUSTOM`

#### CHROMA_STATIC

```json
{
    "effect": "CHROMA_STATIC",
    "param": { "color": 255 }
}
```

#### CHROMA_CUSTOM (5 LEDs)

```json
{
    "effect": "CHROMA_CUSTOM",
    "param": [color1, color2, color3, color4, color5]
}
```

### Keyboard

- **Endpoint:** `/keyboard`
- **Grid (Standard):** 6 rows × 22 columns
- **Grid (v2):** 8 rows × 24 columns for `CHROMA_CUSTOM2`

### Mouse

- **Endpoint:** `/mouse`
- **Grid:** 9 rows × 7 columns

### Mousepad

- **Endpoint:** `/mousepad`
- **LED Count (Standard):** 15 LEDs
- **LED Count (v2):** 20 LEDs

### Headset

- **Endpoint:** `/headset`
- **LED Count:** 5 LEDs

### Keypad

- **Endpoint:** `/keypad`
- **Grid:** 4 rows × 5 columns

---

## Color Format

**BGR Format:** `0xBBGGRR`

- RED: `0x0000FF` (255)
- GREEN: `0x00FF00` (65280)
- BLUE: `0xFF0000` (16711680)

---

## Effect Types

| Effect | Description |
|--------|-------------|
| `CHROMA_NONE` | Turn off lighting |
| `CHROMA_STATIC` | Single static color |
| `CHROMA_CUSTOM` | Per-LED colors (1D array for ChromaLink/Headset, 2D for Keyboard/Mouse) |
| `CHROMA_CUSTOM2` | Extended grid for v2 devices |
| `CHROMA_BREATHING` | Breathing effect |
| `CHROMA_WAVE` | Wave effect |
| `CHROMA_SPECTRUMCYCLING` | Rainbow cycle |

---

## Error Codes

| Code | Constant | Meaning |
|------|----------|---------|
| 0 | `RZRESULT_SUCCESS` | Success |
| 5 | `RZRESULT_ACCESS_DENIED` | Access denied |
| 50 | `RZRESULT_NOT_SUPPORTED` | Effect/device not supported |
| 87 | `RZRESULT_INVALID_PARAMETER` | Bad payload |
| 1062 | `RZRESULT_SERVICE_NOT_ACTIVE` | Synapse not running |
| 1167 | `RZRESULT_DEVICE_NOT_CONNECTED` | Hardware not found |

---

## Key Finding: Device-Specific Effects

If standard endpoints fail, use device-specific endpoint:
`/devid=<GUID>`

Where `<GUID>` is the hardware identifier (e.g., Desktop: `{EB96AB11-E327-4BC0-B3E3-862BBB963B5D}`)

---

## Critical Notes

1. **ChromaLink is LOCKED to 5 virtual LEDs** - The Laptop Stand Chroma has more LEDs but ChromaLink maps them internally
2. **Continuous driving** may be required for some hardware
3. **Effect IDs** can be created via POST and reused via PUT to `/effect`
