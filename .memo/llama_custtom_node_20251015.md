— here’s a **drop-in guide** you can paste into Windsurf and follow to get a *single-worker, fully local* ComfyUI LLM step on your Windows box (RTX 3080 Ti), with **no Ollama, no AGPL**. It uses **llama.cpp (via llama-cpp-python)** inside a **custom Comfy node** to turn a Florence-2 caption into strict JSON: `{primary_subject, secondary_subjects[], nsfw, violence}`.

---

# ComfyUI Local LLM (llama.cpp) Node — Windows (RTX 3080 Ti) Setup

## 0) What you’ll build

A tiny **custom node** that:

* loads a **GGUF** model (e.g., *Llama-3.1-8B-Instruct-Q5_K_M*),
* **runs in-process** (no HTTP daemon),
* takes a caption string (from Florence-2 or any source),
* returns **strict JSON** with `primary_subject`, `secondary_subjects[]`, `nsfw`, `violence`.

Everything is permissively licensed (MIT/Apache-2.0 stacks).

---

## 1) Prerequisites (Windows 10/11, NVIDIA 3080 Ti)

1. **Python 3.11 (64-bit)**

   * Avoid 3.12+ for now to keep binary wheels simple.
   * Verify: `python --version`

2. **CUDA runtime**

   * 3080 Ti = CUDA 12.x. The easiest path is to use a **prebuilt CUDA wheel** for llama-cpp-python:

     * `llama-cpp-python-cu121` (CUDA 12.1) or
     * `llama-cpp-python-cu122` (CUDA 12.2)
   * If you don’t know your CUDA minor version, pick `cu121` first (works broadly).
   * Verify: `nvcc --version` * I think we are using CUDA 12.4, please check


3. **ComfyUI (local)**

   * Typical folder: `C:\Users\<you>\ComfyUI`
   * Start once to generate folders; quit.

4. **Model file (GGUF)**

   * Recommended: `Llama-3.1-8B-Instruct-Q5_K_M.gguf` (~5–6 GB).
   * Place under e.g. `C:\LLM\models\Llama-3.1-8B-Instruct-Q5_K_M.gguf`

5. **(Optional) Florence-2** for captions

   * Any caption source works; this node just needs a **string**.

---

## 2) Install llama-cpp-python (GPU build)

From an **Admin PowerShell** (or your venv):

```powershell
# In your ComfyUI venv if you use one:
# C:\Users\<you>\ComfyUI\python_embeded\python.exe -m pip install ...

pip install --upgrade pip

# Choose one CUDA wheel (try cu121 first). If it fails, try cu122. maybe cu124
pip install llama-cpp-python-cu124 --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124

# or:
# pip install llama-cpp-python-cu122 --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu122
```

> If you hit wheel errors, you can fall back to CPU-only: `pip install llama-cpp-python` (works, just slower).
> You do **not** need Visual Studio build tools when using prebuilt wheels above.

---

## 3) Create the custom node

Create a new file:

```
<ComfyUI root>\custom_nodes\ComfyUI_LocalJSONExtractor\node_llama_json_extractor.py
```

Put this code in it:

```python
# node_llama_json_extractor.py
# MIT License — feel free to keep or adapt
import json
import os
from typing import Dict, Any

# llama.cpp Python bindings
from llama_cpp import Llama

# ---- Simple global cache so model loads once per process
_LLAMA_CACHE: Dict[str, Llama] = {}

def _load_llm(model_path: str, n_ctx: int = 4096, n_gpu_layers: int = -1, seed: int = 0) -> Llama:
    """
    Load (or reuse) a GGUF model. n_gpu_layers=-1 tries to offload maximum layers to GPU.
    If you want to cap VRAM, set e.g. n_gpu_layers=20.
    """
    key = f"{model_path}|ctx={n_ctx}|gpu={n_gpu_layers}"
    if key in _LLAMA_CACHE:
        return _LLAMA_CACHE[key]

    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"GGUF not found at: {model_path}")

    llm = Llama(
        model_path=model_path,
        n_ctx=n_ctx,
        n_gpu_layers=n_gpu_layers,   # GPU offload (requires CUDA wheel)
        seed=seed,
        logits_all=False,
        vocab_only=False,
        use_mlock=False,
        embedding=False,
        # you can also set n_threads here if you want to tune CPU threads
    )
    _LLAMA_CACHE[key] = llm
    return llm


def _build_prompt(caption: str) -> str:
    # Compact system+user instruction for strict JSON
    system = (
        "You extract structured facts from a short image caption. "
        "Return STRICT JSON with keys:\n"
        "  primary_subject (string),\n"
        "  secondary_subjects (array of strings),\n"
        "  nsfw (boolean),\n"
        "  violence (boolean).\n"
        "No extra text. No markdown. No code fences."
    )
    user = f'Caption: """{caption}"""'
    # Simple chat template for llama.cpp's chat API
    return f"<<SYS>>{system}<</SYS>>\n[USER]{user}\n[ASSISTANT]"


def _coerce_json(txt: str) -> str:
    """
    Try to locate and validate a JSON object in the model output.
    If it fails, raise a ValueError so Comfy shows a clear error.
    """
    # Heuristic: find first '{' and last '}' and parse
    start = txt.find("{")
    end = txt.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"Model did not return JSON. Output was:\n{txt}")

    candidate = txt[start : end + 1]
    data = json.loads(candidate)

    # Minimal schema checks
    if "primary_subject" not in data: data["primary_subject"] = ""
    if "secondary_subjects" not in data or not isinstance(data["secondary_subjects"], list):
        data["secondary_subjects"] = []
    if "nsfw" not in data: data["nsfw"] = False
    if "violence" not in data: data["violence"] = False

    # Re-dump to normalized JSON (no spaces to minimize string size)
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


# ---------------- ComfyUI Node Definition ---------------- #

class LocalJSONExtractorLlama:
    """
    ComfyUI node: takes a caption string, returns STRICT JSON string.
    Runs llama.cpp in-process; no HTTP server required.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "caption": ("STRING", {"multiline": True, "default": ""}),
                "model_path": ("STRING", {"default": "C:/LLM/models/Llama-3.1-8B-Instruct-Q5_K_M.gguf"}),
            },
            "optional": {
                "temperature": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 1.0, "step": 0.05}),
                "max_new_tokens": ("INT", {"default": 192, "min": 32, "max": 1024, "step": 16}),
                "n_ctx": ("INT", {"default": 4096, "min": 1024, "max": 8192, "step": 256}),
                "n_gpu_layers": ("INT", {"default": -1, "min": -1, "max": 80, "step": 1}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 2**31 - 1}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("json",)
    FUNCTION = "run"
    CATEGORY = "LLM/Local"

    def run(
        self,
        caption: str,
        model_path: str,
        temperature: float = 0.1,
        max_new_tokens: int = 192,
        n_ctx: int = 4096,
        n_gpu_layers: int = -1,
        seed: int = 0,
    ):
        if not caption or not caption.strip():
            return ('{"primary_subject":"","secondary_subjects":[],"nsfw":false,"violence":false}',)

        llm = _load_llm(model_path=model_path, n_ctx=n_ctx, n_gpu_layers=n_gpu_layers, seed=seed)
        prompt = _build_prompt(caption)

        # llama.cpp chat completion
        out = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": "You are a strict JSON extraction engine."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_new_tokens,
            stop=None,  # you can add ']\n' or similar stops if desired
        )

        # Extract text
        text = out["choices"][0]["message"]["content"]
        json_str = _coerce_json(text)
        return (json_str,)


# ComfyUI entrypoint
NODE_CLASS_MAPPINGS = {
    "LocalJSONExtractorLlama": LocalJSONExtractorLlama,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LocalJSONExtractorLlama": "Local JSON Extractor (llama.cpp)",
}
```

