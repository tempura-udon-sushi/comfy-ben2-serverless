# node_llama_json_extractor.py
# MIT License — feel free to keep or adapt
import json
import os
from typing import Dict, Any

# llama.cpp Python bindings
try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False
    print("[LocalJSONExtractor] WARNING: llama-cpp-python not installed. Node will be disabled.")

# ---- Simple global cache so model loads once per process
_LLAMA_CACHE: Dict[str, Any] = {}

def _load_llm(model_path: str, n_ctx: int = 4096, n_gpu_layers: int = -1, seed: int = 0):
    """
    Load (or reuse) a GGUF model. n_gpu_layers=-1 tries to offload maximum layers to GPU.
    If you want to cap VRAM, set e.g. n_gpu_layers=20.
    """
    if not LLAMA_AVAILABLE:
        raise RuntimeError("llama-cpp-python is not installed. Please install it first.")
    
    key = f"{model_path}|ctx={n_ctx}|gpu={n_gpu_layers}"
    if key in _LLAMA_CACHE:
        return _LLAMA_CACHE[key]

    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"GGUF not found at: {model_path}")

    print(f"[LocalJSONExtractor] Loading GGUF model: {model_path}")
    print(f"[LocalJSONExtractor] Context size: {n_ctx}, GPU layers: {n_gpu_layers}")
    
    llm = Llama(
        model_path=model_path,
        n_ctx=n_ctx,
        n_gpu_layers=n_gpu_layers,   # GPU offload (requires CUDA wheel)
        seed=seed,
        logits_all=False,
        vocab_only=False,
        use_mlock=False,
        embedding=False,
        verbose=True,
        # you can also set n_threads here if you want to tune CPU threads
    )
    _LLAMA_CACHE[key] = llm
    print(f"[LocalJSONExtractor] Model loaded successfully and cached")
    return llm


