# Local JSON Extractor (llama.cpp) for ComfyUI

A custom node that runs local LLM inference using llama.cpp to extract structured JSON from image captions.

## Features

- **In-process inference** - No HTTP server required
- **GPU accelerated** - Uses CUDA for fast inference on NVIDIA GPUs
- **Strict JSON output** - Returns structured data: `primary_subject`, `secondary_subjects`, `nsfw`, `violence`
- **Model caching** - Loads model once per session for efficiency
- **Error handling** - Graceful fallbacks and clear error messages

## Installation

### 1. Install llama-cpp-python with CUDA support

The node requires `llama-cpp-python` with CUDA support. It's already installed in your venv:

```powershell
# From ComfyUI root directory:
.\venv\Scripts\python.exe -m pip install llama-cpp-python --prefer-binary --extra-index-url https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu122
```

### 2. Download a GGUF model

You need a GGUF-format LLM model. Recommended options:

**Option A: Llama 3.1 8B (Recommended)**
- Model: `Llama-3.1-8B-Instruct-Q5_K_M.gguf` (~5.4 GB)
- Download from: https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF
- Place at: `C:\Users\genfp\AI_avatar\Comfy_vanila\ComfyUI\models\llm\Llama-3.1-8B-Instruct-Q5_K_M.gguf`

**Option B: Smaller models (if VRAM is tight)**
- `Llama-3.2-3B-Instruct-Q5_K_M.gguf` (~2.3 GB)
- `Qwen2-7B-Instruct-Q5_K_M.gguf` (~5.1 GB)

**Download instructions:**
```powershell
# Create models/llm directory if it doesn't exist
New-Item -ItemType Directory -Force -Path "C:\Users\genfp\AI_avatar\Comfy_vanila\ComfyUI\models\llm"

# Download using your preferred method:
# - Web browser from HuggingFace
# - wget/curl
# - huggingface-cli
```

## Usage

1. **Restart ComfyUI** to load the node
2. Add **"Local JSON Extractor (llama.cpp)"** node to your workflow
3. Connect a caption string (e.g., from Florence-2) to the `caption` input
4. Set `model_path` to your GGUF file location
5. Adjust parameters:
   - `temperature`: 0.1 (low for deterministic output)
   - `max_new_tokens`: 192 (usually enough for JSON)
   - `n_gpu_layers`: -1 (auto-offload to GPU, or set lower if VRAM limited)
   - `n_ctx`: 4096 (context window size)

## Parameters

- **caption** (required): Input text to analyze
- **model_path** (required): Path to your GGUF model file
- **temperature**: Sampling temperature (0.0-1.0, default 0.1)
- **max_new_tokens**: Maximum tokens to generate (32-1024, default 192)
- **n_ctx**: Context window size (1024-8192, default 4096)
- **n_gpu_layers**: GPU layers to offload (-1 = all, default -1)
- **seed**: Random seed for reproducibility (default 0)

## Output Format

The node returns a JSON string with this structure:

```json
{
  "primary_subject": "person with blue hair",
  "secondary_subjects": ["cityscape", "sunset"],
  "nsfw": false,
  "violence": false
}
```

## Performance Tips (RTX 3080 Ti)

- Set `n_gpu_layers=-1` for maximum speed (if VRAM allows)
- Use Q5_K_M quantization for best quality/size balance
- If you get CUDA OOM errors:
  - Lower `n_gpu_layers` to 20-40
  - Try Q4_K_M quantization instead
  - Reduce `n_ctx` to 2048

## Troubleshooting

### "llama-cpp-python not installed"
- Run the pip install command above in your ComfyUI venv

### "GGUF not found"
- Verify the model_path points to an existing .gguf file
- Use forward slashes: `C:/path/to/model.gguf`

### "Model did not return JSON"
- Try lowering temperature to 0.0-0.1
- Some models work better than others for structured output
- Llama 3.1 Instruct is highly recommended

### Slow inference (CPU only)
- Verify CUDA-enabled wheel is installed: `pip show llama-cpp-python`
- Should show version with `+cu122` suffix
- Check n_gpu_layers is set to -1 or a positive number

## License

MIT License - See node source code for details
