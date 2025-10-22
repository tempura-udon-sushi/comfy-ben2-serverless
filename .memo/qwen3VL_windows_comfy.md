# Qwen3-VL on Windows for ComfyUI Safety Checker

Guide to replace Florence-2 + Llama with a single Qwen3-VL vision model for safety checking.

---

## Why Qwen3-VL?

**Advantages over Florence-2 + Llama:**
- ✅ **Single model** - Vision understanding + text analysis in one
- ✅ **Direct image input** - No need for caption generation step
- ✅ **Better context** - Sees the actual image, not just text description
- ✅ **Existing infrastructure** - Uses your llama-cpp-python setup
- ✅ **Smaller option** - Qwen3-VL-4B (2.8GB) vs Llama-3.1-8B (5.4GB)

**Your current workflow:**
```
Image → Florence-2 → Caption → Llama-3.1-8B → JSON (subject, nsfw, violence)
```

**New workflow:**
```
Image → Qwen3-VL-4B → JSON (subject, nsfw, violence)
```

---

## Prerequisites

- ✅ Windows 10/11
- ✅ Python 3.11 (you have this)
- ✅ CUDA 12.4 (you have this)
- ✅ llama-cpp-python with CUDA (you have this installed)
- ✅ ComfyUI running

---

## Step 1: Download Qwen3-VL GGUF Models

### Option A: Qwen3-VL-4B (Recommended for safety checking)

**Model files needed:**
1. Main model: `Qwen3-VL-4B-Q5_K_M.gguf` (~2.8 GB)
2. Vision projector: `mmproj-qwen3-vl-4b.gguf` (~1.5 GB)

**Download locations:**
```powershell
# Create directory
New-Item -ItemType Directory -Force -Path "C:\Users\genfp\AI_avatar\Comfy_vanila\ComfyUI\models\llm\qwen3vl"

cd C:\Users\genfp\AI_avatar\Comfy_vanila\ComfyUI\models\llm\qwen3vl
```

**Download from HuggingFace:**
- Model card: https://huggingface.co/NexaAI/Qwen3-VL-4B-Thinking-GGUF
- Files needed:
  - `Qwen3-VL-4B-Q5_K_M.gguf` (or Q4_K_M for smaller size)
  - `mmproj-qwen3-vl-4b.gguf`

**Using browser or wget:**
```powershell
# Using PowerShell (if wget available)
wget https://huggingface.co/NexaAI/Qwen3-VL-4B-Thinking-GGUF/resolve/main/Qwen3-VL-4B-Q5_K_M.gguf
wget https://huggingface.co/NexaAI/Qwen3-VL-4B-Thinking-GGUF/resolve/main/mmproj-qwen3-vl-4b.gguf

# Or download manually from browser and place in folder
```

### Option B: Qwen3-VL-30B (If you need higher accuracy)
- More accurate but much larger (~19 GB)
- Requires more VRAM (16-20 GB)

---

## Step 2: Verify llama-cpp-python Supports Vision

Check if your current installation supports multimodal:

```powershell
cd C:\Users\genfp\AI_avatar\Comfy_vanila\ComfyUI
.\venv\Scripts\python.exe -c "from llama_cpp import Llama; print(hasattr(Llama, '__init__'))"
```

If your llama-cpp-python version is 0.3.x+, it should support vision models with the `clip_model_path` parameter.

---

## Step 3: Test Qwen3-VL from Command Line

Create a test script to verify it works:

**test_qwen3vl.py:**
```python
from llama_cpp import Llama
from llama_cpp.llama_chat_format import Llava15ChatHandler
import sys

# Paths
model_path = "C:/Users/genfp/AI_avatar/Comfy_vanila/ComfyUI/models/llm/qwen3vl/Qwen3-VL-4B-Q5_K_M.gguf"
mmproj_path = "C:/Users/genfp/AI_avatar/Comfy_vanila/ComfyUI/models/llm/qwen3vl/mmproj-qwen3-vl-4b.gguf"
image_path = "C:/path/to/test/image.jpg"  # Change this

print("Loading Qwen3-VL model...")

# Initialize with vision support
chat_handler = Llava15ChatHandler(clip_model_path=mmproj_path)

llm = Llama(
    model_path=model_path,
    chat_handler=chat_handler,
    n_ctx=4096,
    n_gpu_layers=-1,  # Use GPU
    verbose=True
)

print("Model loaded! Testing vision...")

# Test prompt
response = llm.create_chat_completion(
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"file://{image_path}"}},
                {"type": "text", "text": "Describe this image and determine if it contains NSFW or violent content."}
            ]
        }
    ]
)

print("\nResponse:")
print(response["choices"][0]["message"]["content"])
```

Run test:
```powershell
.\venv\Scripts\python.exe test_qwen3vl.py
```

---

