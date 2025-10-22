# Safety Check for BEN2/BiRefNet Workflows

## Overview

Unlike the Qwen workflow which uses prompts, BEN2 and BiRefNet workflows perform background removal without text prompts. However, we still need to check input images for inappropriate content before processing.

## Current BEN2 Workflow (Without Safety)

```
Load Image → Smart Resize → BEN2 ONNX Remove Background → Restore Original Size → Free VRAM → Save Image
```

## New BEN2 Workflow (With Safety Check)

```
Load Image 
    ↓
Florence2 Run (detailed caption task)
    ↓
Local JSON Extractor (llama.cpp)
    ↓
Image Safety Gate ← (receives IMAGE + JSON)
    ↓ (passes IMAGE through if safe)
Smart Resize
    ↓
BEN2 ONNX Remove Background
    ↓
Restore Original Size
    ↓
Free VRAM (Inline)
    ↓
Save Image
```

## Node Setup

### 1. Florence2 Run
- **Input**: Original loaded image
- **Task**: Use "detailed caption" or similar analysis task
- **Output**: Caption text describing the image

### 2. Local JSON Extractor (llama.cpp)
- **Input**: Caption from Florence2
- **Model**: Your configured llama.cpp model (e.g., Qwen2.5-3B)
- **Output**: JSON string with `primary_subject`, `nsfw`, `violence` flags

### 3. Image Safety Gate (NEW)
- **Inputs**:
  - `image`: The original image (from Load Image node)
  - `json_string`: Safety analysis from Local JSON Extractor
- **Optional Settings**:
  - `stop_on_nsfw`: Block NSFW content (default: True)
  - `stop_on_violence`: Block violent content (default: True)
- **Outputs**:
  - `image`: Passes through the original image if safe
  - `primary_subject`: Text description of main subject
  - `nsfw`: Boolean flag
  - `violence`: Boolean flag
- **Behavior**:
  - ✅ If content is safe → passes IMAGE through to next node
  - ❌ If content is unsafe → raises error and stops workflow

### 4. Continue with BEN2 Processing
- Connect the `image` output from Image Safety Gate to Smart Resize
- The rest of the workflow remains unchanged

## Key Differences from Qwen Workflow

| Aspect | Qwen Workflow | BEN2/BiRefNet Workflow |
|--------|---------------|------------------------|
| **Safety Gate Node** | LLM Safety Gate (JSON) | **Image Safety Gate** |
| **Input Type** | JSON string only | IMAGE + JSON string |
| **Output Type** | Text (primary_subject) | IMAGE + metadata |
| **Use of Analysis** | Builds prompts for image editing | Just checks safety, no prompt building |
| **Workflow Continuation** | Text → Dynamic Prompt Builder | Image → Smart Resize/Background Removal |

## Example JSON Format

The Local JSON Extractor should output JSON in this format:

```json
{
  "primary_subject": "a person wearing a red shirt",
  "secondary_subjects": ["background furniture", "wall decoration"],
  "nsfw": false,
  "violence": false
}
```

## Safety Check Behavior

### Safe Content Example:
```
[ImageSafetyGate] Checking content: 'a handmade ceramic vase with blue glaze...'
[ImageSafetyGate] NSFW: False, Violence: False
[ImageSafetyGate] ✅ SAFE: Image passed safety check
```
→ Image passes through to background removal

### Unsafe Content Example:
```
[ImageSafetyGate] Checking content: 'explicit adult content...'
[ImageSafetyGate] NSFW: True, Violence: False
[ImageSafetyGate] ❌ BLOCKED: NSFW content detected. Subject: 'explicit adult content'
```
→ Workflow stops with error, image is NOT processed

## Benefits

1. **Input Validation**: Screens inappropriate content before resource-intensive processing
2. **Resource Efficiency**: Avoids wasting GPU/CPU on blocked content
3. **Consistent Safety**: Same safety standards as Qwen workflow
4. **Flexible**: Can disable specific checks (NSFW/violence) if needed
5. **Pass-through Design**: Doesn't modify the image, just gates it

## Notes

- The safety check happens BEFORE resizing/processing, saving resources
- You can optionally use the `primary_subject` output for logging or metadata
- The IMAGE passes through unchanged - safety gate only controls execution flow
- Compatible with both BEN2 and BiRefNet background removal workflows
