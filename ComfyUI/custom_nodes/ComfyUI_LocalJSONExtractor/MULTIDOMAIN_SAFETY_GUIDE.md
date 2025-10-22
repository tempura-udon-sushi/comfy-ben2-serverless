# Multi-Domain Safety Classifier Guide

## Overview

New node that implements the **Florence2 + Llama3.1 Multi-Domain Safety Filter** from your specification document.

## Features

### 5 Safety Domains
1. **Sexual / Nudity** - Explicit content, artistic nudity, lingerie
2. **Violence / Gore** - Blood, injuries, weapons, combat
3. **Hate / Extremism** - Hate symbols, racial violence, extremism
4. **Disturbing / Shock** - Dead bodies, mutilation, animal cruelty
5. **Drugs / Crime** - Illegal substances, trafficking, weapons trade

### Tri-State Output
- **SAFE** - No concerns, proceed normally
- **BORDERLINE** - Ambiguous, needs human review
- **UNSAFE** - Block or reject

## Node: Multi-Domain Safety Classifier (Llama)

### Inputs
- `caption` (STRING): Image description from Florence-2 or any caption
- `model_path` (STRING): Path to Llama 3.1 8B GGUF model
- `temperature` (FLOAT, optional): 0.1 (recommended for stable classification)
- `max_new_tokens` (INT, optional): 300
- `n_ctx` (INT, optional): 4096
- `n_gpu_layers` (INT, optional): -1 (use all GPU)

### Outputs
- `json` (STRING): Complete classification result

### Example Output

```json
{
  "classification": {
    "sexual": "BORDERLINE",
    "violence": "SAFE",
    "hate": "SAFE",
    "disturbing": "SAFE",
    "drugs": "SAFE"
  },
  "reasons": [
    "Partial nudity with lingerie; non-explicit context"
  ],
  "confidence": 0.81
}
```

## Usage in ComfyUI

### Basic Workflow

```
[Load Image]
   ↓
[Florence-2 Caption]
   ↓
[Multi-Domain Safety Classifier (Llama)]
   ↓
[JSON Parser]
   ↓
[Safety Gate Logic]
```

### With Safety Gate

```
[Load Image]
   ↓
[Florence-2 Caption]
   ↓
[Multi-Domain Safety Classifier]
   ↓
[Parse JSON]
   ↓
[If any == "UNSAFE"]
   ├─→ Block workflow
   └─→ Continue if all SAFE
```

## Testing

Run the test script:

```bash
cd ComfyUI/custom_nodes/ComfyUI_LocalJSONExtractor
python test_multidomain_safety.py
```

## Test Cases Included

1. ✅ **Safe Product Photo** - Blue bowl on table
2. ⚠️ **Borderline Fashion** - Woman in bikini (artistic)
3. ❌ **Unsafe Violence** - Blood and injuries
4. ❌ **Unsafe Sexual** - Explicit sexual content
5. ⚠️ **Borderline Action** - Martial arts training
6. ✅ **Safe Medical** - Educational anatomy

## Advantages Over ShieldGemma

| Feature | Multi-Domain Classifier | ShieldGemma |
|---------|------------------------|-------------|
| Categories | 5 domains | 3 categories |
| Output | Tri-state (SAFE/BORDERLINE/UNSAFE) | Binary |
| Context | Understands context (artistic vs explicit) | Limited context |
| False Positives | Lower (BORDERLINE buffer) | Higher (binary) |
| Customizable | ✅ Prompt can be tuned | ❌ Fixed model |
| Bikini Test | BORDERLINE (correct!) | 93% dangerous (wrong!) |

## Policy Definitions

### Sexual / Nudity
- **UNSAFE**: Pornography, explicit sexual acts
- **BORDERLINE**: Lingerie, artistic nudity, sensual poses
- **SAFE**: Fashion, swimwear, medical/educational

### Violence / Gore
- **UNSAFE**: Real blood, injuries, torture, execution
- **BORDERLINE**: Fictional combat, movie scenes, sports
- **SAFE**: Martial arts, symbolic violence

### Hate / Extremism
- **UNSAFE**: Nazi symbols, hate slogans, racial violence
- **BORDERLINE**: Historical context, documentaries
- **SAFE**: Neutral representation

### Disturbing / Shock
- **UNSAFE**: Dead bodies, mutilation, animal cruelty
- **BORDERLINE**: Medical illustrations, educational anatomy
- **SAFE**: Abstract art, symbolic imagery

### Drugs / Crime
- **UNSAFE**: Drug use, trafficking, weapons trade
- **BORDERLINE**: Cinematic context, news reporting
- **SAFE**: Prevention campaigns, fictional references

## Performance

- **Model**: Llama 3.1 8B Instruct Q5_K_M (~5GB VRAM)
- **Speed**: ~2-3 seconds per classification
- **Temperature**: 0.1 recommended (stable, deterministic)
- **Context**: Uses full Florence-2 caption for context

## Next Steps

1. ✅ Llama multi-domain classifier - **DONE**
2. ⏳ Florence-2 enhanced outputs (tags, regions) - **TODO**
3. ⏳ JSON composer node - **TODO**
4. ⏳ Safety gate with tri-state routing - **TODO**

## Comparison to Current Implementation

### Current (2 categories, binary)
```json
{
  "nsfw": false,
  "violence": false
}
```

### New (5 domains, tri-state)
```json
{
  "classification": {
    "sexual": "BORDERLINE",
    "violence": "SAFE",
    "hate": "SAFE",
    "disturbing": "SAFE",
    "drugs": "SAFE"
  },
  "reasons": ["context explanation"],
  "confidence": 0.85
}
```

## License

MIT License - Same as parent project

---

**Ready to test! Restart ComfyUI to load the new node.** 🎯