def _build_prompt(caption: str, subject_priority: str = "auto") -> str:
    """
    Build a prompt for strict JSON extraction.
    Uses a simpler format that works better with various chat templates.
    
    Args:
        caption: The image caption to analyze
        subject_priority: "product" (prioritize objects over people), 
                         "person" (prioritize people), 
                         or "auto" (detect automatically)
    """
    
    # Adjust instructions based on priority
    if subject_priority == "product":
        priority_instruction = (
            "IMPORTANT: If the caption mentions both a person AND an object/product, "
            "the primary_subject MUST be the object/product being held, worn, or used, NOT the person. "
            "Example: 'A person holding a blue bowl' -> primary_subject is 'blue bowl', NOT 'person'.\n"
        )
    elif subject_priority == "person":
        priority_instruction = (
            "IMPORTANT: If the caption mentions both a person AND objects, "
            "the primary_subject MUST be the person with their descriptors. "
            "Example: 'A woman in a red dress holding flowers' -> primary_subject is 'woman in a red dress'.\n"
        )
    else:  # auto
        priority_instruction = ""
    
    system = (
        "You extract structured facts from a short image caption. "
        "Return STRICT JSON with keys:\n"
        f"{priority_instruction}"
        "  primary_subject (string) - the main object/person with ONLY its physical/material descriptors, NO actions or states (e.g., 'wooden sculpture of a bear', NOT 'bear carrying a bag'),\n"
        "  secondary_subjects (array of strings) - other objects, actions, background elements, or context (e.g., ['carrying a bag', 'woods']),\n"
        "  nsfw (boolean),\n"
        "  violence (boolean).\n"
        "No extra text. No markdown. No code fences."
    )
    user = f'Caption: """{caption}"""'
    return f"{system}\n\n{user}"


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

    # Minimal schema checks with defaults
    if "primary_subject" not in data: 
        data["primary_subject"] = ""
    if "secondary_subjects" not in data or not isinstance(data["secondary_subjects"], list):
        data["secondary_subjects"] = []
    if "nsfw" not in data: 
        data["nsfw"] = False
    if "violence" not in data: 
        data["violence"] = False

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
        # Default model path - user should change this to their actual GGUF location
        default_model_path = "C:/LLM/models/Llama-3.1-8B-Instruct-Q5_K_M.gguf"
        
        # Check if ComfyUI models directory exists and suggest it
        comfy_models_llm = "C:/Users/genfp/AI_avatar/Comfy_vanila/ComfyUI/models/llm"
        if os.path.exists(comfy_models_llm):
            # Look for any .gguf file in that directory
            try:
                gguf_files = [f for f in os.listdir(comfy_models_llm) if f.endswith('.gguf')]
                if gguf_files:
                    default_model_path = os.path.join(comfy_models_llm, gguf_files[0]).replace("\\", "/")
            except:
                pass
        
        return {
            "required": {
                "caption": ("STRING", {"multiline": True, "default": ""}),
                "model_path": ("STRING", {"default": default_model_path}),
                "subject_priority": (["auto", "product", "person"], {"default": "product"}),
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
        subject_priority: str = "product",
        temperature: float = 0.1,
        max_new_tokens: int = 192,
        n_ctx: int = 4096,
        n_gpu_layers: int = -1,
        seed: int = 0,
    ):
        if not LLAMA_AVAILABLE:
            error_msg = (
                "llama-cpp-python is not installed. "
                "Please install with: pip install llama-cpp-python-cu124 "
                "--extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124"
            )
            return (json.dumps({"error": error_msg, "primary_subject": "", "secondary_subjects": [], "nsfw": False, "violence": False}),)
        
        if not caption or not caption.strip():
            return ('{"primary_subject":"","secondary_subjects":[],"nsfw":false,"violence":false}',)

        try:
            llm = _load_llm(model_path=model_path, n_ctx=n_ctx, n_gpu_layers=n_gpu_layers, seed=seed)
            prompt = _build_prompt(caption, subject_priority)

            print(f"[LocalJSONExtractor] Generating JSON for caption: {caption[:100]}...")
            
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
            print(f"[LocalJSONExtractor] Raw output: {text}")
            
            json_str = _coerce_json(text)
            print(f"[LocalJSONExtractor] Coerced JSON: {json_str}")
            
            return (json_str,)
            
        except Exception as e:
            error_msg = f"Error in LocalJSONExtractor: {str(e)}"
            print(f"[LocalJSONExtractor] {error_msg}")
            return (json.dumps({"error": error_msg, "primary_subject": "", "secondary_subjects": [], "nsfw": False, "violence": False}),)


class MultiDomainSafetyClassifier:
    """
    Enhanced safety classifier with 5 domains and tri-state output (SAFE/BORDERLINE/UNSAFE).
    Designed for production content moderation.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        default_model_path = "C:/LLM/models/Llama-3.1-8B-Instruct-Q5_K_M.gguf"
        
        comfy_models_llm = "C:/Users/genfp/AI_avatar/Comfy_vanila/ComfyUI/models/llm"
        if os.path.exists(comfy_models_llm):
            try:
                gguf_files = [f for f in os.listdir(comfy_models_llm) if f.endswith('.gguf')]
                if gguf_files:
                    default_model_path = os.path.join(comfy_models_llm, gguf_files[0]).replace("\\", "/")
            except:
                pass
        
        return {
            "required": {
                "caption": ("STRING", {"multiline": True, "default": ""}),
                "model_path": ("STRING", {"default": default_model_path}),
            },
            "optional": {
                "temperature": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 1.0, "step": 0.05}),
                "max_new_tokens": ("INT", {"default": 300, "min": 64, "max": 1024, "step": 16}),
                "n_ctx": ("INT", {"default": 4096, "min": 1024, "max": 8192, "step": 256}),
                "n_gpu_layers": ("INT", {"default": -1, "min": -1, "max": 80, "step": 1}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("json",)
    FUNCTION = "classify"
    CATEGORY = "LLM/Local/Safety"
    
    def classify(
        self,
        caption: str,
        model_path: str,
        temperature: float = 0.1,
        max_new_tokens: int = 300,
        n_ctx: int = 4096,
        n_gpu_layers: int = -1,
    ):
        if not LLAMA_AVAILABLE:
            error_msg = "llama-cpp-python is not installed."
            return (json.dumps({
                "error": error_msg,
                "classification": {
                    "sexual": "SAFE", "violence": "SAFE", "hate": "SAFE",
                    "disturbing": "SAFE", "drugs": "SAFE"
                },
                "reasons": ["Model unavailable"],
                "confidence": 0.0
            }),)
        
        if not caption or not caption.strip():
            return (json.dumps({
                "classification": {
                    "sexual": "SAFE", "violence": "SAFE", "hate": "SAFE",
                    "disturbing": "SAFE", "drugs": "SAFE"
                },
                "reasons": ["Empty caption"],
                "confidence": 1.0
            }),)
        
        try:
            llm = _load_llm(model_path=model_path, n_ctx=n_ctx, n_gpu_layers=n_gpu_layers, seed=0)
            
            # Build multi-domain safety prompt - use few-shot examples
            full_prompt = (
                "Image: A blue ceramic bowl on a wooden table\n"
                'JSON: {"classification":{"sexual":"SAFE","violence":"SAFE","hate":"SAFE","disturbing":"SAFE","drugs":"SAFE"},"reasons":["neutral product photo"],"confidence":0.95}\n\n'
                
                "Image: A woman wearing a red bikini on a beach\n"
                'JSON: {"classification":{"sexual":"BORDERLINE","violence":"SAFE","hate":"SAFE","disturbing":"SAFE","drugs":"SAFE"},"reasons":["swimwear in appropriate context"],"confidence":0.85}\n\n'
                
                "Image: A person with a bloody knife standing over another person\n"
                'JSON: {"classification":{"sexual":"SAFE","violence":"UNSAFE","hate":"SAFE","disturbing":"UNSAFE","drugs":"SAFE"},"reasons":["depicts violence and blood"],"confidence":0.92}\n\n'
                
                f'Image: {caption}\n'
                'JSON:'
            )
            
            print(f"[MultiDomainSafetyClassifier] Analyzing caption with Llama...")
            
            response = llm(
                full_prompt,
                max_tokens=max_new_tokens,
                temperature=temperature,
                stop=["Image:", "\n\n\n", "```", "Note:", "Here's"],
                echo=False
            )
            
            raw_output = response["choices"][0]["text"].strip()
            print(f"[MultiDomainSafetyClassifier] Raw output: {raw_output[:200]}...")
            
            # Parse and validate JSON
            json_result = self._parse_safety_json(raw_output)
            
            print(f"[MultiDomainSafetyClassifier] Classification: {json_result['classification']}")
            
            return (json.dumps(json_result, ensure_ascii=False, indent=2),)
        
        except Exception as e:
            error_msg = f"Error in MultiDomainSafetyClassifier: {str(e)}"
            print(f"[MultiDomainSafetyClassifier] {error_msg}")
            import traceback
            traceback.print_exc()
            return (json.dumps({
                "error": error_msg,
                "classification": {
                    "sexual": "SAFE", "violence": "SAFE", "hate": "SAFE",
                    "disturbing": "SAFE", "drugs": "SAFE"
                },
                "reasons": [f"Classification failed: {str(e)}"],
                "confidence": 0.0
            }),)
    
    def _parse_safety_json(self, raw_output: str) -> dict:
        """Parse and validate multi-domain safety JSON output"""
        # Find JSON in output
        start = raw_output.find("{")
        end = raw_output.rfind("}")
        
        if start == -1 or end == -1:
            raise ValueError(f"No JSON found in output: {raw_output}")
        
        candidate = raw_output[start : end + 1]
        
        # Try to parse JSON, handling nested braces properly
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError as e:
            # If rfind got wrong closing brace, try to find matching brace
            brace_count = 0
            actual_end = start
            for i in range(start, len(raw_output)):
                if raw_output[i] == '{':
                    brace_count += 1
                elif raw_output[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        actual_end = i
                        break
            
            candidate = raw_output[start : actual_end + 1]
            data = json.loads(candidate)
        
        # Validate and set defaults
        if "classification" not in data:
            data["classification"] = {}
        
        classification = data["classification"]
        valid_states = ["SAFE", "BORDERLINE", "UNSAFE"]
        
        # Ensure all 5 domains exist with valid values
        for domain in ["sexual", "violence", "hate", "disturbing", "drugs"]:
            if domain not in classification or classification[domain] not in valid_states:
                classification[domain] = "SAFE"
        
        if "reasons" not in data or not isinstance(data["reasons"], list):
            data["reasons"] = ["No specific concerns detected"]
        
        if "confidence" not in data or not isinstance(data["confidence"], (int, float)):
            data["confidence"] = 0.5
        
        # Clamp confidence to [0, 1]
        data["confidence"] = max(0.0, min(1.0, float(data["confidence"])))
        
        return data


# ComfyUI entrypoint
NODE_CLASS_MAPPINGS = {
    "LocalJSONExtractorLlama": LocalJSONExtractorLlama,
    "MultiDomainSafetyClassifier": MultiDomainSafetyClassifier,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LocalJSONExtractorLlama": "Local JSON Extractor (Llama)",
    "MultiDomainSafetyClassifier": "Multi-Domain Safety Classifier (Llama)",
}