> Paths are Windows-style in the default; change `model_path` to your GGUF location if different.

---

## 4) Restart ComfyUI & wire the graph

1. **Restart** ComfyUI so it discovers the node.
2. In your workflow:

   * **Florence-2 (or your caption node)** → output `caption` (STRING)
   * Add **Local JSON Extractor (llama.cpp)** node:

     * `caption`: connect from Florence-2
     * `model_path`: `C:/LLM/models/Llama-3.1-8B-Instruct-Q5_K_M.gguf`
     * `temperature`: `0.1`
     * `max_new_tokens`: `192`
     * `n_gpu_layers`: `-1` (auto offload) or set a cap (e.g., `20`) if VRAM is tight
   * The node returns a **STRING** containing strict JSON.
   * (Optional) Pipe that into a small Python node that parses/saves JSON, or just write it to a text/file node.

---

## 5) Performance tips (3080 Ti)

* **n_gpu_layers**

  * `-1` tries to offload as many layers as possible → fastest if VRAM allows.
  * If you hit OOM, try `n_gpu_layers=20` (or lower) — still quite fast for short outputs.
* **Quantization**

  * Q5_K_M is a great balance; if you need smaller, try **Q4_K_M** (accuracy drops slightly).
* **Low variance**

  * Use `temperature=0.0–0.2`, no top-p (defaults are fine). You want deterministic JSON.
* **JSON coercion**

  * The node already validates/coerces to a strict JSON object. If the output ever fails, it throws a readable error in the UI.

---

## 6) Optional: add a tiny **local text-safety** head

If you want a second opinion beyond the LLM booleans:

* Convert a small NSFW/violence text classifier to **ONNX** and run it with **onnxruntime** in another custom node.
* AND/OR its flags with the LLM’s `nsfw/violence` before accepting.

(You can add this later; for most product captions the LLM flags with temperature 0.1 are stable.)

---

## 7) Troubleshooting

* **ImportError: llama_cpp not found**

  * Ensure you installed `llama-cpp-python-cu124` into the **same** Python environment ComfyUI uses.
* **CUDA wheel fails to install**

  * Try the other wheel (`cu122`). As a fallback: `pip install llama-cpp-python` (CPU-only).
* **CUDA OOM**

  * Lower `n_gpu_layers`, or try a smaller quant (Q4), or reduce `n_ctx` to 2048.
* **Wrong model path**

  * The node won’t auto-download GGUFs; make sure the `model_path` points to an existing file.

---

## 8) Going to Runpod later (still single worker)

* Use the **same node**.
* Put the GGUF on your **Network Volume** (e.g., `/workspace/vol/models/...gguf`) and set `model_path` accordingly.
* If the serverless image is ephemeral, **bake the GGUF into the image** to avoid slow cold-starts.

---

## 9) License notes

* **llama.cpp / llama-cpp-python**: MIT
* **Transformers/ONNX Runtime** (if you add them): Apache-2.0 / MIT
* Your custom node: you can license MIT (header is included above)

---

### That’s it

This keeps your whole pipeline **local, fast, single-worker**, and **AGPL-free**:

```
Florence-2 (caption) → Local JSON Extractor (llama.cpp) → strict JSON
```

If you want, I can also supply a **minimal ComfyUI workflow JSON** that wires a dummy “Caption (STRING)” input → this node → “Save Text”.
