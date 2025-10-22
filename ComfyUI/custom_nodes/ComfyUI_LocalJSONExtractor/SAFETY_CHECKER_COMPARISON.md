# Safety Checker Comparison Guide

## Quick Overview

| Checker | Type | Model Size | Speed | Accuracy | Best For |
|---------|------|------------|-------|----------|----------|
| **ShieldGemma** | Dedicated safety classifier | 4B | ⚡⚡⚡ Fast | ⭐⭐⭐⭐⭐ Excellent | Production, strict moderation |
| **Florence2 + Llama3.1** | Caption + text analysis | 1B + 3B | ⚡ Slow | ⭐⭐⭐ Good | Custom categories, captions needed |
| **Qwen2.5-VL** | Vision-language model | 3B-7B | ⚡⚡ Medium | ⭐⭐⭐⭐ Very Good | Flexible, multi-purpose |

## Detailed Comparison

### 🛡️ ShieldGemma 2 (NEW)

**Technology**: Google's specialized safety classification model

**How it works**:
```
Image → ShieldGemma Model → 3 Safety Scores
                              ├─ Sexual Content
                              ├─ Dangerous Content  
                              └─ Violence/Gore
```

**Pros**:
- ✅ Purpose-built for safety (highest accuracy)
- ✅ Fastest (single pass, no caption generation)
- ✅ Standard safety policies (consistent definitions)
- ✅ Production-tested by Google
- ✅ Direct image analysis (no intermediate steps)
- ✅ 3 well-defined categories
- ✅ Probability scores for each category

