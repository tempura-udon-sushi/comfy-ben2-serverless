# Hybrid Safety System: NudeNet + Multi-Domain Classifier

## Overview

Best-of-both-worlds approach combining:
- **NudeNet** - Specialized nude detection (highly accurate for sexual content)
- **Llama Multi-Domain** - Contextual understanding (violence, hate, disturbing, drugs)

## Why Hybrid?

### Problem with Llama Alone
- Text-based classification can miss visual nudity
- "Woman in artistic pose" might pass even if topless
- Context understanding but lacks visual precision

### Problem with NudeNet Alone
- Only detects nudity/sexual content
- Doesn't check violence, hate, disturbing content, drugs
- No context understanding

### Solution: Hybrid
✅ NudeNet catches **visual nudity** (even if caption is vague)
✅ Llama catches **other harmful content** (violence, hate, drugs)
✅ Llama provides **context** (artistic vs explicit)

## Installation

```bash
pip install nudenet
```

## Available Nodes

### 1. NudeNet Safety Checker
Specialized nude detection using computer vision.

**Inputs:**
- `image` (IMAGE): Image to check
- `threshold` (FLOAT, default 0.6): Detection confidence threshold

**Outputs:**
- `json` (STRING): Full detection results
- `is_nsfw` (BOOLEAN): True if nudity detected
- `max_score` (FLOAT): Highest detection score

**Detects:**
- FEMALE_BREAST_EXPOSED
- FEMALE_GENITALIA_EXPOSED
- MALE_GENITALIA_EXPOSED
- ANUS_EXPOSED
- BUTTOCKS_EXPOSED

### 2. Hybrid Safety Gate
Combines NudeNet + Multi-Domain Classifier.

**Inputs:**
- `image` (IMAGE): Image to check
- `nudenet_json` (STRING): Output from NudeNet Safety Checker
- `multidomain_json` (STRING): Output from Multi-Domain Safety Classifier
- `block_unsafe` (BOOLEAN, default True): Block UNSAFE classifications
- `block_borderline` (BOOLEAN, default False): Block BORDERLINE classifications
- `nudenet_overrides_llama` (BOOLEAN, default True): NudeNet sexual detection overrides Llama

**Outputs:**
- `image` (IMAGE): Passes through if safe
- `status` (STRING): Status message

## Recommended Workflow

### Maximum Protection (Recommended)

```
[Load Image]
    ↓
    ├──> [Florence-2 Caption]
    │        ↓
    │    [Multi-Domain Safety Classifier (Llama)]
    │        ↓
    └──────→ [NudeNet Safety Checker]
                ↓
            [Hybrid Safety Gate]
                ↓
            [Continue workflow if safe]
```

### Configuration

**Hybrid Safety Gate Settings:**
- `block_unsafe`: ✅ True (block explicit content)
- `block_borderline`: ❌ False (allow artistic/contextual)
- `nudenet_overrides_llama`: ✅ True (trust visual detection over text)

**NudeNet Threshold:**
- `0.4` - Very strict (may have false positives)
- `0.6` - **Recommended** (balanced)
- `0.8` - Lenient (only obvious nudity)

## Test Cases

### Case 1: Topless Woman
**NudeNet:** ❌ NSFW (FEMALE_BREAST_EXPOSED, score: 0.95)
**Llama:** ✅ SAFE (might miss if caption is vague)
**Result:** ❌ **BLOCKED** (NudeNet overrides)

### Case 2: Bikini on Beach
**NudeNet:** ✅ SAFE (no exposed parts)
**Llama:** ⚠️ BORDERLINE (sexual: BORDERLINE)
**Result:** ✅ **ALLOWED** (not blocking BORDERLINE)

### Case 3: Violent Scene
**NudeNet:** ✅ SAFE (no nudity)
**Llama:** ❌ UNSAFE (violence: UNSAFE)
**Result:** ❌ **BLOCKED** (Llama catches violence)

### Case 4: Hate Symbol
**NudeNet:** ✅ SAFE (no nudity)
**Llama:** ❌ UNSAFE (hate: UNSAFE)
**Result:** ❌ **BLOCKED** (Llama catches hate)

## Advantages

| Feature | Single Model | Hybrid System |
|---------|-------------|---------------|
| **Detect visual nudity** | ⚠️ Limited | ✅ Excellent (NudeNet) |
| **Context understanding** | ✅ Good | ✅ Good (Llama) |
| **Violence detection** | ✅ Good | ✅ Good (Llama) |
| **Hate symbol detection** | ✅ Good | ✅ Good (Llama) |
| **False positives** | ⚠️ Higher | ✅ Lower |
| **False negatives (nudity)** | ⚠️ Higher | ✅ Lower |

## Performance

### NudeNet
- **Speed:** ~0.5-1s per image
- **VRAM:** ~1GB
- **Model:** ONNX (optimized)

### Total Pipeline
- Florence-2: ~0.5s
- Multi-Domain Classifier: ~2-3s
- NudeNet: ~0.5-1s
- **Total:** ~3-4.5s per image

### For Production
- Run on GPU (CUDA)
- Batch processing when possible
- Cache model loading

## Troubleshooting

### "nudenet not installed"
```bash
pip install nudenet
```

### Slow performance
- Ensure GPU is available
- Check CUDA installation
- Reduce image resolution before checking

### False positives (blocking safe images)
- Lower NudeNet threshold to 0.7-0.8
- Set `block_borderline` to False
- Review Llama prompt examples

### False negatives (missing unsafe images)
- Lower NudeNet threshold to 0.4-0.5
- Set `block_borderline` to True
- Add more specific examples to Llama prompt

## Migration from Old System

### Old (Single Gate)
```
Florence-2 → LocalJSONExtractor → ImageSafetyGate
```

### New (Hybrid)
```
Florence-2 → Multi-Domain Classifier ┐
                                     ├→ Hybrid Safety Gate
NudeNet Checker                     ┘
```

## License

- NudeNet: MIT License
- Multi-Domain Classifier: MIT License

## Credits

- NudeNet: https://github.com/notAI-tech/NudeNet
- ComfyUI-Nudenet reference: https://github.com/phuvinh010701/ComfyUI-Nudenet

---

**Result: Industry-grade safety filtering with minimal false positives!** 🎯
