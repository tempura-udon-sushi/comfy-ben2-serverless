# BEN2 Serverless - Model Download URLs

Quick reference for all model download URLs used in the Docker build.

## 📦 Models Required

### 1. BEN2_Base.onnx
- **Size**: ~223 MB
- **License**: Apache 2.0
- **Purpose**: Background removal
- **URL**: 
  ```
  https://huggingface.co/PramaLLC/BEN2/resolve/main/BEN2_Base.onnx
  ```
- **Destination**: `/comfyui/models/ben2_onnx/BEN2_Base.onnx`
- **Download command**:
  ```bash
  wget -O BEN2_Base.onnx "https://huggingface.co/PramaLLC/BEN2/resolve/main/BEN2_Base.onnx"
  ```

### 2. Llama-3.1-8B-Instruct (GGUF)
- **Size**: ~5.4 GB
- **License**: Meta Llama 3.1 Community License
- **Purpose**: JSON extraction, safety classification
- **Repository**: https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF
- **File**: `Llama-3.1-8B-Instruct-Q5_K_M.gguf`
- **URL**:
  ```
  https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Llama-3.1-8B-Instruct-Q5_K_M.gguf
  ```
- **Destination**: `/comfyui/models/llm/Llama-3.1-8B-Instruct-Q5_K_M.gguf`
- **Download command**:
  ```bash
  wget -O Llama-3.1-8B-Instruct-Q5_K_M.gguf "https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Llama-3.1-8B-Instruct-Q5_K_M.gguf"
  ```

### 3. Florence-2-base
- **Size**: ~230 MB (model files)
- **License**: MIT
- **Purpose**: Image captioning, vision tasks
- **Repository**: https://huggingface.co/microsoft/Florence-2-base
- **Method**: Auto-download via transformers
- **Cache location**: `/comfyui/models/LLM/models--microsoft--Florence-2-base/`
- **Pre-download script**:
  ```python
  from transformers import AutoModelForCausalLM, AutoProcessor
  
  model = AutoModelForCausalLM.from_pretrained(
      'microsoft/Florence-2-base',
      trust_remote_code=True,
      cache_dir='/comfyui/models/LLM'
  )
  
  processor = AutoProcessor.from_pretrained(
      'microsoft/Florence-2-base',
      trust_remote_code=True,
      cache_dir='/comfyui/models/LLM'
  )
  ```

### 4. NudeNet
- **Size**: ~100 MB
- **License**: MIT
- **Purpose**: NSFW content detection
- **Repository**: https://github.com/notAI-tech/NudeNet
- **Method**: Auto-download via nudenet package
- **Cache location**: `~/.NudeNet/` (auto-managed)
- **Pre-download script**:
  ```python
  from nudenet import NudeDetector
  detector = NudeDetector()
  # First initialization downloads the model
  ```

## 🔄 Alternative Model Versions

### Llama Alternatives (if VRAM limited)

**Smaller - Llama 3.2 3B**
- **Size**: ~2.3 GB
- **File**: `Llama-3.2-3B-Instruct-Q5_K_M.gguf`
- **URL**:
  ```
  https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q5_K_M.gguf
  ```

**Larger - Llama 3.1 8B Q8**
- **Size**: ~7.7 GB
- **File**: `Llama-3.1-8B-Instruct-Q8_0.gguf`
- **URL**:
  ```
  https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Llama-3.1-8B-Instruct-Q8_0.gguf
  ```

### Florence-2 Alternatives

**Fine-tuned for prompts**
- **Repository**: `MiaoshouAI/Florence-2-base-PromptGen-v2.0`
- **Size**: Similar to base (~230 MB)
- **Better for**: Generating detailed prompts

**Large variant**
- **Repository**: `microsoft/Florence-2-large`
- **Size**: ~770 MB
- **Better for**: More accurate captioning

## 📊 Total Download Size

| Configuration | Total Size |
|---------------|------------|
| **Default (Recommended)** | ~6 GB |
| BEN2 + Florence + NudeNet + Llama 3.1 8B Q5 | 223MB + 230MB + 100MB + 5.4GB |
| **Lightweight** | ~3 GB |
| BEN2 + Florence + NudeNet + Llama 3.2 3B Q5 | 223MB + 230MB + 100MB + 2.3GB |
| **High Quality** | ~8.5 GB |
| BEN2 + Florence-Large + NudeNet + Llama 3.1 8B Q8 | 223MB + 770MB + 100MB + 7.7GB |

## 🔗 Repository Links

- **BEN2**: https://huggingface.co/PramaLLC/BEN2
- **Llama 3.1 GGUF**: https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF
- **Florence-2**: https://huggingface.co/microsoft/Florence-2-base
- **NudeNet**: https://github.com/notAI-tech/NudeNet

## 🛠️ Manual Download Script

If you want to download models manually before building:

```bash
#!/bin/bash
# download_models.sh

mkdir -p models/ben2_onnx
mkdir -p models/llm

echo "Downloading BEN2..."
wget -O models/ben2_onnx/BEN2_Base.onnx \
  "https://huggingface.co/PramaLLC/BEN2/resolve/main/BEN2_Base.onnx"

echo "Downloading Llama 3.1 8B..."
wget -O models/llm/Llama-3.1-8B-Instruct-Q5_K_M.gguf \
  "https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Llama-3.1-8B-Instruct-Q5_K_M.gguf"

echo "✅ Models downloaded!"
```

**PowerShell version:**
```powershell
# download_models.ps1

New-Item -ItemType Directory -Force -Path "models\ben2_onnx"
New-Item -ItemType Directory -Force -Path "models\llm"

Write-Host "Downloading BEN2..."
Invoke-WebRequest -Uri "https://huggingface.co/PramaLLC/BEN2/resolve/main/BEN2_Base.onnx" `
  -OutFile "models\ben2_onnx\BEN2_Base.onnx"

Write-Host "Downloading Llama 3.1 8B..."
Invoke-WebRequest -Uri "https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Llama-3.1-8B-Instruct-Q5_K_M.gguf" `
  -OutFile "models\llm\Llama-3.1-8B-Instruct-Q5_K_M.gguf"

Write-Host "✅ Models downloaded!"
```

## 🔍 Verify Downloads

After downloading, verify file sizes:

```bash
# Linux/Mac
ls -lh models/ben2_onnx/BEN2_Base.onnx           # Should be ~223 MB
ls -lh models/llm/Llama-3.1-8B-Instruct-Q5_K_M.gguf  # Should be ~5.4 GB

# Windows PowerShell
Get-Item models\ben2_onnx\BEN2_Base.onnx | Select-Object Length
Get-Item models\llm\Llama-3.1-8B-Instruct-Q5_K_M.gguf | Select-Object Length
```

## 📝 Notes

- All URLs are direct download links (no Git LFS required)
- Models are hosted on HuggingFace (reliable, free CDN)
- No authentication required for any model
- Downloads can be resumed if interrupted
- Consider using `wget -c` or `curl -C -` for resume capability

---

**Last Updated**: 2025-10-23  
**Verified**: All URLs working as of build date
