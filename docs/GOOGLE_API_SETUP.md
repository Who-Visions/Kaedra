# Google Cloud API Setup for KAEDRA

**Status:** ✅ Integrated  
**Last Updated:** 2025-11-27T02:59:00-05:00

---

## APIs Integrated

### 1. **Custom Search API** (Free: 100 searches/day)
- **Purpose:** Web search for NYX intelligence gathering
- **Trigger:** `/nyx search [query]`
- **Cost:** FREE up to 100/day

### 2. **Google News** (100% Free via RSS)
- **Purpose:** Latest news on any topic
- **Trigger:** `/nyx news` or `/nyx news [topic]`
- **Cost:** FREE (no limits, uses RSS)

### 3. **YouTube Data API** (Free: 10,000 quota units/day)
- **Purpose:** Video search, trending content
- **Trigger:** `/nyx youtube [query]`
- **Cost:** FREE up to 10K quota/day

### 4. **Google Trends** (100% Free via RSS)
- **Purpose:** Trending search topics
- **Trigger:** `/nyx trends`
- **Cost:** FREE (no limits, uses RSS)

---

## Setup Instructions

### Step 1: Get Your API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to: **APIs & Services** → **Credentials**
3. Click: **Create Credentials** → **API Key**
4. Copy the API key

### Step 2: Enable Required APIs

Enable these APIs in your project:
- ✅ Custom Search API
- ✅ YouTube Data API v3

**Already enabled** (from your screenshot):
- ✅ 115+ APIs including these

### Step 3: Create Custom Search Engine (for Custom Search API)

1. Go to [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Click **Add** → Create new search engine
3. Configure:
   - **Sites to search:** Entire web
   - **Name:** KAEDRA Search
4. Get your **Search Engine ID** (cx parameter)

### Step 4: Set Environment Variables

#### Windows (PowerShell):
```powershell
$env:GOOGLE_API_KEY="YOUR_API_KEY_HERE"
$env:GOOGLE_CSE_ID="YOUR_SEARCH_ENGINE_ID_HERE"
$env:GOOGLE_CLOUD_PROJECT="who-visions-app"
```

#### Windows (Command Prompt):
```cmd
set GOOGLE_API_KEY=YOUR_API_KEY_HERE
set GOOGLE_CSE_ID=YOUR_SEARCH_ENGINE_ID_HERE
set GOOGLE_CLOUD_PROJECT=who-visions-app
```

#### Linux/Mac:
```bash
export GOOGLE_API_KEY="YOUR_API_KEY_HERE"
export GOOGLE_CSE_ID="YOUR_SEARCH_ENGINE_ID_HERE"
export GOOGLE_CLOUD_PROJECT="who-visions-app"
```

#### Permanent (Add to `.env` file):
```
GOOGLE_API_KEY=YOUR_API_KEY_HERE
GOOGLE_CSE_ID=YOUR_SEARCH_ENGINE_ID_HERE
GOOGLE_CLOUD_PROJECT=who-visions-app
```

---

## Usage Examples

### With API Keys Set:
```
[YOU] >> /nyx
[NYX] NYX active. Observing.

[YOU] >> search latest AI breakthroughs
[NYX] [AUTO-EXEC] Scanning search...
✓ Tool executed successfully
{
  "query": "latest AI breakthroughs",
  "results": [
    {"title": "...", "link": "...", "snippet": "..."},
    ...
  ]
}
[NYX] The timeline is converging on quantum AI advancement...

[YOU] >> youtube AI tutorial
[NYX] [AUTO-EXEC] Scanning youtube...
✓ Tool executed successfully
{
  "videos": [
    {"title": "...", "url": "...", "views": "..."},
    ...
  ]
}
[NYX] Strong signal detected in educational content...

[YOU] >> news technology
[NYX] [AUTO-EXEC] Scanning news...
✓ Tool executed successfully
{
  "articles": [
    {"title": "...", "link": "...", "source": "..."},
    ...
  ]
}
[NYX] Reading multiple timeline convergence points...
```

### Without API Keys (Fallback to Free APIs):
```
[YOU] >> /nyx
[NYX] NYX active. Observing.

[YOU] >> news
[NYX] [AUTO-EXEC] Scanning news...
✓ Tool executed successfully (using Hacker News fallback)
{
  "stories": [
    {"title": "...", "score": 542, "url": "..."},
    ...
  ]
}
[NYX] Detecting strong tech momentum in Timeline Φ...
```

---

## What Works WITHOUT API Keys

✅ **Always Available (No Keys Needed):**
- Google News (RSS)
- Google Trends (RSS)
- Hacker News
- CoinGecko crypto prices
- Weather data
- System diagnostics
- All BLADE commands

❌ **Requires API Key:**
- Custom Search API
- YouTube Data API

**Fallback Behavior:**
- If API keys not set, NYX will use free alternatives (Hacker News, RSS feeds)
- **Zero errors** - graceful degradation

---

## API Quotas & Limits

| API | Free Tier | Daily Limit | Cost if Exceeded |
|-----|-----------|-------------|------------------|
| Custom Search | 100 queries/day | 100 | $5/1000 queries |
| YouTube Data | 10,000 units/day | 10,000 | $0/month (generous) |
| Google News RSS | Unlimited | ∞ | FREE forever |
| Google Trends RSS | Unlimited | ∞ | FREE forever |

---

## Troubleshooting

### "GOOGLE_API_KEY not set" Error
**Solution:** Set the environment variable (see Step 4)

### "API error: 403"
**Causes:**
- API not enabled in Google Cloud Console
- API key restrictions blocking the request
- Quota exceeded

**Solution:**
1. Check API is enabled
2. Remove API key restrictions (or add allowed IPs)
3. Check quota usage

### "Custom Search Engine ID not found"
**Solution:** Create a CSE and set `GOOGLE_CSE_ID` env var

---

## Cost Optimization

**To stay FREE forever:**
1. Keep searches under 100/day (Custom Search)
2. Keep YouTube API calls reasonable (10K is generous)
3. Use Google News RSS (unlimited) for news
4. Use Google Trends RSS (unlimited) for trends
5. Use Hacker News (unlimited) as backup

**NYX automatically uses the cheapest option available.**

---

## Testing

```bash
# Navigate to kaedra_v006
cd c:\Users\super\Watchtower\kaedra_v006

# Run test
py -m kaedra

# Test Google tools
/nyx
news technology
search AI news
trends
youtube AI tutorial
```

---

## Integration Status

### KAEDRA v0.0.6
- ✅ Google tools module created (`core/google_tools.py`)
- ✅ Integrated into FREE_TOOLS registry
- ✅ NYX can auto-call Google APIs
- ✅ Graceful fallback if keys not set
- ✅ CLI triggers added

### NYX Capabilities
- ✅ Google Search
- ✅ Google News
- ✅ Google Trends
- ✅ YouTube Search
- ✅ YouTube Trending
- ✅ Automatic API selection (best free option)

### BLADE Capabilities
- ✅ System diagnostics (unchanged)
- ✅ Local commands (unchanged)

---

*"Your 115+ enabled APIs are now at NYX's command."* — NYX
