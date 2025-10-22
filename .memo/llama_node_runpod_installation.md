# ComfyUI Local LLM Node - Runpod Installation Guide

Guide for deploying the Local JSON Extractor (llama.cpp) custom node on Runpod.

---

## Prerequisites

- Runpod account with GPU pod (RTX 3090/4090 or A40/A100 recommended)
- ComfyUI already running on Runpod
- Network volume (optional but recommended for model storage)

---

## Installation Steps

### 1. Deploy Custom Node Files

Copy the custom node to your Runpod instance:

```bash
# SSH into your Runpod pod or use the web terminal
cd /workspace/ComfyUI/custom_nodes

# Create the node directory
mkdir -p ComfyUI_LocalJSONExtractor

# Create the files (or copy from your local setup)
cd ComfyUI_LocalJSONExtractor
```

Upload these files to the directory:
- `__init__.py`
- `node_llama_json_extractor.py`
- `requirements.txt`
- `README.md` (optional)

**Or** use git if you've put it in a repository:
```bash
cd /workspace/ComfyUI/custom_nodes
git clone <your-repo-url> ComfyUI_LocalJSONExtractor
```

---

### 2. Install llama-cpp-python with CUDA

Detect your CUDA version:
```bash
nvcc --version
# or
nvidia-smi
```

Install based on CUDA version:

**For CUDA 12.1/12.2:**
```bash
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
```

**For CUDA 11.8:**
```bash
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu118
```

**Verify installation:**
```bash
python -c "from llama_cpp import Llama; print('Import successful')"
```

---

### 3. Download GGUF Model

**Option A: Network Volume (Recommended)**

```bash
# Create directory on network volume
mkdir -p /runpod-volume/models/llm

# Download model using wget
cd /runpod-volume/models/llm
wget https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf

# Verify download
ls -lh *.gguf
```

**Option B: Local Pod Storage (Faster but ephemeral)**

```bash
# Create directory on local storage
mkdir -p /workspace/ComfyUI/models/llm

# Download model
cd /workspace/ComfyUI/models/llm
wget https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf
```

**Using huggingface-cli (alternative):**
```bash
pip install huggingface-hub
huggingface-cli download bartowski/Meta-Llama-3.1-8B-Instruct-GGUF \
  Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf \
  --local-dir /runpod-volume/models/llm
```

---

### 4. Update Node Configuration

Edit the node file to set default path for Runpod:

```bash
nano /workspace/ComfyUI/custom_nodes/ComfyUI_LocalJSONExtractor/node_llama_json_extractor.py
```

Find line ~129 and change default_model_path:

```python
# For Network Volume:
default_model_path = "/runpod-volume/models/llm/Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf"

# For Local Storage:
default_model_path = "/workspace/ComfyUI/models/llm/Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf"
```

---

### 5. Restart ComfyUI

```bash
# Find ComfyUI process
ps aux | grep python | grep main.py

# Kill it
kill <PID>

# Or use pkill
pkill -f "python.*main.py"

# Restart ComfyUI (adjust based on your startup method)
cd /workspace/ComfyUI
python main.py --listen 0.0.0.0 --port 8188
```

---

## Docker Image Setup (Advanced)

For faster cold starts, bake the model into your Docker image.

### Dockerfile Example

```dockerfile
FROM runpod/pytorch:2.1.0-py3.10-cuda12.1.0-devel

# Install ComfyUI and dependencies
WORKDIR /workspace
RUN git clone https://github.com/comfyanonymous/ComfyUI.git
WORKDIR /workspace/ComfyUI
RUN pip install -r requirements.txt

# Install llama-cpp-python with CUDA
RUN pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121

# Copy custom node
COPY ComfyUI_LocalJSONExtractor /workspace/ComfyUI/custom_nodes/ComfyUI_LocalJSONExtractor

# Download and bake GGUF model into image
RUN mkdir -p /workspace/ComfyUI/models/llm
RUN wget -O /workspace/ComfyUI/models/llm/Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf \
    https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf

# Expose port
EXPOSE 8188

# Start ComfyUI
CMD ["python", "main.py", "--listen", "0.0.0.0", "--port", "8188"]
```