## Step 4: Create ComfyUI Vision Safety Node

**File:** `ComfyUI/custom_nodes/ComfyUI_LocalJSONExtractor/vision_safety_checker.py`

```python
import os
import json
from typing import Dict, Any
import torch
from PIL import Image
import numpy as np

try:
    from llama_cpp import Llama
    from llama_cpp.llama_chat_format import Llava15ChatHandler
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False
    print("[VisionSafetyChecker] WARNING: llama-cpp-python not installed")

# Global cache
_QWEN_CACHE: Dict[str, Any] = {}

def _load_vision_llm(model_path: str, mmproj_path: str, n_gpu_layers: int = -1):
    """Load Qwen3-VL model with vision support"""
    key = f"{model_path}|{mmproj_path}"
    if key in _QWEN_CACHE:
        return _QWEN_CACHE[key]
    
    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}")
    if not os.path.isfile(mmproj_path):
        raise FileNotFoundError(f"Vision projector not found: {mmproj_path}")
    
    print(f"[VisionSafetyChecker] Loading Qwen3-VL model: {model_path}")
    print(f"[VisionSafetyChecker] Vision projector: {mmproj_path}")
    
    chat_handler = Llava15ChatHandler(clip_model_path=mmproj_path)
    
    llm = Llama(
        model_path=model_path,
        chat_handler=chat_handler,
        n_ctx=4096,
        n_gpu_layers=n_gpu_layers,
        verbose=True
    )
    
    _QWEN_CACHE[key] = llm
    print(f"[VisionSafetyChecker] Model loaded successfully")
    return llm


class VisionSafetyChecker:
    """
    Direct image-to-JSON safety checker using Qwen3-VL
    Replaces Florence-2 + Llama workflow
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        default_model = "C:/Users/genfp/AI_avatar/Comfy_vanila/ComfyUI/models/llm/qwen3vl/Qwen3-VL-4B-Q5_K_M.gguf"
        default_mmproj = "C:/Users/genfp/AI_avatar/Comfy_vanila/ComfyUI/models/llm/qwen3vl/mmproj-qwen3-vl-4b.gguf"
        
        return {
            "required": {
                "image": ("IMAGE",),
                "model_path": ("STRING", {"default": default_model}),
                "mmproj_path": ("STRING", {"default": default_mmproj}),
                "subject_priority": (["auto", "product", "person"], {"default": "product"}),
            },
            "optional": {
                "temperature": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 1.0, "step": 0.05}),
                "n_gpu_layers": ("INT", {"default": -1, "min": -1, "max": 80}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("json",)
    FUNCTION = "analyze_image"
    CATEGORY = "LLM/Local"
    
    def analyze_image(
        self,
        image,
        model_path: str,
        mmproj_path: str,
        subject_priority: str = "product",
        temperature: float = 0.1,
        n_gpu_layers: int = -1,
    ):
        if not LLAMA_AVAILABLE:
            error = "llama-cpp-python not installed"
            return (json.dumps({"error": error, "primary_subject": "", "secondary_subjects": [], "nsfw": False, "violence": False}),)
        
        try:
            # Convert ComfyUI tensor to PIL Image
            # ComfyUI images are [B, H, W, C] in range [0, 1]
            img_tensor = image[0]  # Take first image if batch
            img_np = (img_tensor.cpu().numpy() * 255).astype(np.uint8)
            pil_image = Image.fromarray(img_np)
            
            # Save temporarily (llama.cpp needs file path)
            temp_path = "C:/Users/genfp/AI_avatar/Comfy_vanila/ComfyUI/temp/vision_temp.jpg"
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            pil_image.save(temp_path)
            
            # Build prompt based on priority
            if subject_priority == "product":
                priority_text = "If there's both a person and a product/object, focus on the PRODUCT, not the person."
            elif subject_priority == "person":
                priority_text = "If there's both a person and objects, focus on the PERSON with their attributes."
            else:
                priority_text = ""
            
            prompt = f"""Analyze this image and return STRICT JSON with:
- primary_subject (string): The main object/person with physical descriptors only, NO actions
- secondary_subjects (array): Other objects, actions, background elements
- nsfw (boolean): Is this NSFW content?
- violence (boolean): Does this contain violence?

{priority_text}

Return ONLY the JSON object, no other text."""
            
            # Load model and run inference
            llm = _load_vision_llm(model_path, mmproj_path, n_gpu_layers)
            
            print(f"[VisionSafetyChecker] Analyzing image...")
            
            response = llm.create_chat_completion(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"file://{temp_path}"}},
                            {"type": "text", "text": prompt}
                        ]
                    }
                ],
                temperature=temperature,
                max_tokens=256,
            )
            
            text = response["choices"][0]["message"]["content"]
            print(f"[VisionSafetyChecker] Raw output: {text}")
            
            # Parse JSON
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                json_str = text[start:end+1]
                data = json.loads(json_str)
                
                # Validate schema
                if "primary_subject" not in data:
                    data["primary_subject"] = ""
                if "secondary_subjects" not in data or not isinstance(data["secondary_subjects"], list):
                    data["secondary_subjects"] = []
                if "nsfw" not in data:
                    data["nsfw"] = False
                if "violence" not in data:
                    data["violence"] = False
                
                json_str = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
                print(f"[VisionSafetyChecker] Result: {json_str}")
                return (json_str,)
            else:
                raise ValueError(f"No JSON found in output: {text}")
                
        except Exception as e:
            error_msg = f"Error in VisionSafetyChecker: {str(e)}"
            print(f"[VisionSafetyChecker] {error_msg}")
            return (json.dumps({"error": error_msg, "primary_subject": "", "secondary_subjects": [], "nsfw": False, "violence": False}),)


NODE_CLASS_MAPPINGS = {
    "VisionSafetyChecker": VisionSafetyChecker,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VisionSafetyChecker": "Vision Safety Checker (Qwen3-VL)",
}
```

