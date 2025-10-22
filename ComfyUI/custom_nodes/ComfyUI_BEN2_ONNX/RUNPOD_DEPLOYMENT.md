# BiRefNet_HR RunPod Serverless Deployment Guide

## Overview
This guide explains how to deploy BiRefNet_HR models for RunPod serverless, with models stored in the project directory instead of HuggingFace cache.

## Why This Approach?
✅ **Faster cold starts** - No model download on first run  
✅ **Predictable paths** - Models in `ComfyUI/models/birefnet_hr/`  
✅ **Offline capable** - No network dependency after build  
✅ **Version control** - You control exact model versions  

---

## Setup Instructions

### 1. Download Models Locally

Run the download script to fetch models to the correct directory:

```bash
cd ComfyUI/custom_nodes/ComfyUI_BEN2_ONNX
python download_birefnet_models.py
```

This will download models to:
```
ComfyUI/models/birefnet_hr/
├── BiRefNet_HR/
│   ├── config.json
│   ├── model.safetensors
│   └── ...
└── BiRefNet_HR-matting/
    ├── config.json
    ├── model.safetensors
    └── ...
```

### 2. Verify Model Files

```bash
ls -la ComfyUI/models/birefnet_hr/
```

Expected size: ~1.5-2GB per model

---

## Docker Deployment

### Dockerfile Example

```dockerfile
FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel

# Install dependencies
RUN pip install transformers pillow torchvision

# Copy ComfyUI
COPY ComfyUI /ComfyUI
WORKDIR /ComfyUI

# Ensure models are included
COPY ComfyUI/models/birefnet_hr /ComfyUI/models/birefnet_hr

# Verify models exist
RUN ls -la /ComfyUI/models/birefnet_hr/

CMD ["python", "main.py", "--listen", "0.0.0.0"]
```

### Build & Push

```bash
# Build
docker build -t your-registry/comfyui-birefnet:latest .

# Push
docker push your-registry/comfyui-birefnet:latest
```

---

## RunPod Configuration

### Environment Variables
```bash
MODEL_PATH=/ComfyUI/models/birefnet_hr
TRANSFORMERS_OFFLINE=1  # Optional: Force offline mode
```

### Volume Mounting (Alternative)
If you prefer volume mounting instead of baking into image:
```bash
/runpod-volume/models/birefnet_hr -> /ComfyUI/models/birefnet_hr
```

---

## How It Works

### Modified Loading Logic

The `birefnet_hr_node.py` now:

1. **Checks local first**: `ComfyUI/models/birefnet_hr/{model_variant}/`
2. **Falls back to download**: If not found (with warning)
3. **Uses `local_files_only=True`**: When loading from disk

### Path Resolution

```python
birefnet_hr_dir = os.path.join(folder_paths.models_dir, "birefnet_hr")
model_path = os.path.join(birefnet_hr_dir, model_variant)
```

---

## Testing

### Local Test
```bash
cd ComfyUI
python main.py
```

Load your workflow `BG_remove_BiRefNet_pro_2nd.json` - should see:
```
Loading BiRefNet_HR model from: C:\...\ComfyUI\models\birefnet_hr\BiRefNet_HR
BiRefNet_HR loaded in FP16 mode
```

### Offline Test
Disable network and verify it still works:
```bash
# Disconnect network
python main.py
```

Should work without any download attempts.

---

## Troubleshooting

### Models Not Found
```
RuntimeError: Failed to load BiRefNet_HR model from ...
```

**Solution**: Run `python download_birefnet_models.py`

### Wrong Directory
Check `folder_paths.models_dir`:
```python
import folder_paths
print(folder_paths.models_dir)
```

### Large Docker Image
Models add ~2-3GB. Consider:
- Multi-stage builds
- Model compression
- Shared volume for models

---

## Comparison: Old vs New

| Aspect | Old (HF Cache) | New (Project Dir) |
|--------|----------------|-------------------|
| **Location** | `~/.cache/huggingface/` | `ComfyUI/models/birefnet_hr/` |
| **Cold Start** | Downloads on first run | Instant (pre-loaded) |
| **Docker Size** | Smaller base, downloads runtime | Larger base, no runtime download |
| **Offline** | ❌ Needs internet first time | ✅ Works offline |
| **RunPod** | ❌ Downloads per instance | ✅ Pre-baked |

---

## Manual Download (Alternative Method)

If script fails, download manually:

```bash
# Using HuggingFace CLI
huggingface-cli download ZhengPeng7/BiRefNet_HR \
  --local-dir ComfyUI/models/birefnet_hr/BiRefNet_HR

huggingface-cli download ZhengPeng7/BiRefNet_HR-matting \
  --local-dir ComfyUI/models/birefnet_hr/BiRefNet_HR-matting
```

Or using Python:
```python
from transformers import AutoModelForImageSegmentation

model = AutoModelForImageSegmentation.from_pretrained(
    "ZhengPeng7/BiRefNet_HR",
    trust_remote_code=True
)
model.save_pretrained("ComfyUI/models/birefnet_hr/BiRefNet_HR")
```

---

## Questions?

- Check model size: Each model ~1.5-2GB
- Verify paths: Use absolute paths in Docker
- Test locally first: Before pushing to RunPod
