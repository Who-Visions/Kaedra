# KAEDRA Model Strategy (With $1,000 Credits)

**Credits Available:** $1,000  
**Strategy:** Maximize quality and capability, optimize for credit longevity  
**Last Updated:** 2025-11-27

---

## 💰 Budget Reality Check

### Credit Burn Rate Analysis

**Current Usage:** ~775 requests/month

| Scenario | Model Mix | Monthly Cost | Credits Last |
|----------|-----------|--------------|--------------|
| **All Gemini 3 Pro** | Maximum quality | ~$11/month | 90+ months |
| **Recommended Mix** | Balanced quality | ~$6/month | 166+ months |
| **All Flash-Lite** | Ultra-cheap | ~$0.80/month | 1,250 months |

**Key Insight:** With $1,000 credits, you can afford to use **premium models** for YEARS.

---

## 🎯 Recommended Model Assignment (Quality-First)

### **KAEDRA** (Main Orchestrator)
- ✅ **Model:** `gemini-2.5-flash`
- ✅ **Cost:** $0.30 input, $2.50 output
- ✅ **Why:** Fast, smart, handles complex routing
- 💰 **Monthly:** ~$2

### **NYX** (Timeline Oracle - Premium Intelligence)
- ✅ **Model:** `gemini-2.5-pro` (or 3 Pro for critical scans)
- ✅ **Cost:** $1.25-$4.00 input, $10.00-$18.00 output
- ✅ **Why:** Best reasoning for signal analysis, worth the cost
- 💰 **Monthly:** ~$3-5

### **BLADE** (System Executor - Efficiency)
- ✅ **Model:** `gemini-2.5-flash`
- ✅ **Cost:** $0.30 input, $2.50 output
- ✅ **Why:** Quick execution, good enough for commands
- 💰 **Monthly:** ~$1

---

## 🔥 When to Use Each Model

### **Gemini 3 Pro Preview** ($14/1M) - The Beast
**Use for:**
- ✅ Critical NYX timeline analysis
- ✅ Complex multi-step reasoning
- ✅ High-stakes decision making
- ✅ Advanced agentic tasks

**Monthly allocation:** $2-3 (200-250K tokens)

### **Gemini 2.5 Pro** ($11.25/1M) - The Workhorse
**Use for:**
- ✅ NYX signal analysis
- ✅ Complex code generation
- ✅ Deep reasoning tasks
- ✅ Council mode deliberations

**Monthly allocation:** $3-4 (300-400K tokens)

### **Gemini 2.5 Flash** ($2.80/1M) - The Default
**Use for:**
- ✅ KAEDRA orchestration
- ✅ BLADE execution
- ✅ General queries
- ✅ 90% of daily tasks

**Monthly allocation:** Unlimited (main workhorse)

### **Gemini 2.5 Flash-Lite** ($0.50/1M) - The Backup
**Use for:**
- ✅ Ultra-simple commands
- ✅ Testing/debugging
- ✅ Batch operations

**Monthly allocation:** Minimal (only when Flash is overkill)

---

## 💡 Smart Optimizations (Even With Credits)

### 1. **Use Batch API** (50% savings, same quality)
```python
# NYX scanning 1000 signals/month
# Standard: $11.25 → Batch: $5.625
# SAME QUALITY, HALF COST
# Credits last 2x longer
```

### 2. **Context Caching** (90% savings on repeated context)
```python
# KAEDRA system prompts cached
# Repeated context: $0.30 → $0.03 (90% off)
# NYX timeline memory: $1.25 → $0.125 (90% off)
```

### 3. **Smart Model Routing**
```python
def route_query(query, context):
    if "critical" in query or "timeline scan" in query:
        return "gemini-3-pro"  # Best quality
    elif context.complexity > 7:
        return "gemini-2.5-pro"  # Strong reasoning
    else:
        return "gemini-2.5-flash"  # Fast & smart default
```

---

## 📊 Monthly Budget Breakdown (Optimized)

### Conservative Estimate (Current Usage)
```
KAEDRA (Flash): 400 requests × 2K tokens = 800K tokens
  Input:  800K × $0.30/1M = $0.24
  Output: 800K × $2.50/1M = $2.00
  Subtotal: $2.24

NYX (Pro): 250 requests × 3K tokens = 750K tokens
  Input:  750K × $1.25/1M = $0.94
  Output: 750K × $10/1M = $7.50
  Subtotal: $8.44

BLADE (Flash): 125 requests × 1.5K tokens = 188K tokens
  Input:  188K × $0.30/1M = $0.06
  Output: 188K × $2.50/1M = $0.47
  Subtotal: $0.53

TOTAL: ~$11/month
Credits last: 90+ months (7.5 years!)
```