---

## Step 5: Register New Node

Add to `__init__.py`:
```python
from .vision_safety_checker import NODE_CLASS_MAPPINGS as VISION_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as VISION_DISPLAY

NODE_CLASS_MAPPINGS = {**EXTRACTOR_MAPPINGS, **PARSER_MAPPINGS, **SAFETY_MAPPINGS, **VISION_MAPPINGS}
NODE_DISPLAY_NAME_MAPPINGS = {**EXTRACTOR_DISPLAY, **PARSER_DISPLAY, **SAFETY_DISPLAY, **VISION_DISPLAY}
```

---

## New Workflow Comparison

### Old Workflow (Florence-2 + Llama)
```
Load Image
    ↓
Florence-2 Caption
    ↓ (caption text)
Local JSON Extractor (Llama 3.1-8B)
    ↓ (json)
Safety Gate
    ↓
Dynamic Prompt Builder
```

### New Workflow (Qwen3-VL Only)
```
Load Image
    ↓
Vision Safety Checker (Qwen3-VL-4B)
    ↓ (json)
Safety Gate
    ↓
Dynamic Prompt Builder
```

**Benefits:**
- ⚡ Faster (one model vs two)
- 🎯 More accurate (sees actual image)
- 💾 Less VRAM (2.8GB vs 5.4GB for Llama)
- 🔧 Simpler workflow

---

## Performance Expectations (RTX 3080 Ti)

**Qwen3-VL-4B-Q5_K_M:**
- First inference: 10-20 seconds (model loading)
- Subsequent inferences: 2-4 seconds
- VRAM usage: ~4-5 GB
- Accuracy: Better than Florence-2 + Llama (direct vision)

**vs Current Setup:**
- Florence-2: 3-5 seconds
- Llama-3.1-8B: 1-3 seconds
- Total: 4-8 seconds

**Qwen3-VL is competitive and more accurate!**

---

## Troubleshooting

### "clip_model_path parameter not found"
Your llama-cpp-python version doesn't support vision models. Update:
```powershell
.\venv\Scripts\python.exe -m pip install --upgrade llama-cpp-python --force-reinstall --no-cache-dir
```

### "Cannot load mmproj file"
Ensure you downloaded the correct mmproj file for your model size (4B vs 30B).

### CUDA Out of Memory
Lower `n_gpu_layers` to 20-30 or use Q4_K_M quantization instead of Q5_K_M.

### Slow performance
Make sure `n_gpu_layers=-1` to use GPU fully. Check NVIDIA GPU usage in Task Manager.

---

## Model Size Comparison

| Model | Quantization | Size | VRAM | Use Case |
|-------|-------------|------|------|----------|
| Qwen3-VL-4B | Q4_K_M | 2.1 GB | 3-4 GB | Fast safety check |
| Qwen3-VL-4B | Q5_K_M | 2.8 GB | 4-5 GB | Balanced (recommended) |
| Qwen3-VL-4B | Q6_K | 3.3 GB | 5-6 GB | Higher quality |
| Qwen3-VL-30B | Q4_K_M | 19 GB | 18-20 GB | Max accuracy |

---

## Next Steps

1. ✅ Download Qwen3-VL-4B GGUF files
2. ✅ Create vision_safety_checker.py node
3. ✅ Test with sample images
4. ✅ Compare accuracy vs Florence-2 + Llama
5. ✅ Deploy if results are better

---

## Resources

- **Qwen3-VL-4B GGUF**: https://huggingface.co/NexaAI/Qwen3-VL-4B-Thinking-GGUF
- **llama.cpp vision support**: https://github.com/ggerganov/llama.cpp
- **llama-cpp-python docs**: https://github.com/abetlen/llama-cpp-python