**Cons**:
- ❌ Fixed 3 categories only (can't customize)
- ❌ 8GB model download (first time)
- ❌ Only safety classification (no captions)

**When to use**:
- Need highest accuracy for safety
- Building production systems
- Want standardized safety policies
- Don't need image captions
- Speed is important

**Example workflow**:
```
Load Image → ShieldGemma Safety Gate → [Processing] → Save
```

---

### 📷 Florence2 + Llama3.1 (CURRENT)

**Technology**: Image captioning model + text LLM

**How it works**:
```
Image → Florence2 → Caption → Llama3.1 → JSON Analysis
                                          ├─ NSFW
                                          └─ Violence
```

**Pros**:
- ✅ Generates detailed image captions
- ✅ Custom safety categories (define your own)
- ✅ Can extract other metadata (subjects, objects)
- ✅ Flexible prompt engineering
- ✅ Works well for product descriptions

**Cons**:
- ❌ Two-step process (slower)
- ❌ Indirect analysis (caption may miss details)
- ❌ Caption quality affects safety detection
- ❌ More prompt engineering needed
- ❌ Lower accuracy for edge cases

**When to use**:
- Need image captions anyway
- Want custom safety categories
- Need to extract subjects/metadata
- Have specific prompting requirements
- Processing product images with descriptions

**Example workflow**:
```
Load Image → Florence2 Run → Local JSON Extractor → LLM Safety Gate → [Processing]
```

---

### 👁️ Qwen2.5-VL (ALTERNATIVE)

**Technology**: Vision-language model with safety classification

**How it works**:
```
Image → Qwen2.5-VL → JSON Analysis
                      ├─ Description
                      ├─ NSFW
                      └─ Violence
```

**Pros**:
- ✅ Single model (simpler than Florence2 + Llama)
- ✅ Custom categories possible
- ✅ Good vision-language understanding
- ✅ Can generate descriptions + safety check
- ✅ Flexible prompting
- ✅ Multiple size options (3B, 7B)

**Cons**:
- ❌ General-purpose (not specialized for safety)
- ❌ Slower than ShieldGemma
- ❌ Requires GGUF or HF setup
- ❌ May need prompt tuning
- ❌ Less accurate than ShieldGemma for safety

**When to use**:
- Need both descriptions and safety
- Want flexibility in categories
- Already using Qwen for other tasks
- Need good balance of features
- Want single-model solution

**Example workflow**:
```
Load Image → Vision Safety Checker (Qwen2.5-VL-HF) → Image Safety Gate → [Processing]
```

---

## Performance Comparison

### Speed Test (Approximate)

On typical hardware (RTX 3090 / 4090):

| Checker | Time per Image | Bottleneck |
|---------|----------------|------------|
| ShieldGemma | ~0.5-1s | Model inference |
| Florence2 + Llama | ~2-3s | Two model passes |
| Qwen2.5-VL | ~1-2s | Vision encoder + LLM |

### Accuracy (Subjective)

Based on safety detection accuracy:

| Content Type | ShieldGemma | Florence2+Llama | Qwen2.5-VL |
|--------------|-------------|-----------------|------------|
| Explicit sexual content | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Subtle suggestive content | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| Weapons/dangerous items | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Violence/gore | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Context understanding | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## Migration Guide

### From Florence2 + Llama to ShieldGemma

**Before (Florence2 + Llama)**:
```
Load Image
    ↓
Florence2 Run (detailed caption)
    ↓
Local JSON Extractor (Llama3.1)
    ↓
Image Safety Gate
    ↓
[Processing]
```

**After (ShieldGemma)**:
```
Load Image
    ↓
ShieldGemma Safety Gate
    ↓
[Processing]
```

**Changes**:
1. Remove Florence2 Run node
2. Remove Local JSON Extractor node
3. Replace Image Safety Gate with ShieldGemma Safety Gate
4. Adjust threshold if needed (default 0.5 works well)

**Benefits**:
- 2-3x faster
- Higher accuracy
- Simpler workflow
- Less memory usage (after model load)

---

### From Qwen2.5-VL to ShieldGemma

**Before (Qwen2.5-VL)**:
```
Load Image
    ↓
Vision Safety Checker (Qwen2.5-VL-HF)
    ↓
Image Safety Gate
    ↓
[Processing]
```

**After (ShieldGemma)**:
```
Load Image
    ↓
ShieldGemma Safety Gate
    ↓
[Processing]
```

**Changes**:
1. Replace Vision Safety Checker with ShieldGemma Safety Gate
2. Adjust parameters (ShieldGemma has fewer options)

**Benefits**:
- Faster inference
- Higher safety detection accuracy
- Standardized categories
- Less prompt engineering

---

## Combining Multiple Checkers

For maximum safety, use multiple checkers in sequence or parallel:

### Sequential (Strict)
```
Load Image
    ↓
ShieldGemma Safety Gate (fast, catches obvious violations)
    ↓
Qwen2.5-VL Safety Check (context-aware, custom categories)
    ↓
[Processing only if both pass]
```

### Parallel (Analysis)
```
Load Image
    ↓
├─ ShieldGemma Safety Checker → scores
├─ Qwen2.5-VL Safety Checker → scores + description
│
└─ [Combine results with custom logic]
```

---

## Recommendations by Use Case

### 🏭 Production Content Moderation
**Recommended**: ShieldGemma Safety Gate
- Highest accuracy for safety
- Fast processing
- Reliable and tested

### 🛍️ E-commerce Product Images
**Recommended**: Florence2 + Llama OR ShieldGemma
- Florence2 if you need product descriptions
- ShieldGemma if you only need safety check

### 🎨 Creative AI Workflows
**Recommended**: Qwen2.5-VL
- Flexible safety definitions
- Can provide creative descriptions
- Good balance of features

### ⚡ Batch Processing (Speed Critical)
**Recommended**: ShieldGemma
- Fastest single-model solution
- Can keep model loaded
- Efficient GPU usage

### 🎯 Custom Safety Policies
**Recommended**: Florence2 + Llama OR Qwen2.5-VL
- ShieldGemma has fixed 3 categories
- Other options allow custom prompts

### 🔬 Research & Experimentation
**Recommended**: Try all three!
- Compare accuracy on your dataset
- Test edge cases
- Choose what works best

---

## Cost Comparison

### VRAM Usage

| Checker | Model Load | Peak Usage | Notes |
|---------|------------|------------|-------|
| ShieldGemma | ~8GB | ~10GB | FP16, one-time load |
| Florence2 + Llama | ~2GB + ~4GB | ~8GB | Two models, can unload between |
| Qwen2.5-VL (3B) | ~6GB | ~8GB | 8-bit quantization |
| Qwen2.5-VL (7B) | ~10GB | ~12GB | 8-bit quantization |

### Disk Space

| Checker | Model Files | Cache |
|---------|-------------|-------|
| ShieldGemma | ~8GB | ~8GB HF cache |
| Florence2 | ~1GB | |
| Llama3.1 (3B GGUF) | ~2.5GB | |
| Qwen2.5-VL (3B) | ~6GB | HF cache |

---

## Summary

| Scenario | Best Choice | Reason |
|----------|-------------|--------|
| Need highest safety accuracy | **ShieldGemma** | Purpose-built, tested |
| Need fastest processing | **ShieldGemma** | Single-pass analysis |
| Need image captions | **Florence2 + Llama** | Generates descriptions |
| Need custom categories | **Qwen2.5-VL** or **Florence2+Llama** | Flexible prompting |
| Production deployment | **ShieldGemma** | Most reliable |
| Resource-constrained | **Florence2 + Llama** | Smaller models |
| Multi-purpose vision | **Qwen2.5-VL** | Single model, multiple tasks |

---

## Getting Started

1. **Install ShieldGemma**:
   ```bash
   pip install transformers accelerate
   ```

2. **Add node to workflow**:
   - Search for "ShieldGemma" in node menu
   - Add "ShieldGemma Safety Gate" to your workflow

3. **Connect**:
   ```
   Load Image → ShieldGemma Safety Gate → [Your nodes]
   ```

4. **Configure**:
   - Set threshold (default 0.5 is good)
   - Choose which categories to check
   - Adjust `keep_model_loaded` based on usage

5. **Test**:
   - Run with safe test image
   - Check console output
   - Verify gate passes/blocks correctly

---

## Questions?

See the full guides:
- [ShieldGemma Guide](./SHIELDGEMMA_GUIDE.md)
- [BEN2 Safety Workflow](./BEN2_SAFETY_WORKFLOW.md)
- [Vision Safety Checker Documentation](./vision_safety_checker.py)