Build and push:
```bash
docker build -t <your-dockerhub-username>/comfyui-llm:latest .
docker push <your-dockerhub-username>/comfyui-llm:latest
```

Use this image in your Runpod template.

---

## Testing on Runpod

1. Open ComfyUI web interface
2. Add **"Local JSON Extractor (llama.cpp)"** node
3. Set parameters:
   - `model_path`: Path to your GGUF file
   - `n_gpu_layers`: `-1` (auto-offload all layers)
   - `temperature`: `0.1`
4. Connect caption input (e.g., from Florence-2)
5. Run workflow

**Expected Performance:**
- First run: 15-30 seconds (model loading + inference)
- Subsequent runs: 1-3 seconds (cached model)
- VRAM usage: ~6-8 GB for Q5_K_M 8B model

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'llama_cpp'"
```bash
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
```

### "GGUF not found at: /path/to/model.gguf"
- Verify file exists: `ls -lh /path/to/model.gguf`
- Check permissions: `chmod 644 /path/to/model.gguf`
- Update model_path in node settings

### CUDA Out of Memory
- Lower `n_gpu_layers` to 30-40
- Use smaller quantization: Q4_K_M instead of Q5_K_M
- Reduce `n_ctx` to 2048

### Slow Inference (CPU fallback)
```bash
# Verify CUDA is enabled
python -c "from llama_cpp import Llama; import llama_cpp; print(llama_cpp.__version__)"

# Check for ggml-cuda library
find /usr/local/lib/python*/site-packages/llama_cpp -name "*cuda*"
```

### Model Loads Every Time (Not Cached)
- This is normal for serverless/ephemeral pods
- Use persistent pod or network volume
- Model cache persists within a single ComfyUI session

---

## Startup Script for Runpod

Create `/workspace/startup.sh`:

```bash
#!/bin/bash

# Update system
apt-get update

# Install dependencies if needed
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121

# Download model if not exists
if [ ! -f "/runpod-volume/models/llm/Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf" ]; then
    echo "Downloading GGUF model..."
    mkdir -p /runpod-volume/models/llm
    wget -O /runpod-volume/models/llm/Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf \
        https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf
fi

# Start ComfyUI
cd /workspace/ComfyUI
python main.py --listen 0.0.0.0 --port 8188
```

Make executable:
```bash
chmod +x /workspace/startup.sh
```

Add to Runpod template environment or run manually.

---

## Cost Optimization Tips

1. **Use Network Volume** - Store model once, reuse across pods
2. **Batch Requests** - Process multiple captions in one session
3. **Model Caching** - Keep pod running during active use
4. **Smaller Models** - Use Q4_K_M or 3B models for simpler tasks
5. **Spot Instances** - Use if you can tolerate interruptions

---

## Model Recommendations by GPU

| GPU | Recommended Model | Quantization | VRAM Usage |
|-----|------------------|--------------|------------|
| RTX 3090/4090 (24GB) | Llama-3.1-8B | Q5_K_M | 6-8 GB |
| RTX 3080 (10GB) | Llama-3.2-3B | Q5_K_M | 3-4 GB |
| A40/A100 (40-80GB) | Llama-3.1-70B | Q4_K_M | 35-40 GB |
| T4 (16GB) | Llama-3.2-3B | Q4_K_M | 2-3 GB |

---

## Additional Resources

- **llama.cpp GitHub**: https://github.com/ggerganov/llama.cpp
- **llama-cpp-python**: https://github.com/abetlen/llama-cpp-python
- **GGUF Models**: https://huggingface.co/models?library=gguf
- **Runpod Docs**: https://docs.runpod.io/

---

## License

- Custom node: MIT License
- llama.cpp: MIT License
- Model licenses vary (check model card on HuggingFace)