### With Optimizations (Batch + Cache)
```
Same usage, 50% batch discount + 30% cache savings
TOTAL: ~$6/month
Credits last: 166+ months (13.8 years!)
```

---

## 🎯 Implementation Updates for KAEDRA

### Update `config.py` with Premium Models

```python
# kaedra/core/config.py

MODELS = {
    # Premium tier (your setup)
    "ultra": "gemini-3-pro-preview",           # $14/1M - Critical tasks
    "pro": "gemini-2.5-pro",                   # $11.25/1M - Complex reasoning
    "flash": "gemini-2.5-flash",               # $2.80/1M - Default
    "lite": "gemini-2.5-flash-lite",           # $0.50/1M - Simple tasks
}

MODEL_COSTS = {
    "ultra": 0.038,  # Estimated per ~2K query
    "pro": 0.031,
    "flash": 0.008,
    "lite": 0.001,
}

# Agent-specific model assignments
AGENT_MODELS = {
    "kaedra": "flash",   # Smart default
    "nyx": "pro",        # Premium intelligence
    "blade": "flash",    # Fast execution
}

# Context for model selection
MODEL_ROUTING = {
    "critical_threshold": "ultra",     # Use 3 Pro for critical tasks
    "complex_threshold": "pro",        # Use 2.5 Pro for complex reasoning
    "default": "flash",                # Use Flash for everything else
}
```

### Enable Batch API

```python
# kaedra/services/prompt.py

class PromptService:
    def __init__(self, model_key="flash", use_batch=False):
        self.model_key = model_key
        self.use_batch = use_batch  # 50% cost reduction
        
    def generate_batch(self, prompts: list):
        """
        Use Batch API for bulk operations
        50% cost savings, same quality
        """
        # Implementation here
        pass
```

### Enable Context Caching

```python
# kaedra/services/prompt.py

class PromptService:
    def __init__(self, model_key="flash", enable_cache=True):
        self.cache_enabled = enable_cache
        self.cached_contexts = {}
        
    def generate_with_cache(self, prompt, context):
        """
        Cache frequently used context
        90% savings on cached portions
        """
        if self.cache_enabled and context in self.cached_contexts:
            # Use cached context
            cache_token_cost = 0.03  # vs 0.30 standard
        else:
            # Cache new context
            self.cached_contexts[context] = True
```

---

## 📈 Credit Longevity Scenarios

### Scenario 1: Ultra-Premium (Use Best Models)
```
All Gemini 3 Pro: $14/month
Credits last: 71 months (6 years)
Quality: MAXIMUM
```

### Scenario 2: Balanced Premium (Recommended)
```
Mix of Pro/Flash: $6-8/month
Credits last: 120+ months (10+ years)
Quality: EXCELLENT
```

### Scenario 3: Conservative Premium
```
Mostly Flash, Pro for NYX: $3-4/month
Credits last: 250+ months (20+ years)
Quality: VERY GOOD
```

---

## 🚀 **RECOMMENDED STRATEGY**

### **Use "Balanced Premium"**

**Why:**
1. ✅ Gemini 2.5 Pro for NYX = best signal analysis
2. ✅ Gemini 2.5 Flash for KAEDRA/BLADE = fast & smart
3. ✅ Gemini 3 Pro for critical decisions only
4. ✅ Credits last 10+ years
5. ✅ Always get high-quality results

**Monthly Cost:** $6-8  
**Credits Last:** 120-166 months  
**Quality:** Excellent across all agents

---

## ✅ Action Items

### Immediate
1. ✅ Update KAEDRA config with premium models
2. ✅ Set NYX default to `gemini-2.5-pro`
3. ✅ Keep KAEDRA/BLADE on `gemini-2.5-flash`
4. ✅ Enable context caching

### Short-term
1. ⏳ Implement Batch API for NYX bulk scanning
2. ⏳ Add smart model routing (critical → 3 Pro)
3. ⏳ Monitor credit burn rate monthly

### Long-term
1. 🔮 Adjust model mix based on usage patterns
2. 🔮 Optimize caching strategy
3. 🔮 Scale up if needed (you have the credits!)

---

## 💰 Bottom Line

**With $1,000 credits:**
- Don't penny-pinch on model quality
- Use Gemini 2.5 Pro as default for NYX
- Use Gemini 2.5 Flash for KAEDRA/BLADE
- Save Gemini 3 Pro for critical moments
- Enable Batch API & Caching = 2x credit longevity
- Your credits will last **10+ YEARS** easily

**Estimated monthly spend:** $6-8  
**Credits exhausted:** ~2035 (10+ years from now)

🎯 **Stop worrying about cost. Focus on getting the best results.**
