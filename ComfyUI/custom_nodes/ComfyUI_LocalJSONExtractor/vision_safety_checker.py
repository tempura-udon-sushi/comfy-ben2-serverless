# vision_safety_checker.py
# Vision-based safety checker using Qwen2.5-VL (direct image analysis)
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
    """Load Qwen2.5-VL model with vision support"""
    key = f"{model_path}|{mmproj_path}"
    if key in _QWEN_CACHE:
        return _QWEN_CACHE[key]
    
    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}")
    if not os.path.isfile(mmproj_path):
        raise FileNotFoundError(f"Vision projector not found: {mmproj_path}")
    
    print(f"[VisionSafetyChecker] Loading Qwen2.5-VL model: {os.path.basename(model_path)}")
    print(f"[VisionSafetyChecker] Vision projector: {os.path.basename(mmproj_path)}")
    
    chat_handler = Llava15ChatHandler(clip_model_path=mmproj_path)
    
    llm = Llama(
        model_path=model_path,
        chat_handler=chat_handler,
        n_ctx=4096,
        n_gpu_layers=n_gpu_layers,
        verbose=False
    )
    
    _QWEN_CACHE[key] = llm
    print(f"[VisionSafetyChecker] Model loaded and cached successfully")
    return llm


class VisionSafetyChecker:
    """
    Direct image-to-JSON safety checker using Qwen2.5-VL
    Replaces Florence-2 + Llama workflow with single vision model
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        default_model = "C:/Users/genfp/AI_avatar/Comfy_vanila/ComfyUI/models/llm/qwen3vl/Qwen2.5-VL-3B-Instruct-q8_0.gguf"
        default_mmproj = "C:/Users/genfp/AI_avatar/Comfy_vanila/ComfyUI/models/llm/qwen3vl/Qwen2.5-VL-3B-Instruct-mmproj-f16.gguf"
        
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
            temp_dir = "C:/Users/genfp/AI_avatar/Comfy_vanila/ComfyUI/temp"
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, "vision_temp.jpg")
            pil_image.save(temp_path)
            
            # Build prompt based on priority
            if subject_priority == "product":
                priority_text = "IMPORTANT: If there's both a person and a product/object in the image, the primary_subject MUST be the PRODUCT/OBJECT, NOT the person."
            elif subject_priority == "person":
                priority_text = "IMPORTANT: If there's both a person and objects in the image, the primary_subject MUST be the PERSON with their attributes."
            else:
                priority_text = ""
            
            # Simpler prompt for Qwen2.5-VL
            if subject_priority == "product":
                focus = "Focus on the product/object, not the person."
            elif subject_priority == "person":
                focus = "Focus on the person, not objects."
            else:
                focus = ""
            
            prompt = f"""Describe this image. {focus}
What is the main subject?
Are there any other objects or actions?
Is this NSFW or violent content?

Return as JSON with: primary_subject, secondary_subjects (array), nsfw (boolean), violence (boolean)"""
            
            # Load model and run inference
            llm = _load_vision_llm(model_path, mmproj_path, n_gpu_layers)
            
            print(f"[VisionSafetyChecker] Analyzing image...")
            
            # Convert to proper file:// URL for Windows (file:/// with 3 slashes)
            temp_path_unix = temp_path.replace("\\", "/")
            file_url = f"file:///{temp_path_unix}" if not temp_path_unix.startswith("file://") else temp_path_unix
            
            print(f"[VisionSafetyChecker] Image URL: {file_url}")
            
            response = llm.create_chat_completion(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": file_url}},
                            {"type": "text", "text": prompt}
                        ]
                    }
                ],
                temperature=temperature,
                max_tokens=512,  # Increased for more output
                stream=False,
            )
            
            text = response["choices"][0]["message"]["content"]
            print(f"[VisionSafetyChecker] Raw output ({len(text)} chars): {text}")
            
            # If output is empty or too short, use fallback
            if not text or len(text.strip()) < 10:
                print("[VisionSafetyChecker] Model returned empty/short output, using fallback")
                return (json.dumps({"primary_subject": "unknown object", "secondary_subjects": [], "nsfw": False, "violence": False}),)
            
            # Parse JSON
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                json_str = text[start:end+1]
                data = json.loads(json_str)
                
                # Validate and fix schema
                if "primary_subject" not in data:
                    data["primary_subject"] = ""
                if "secondary_subjects" not in data or not isinstance(data["secondary_subjects"], list):
                    data["secondary_subjects"] = []
                if "nsfw" not in data:
                    data["nsfw"] = False
                if "violence" not in data:
                    data["violence"] = False
                
                # Normalize JSON
                json_str = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
                print(f"[VisionSafetyChecker] Result: {json_str}")
                return (json_str,)
            else:
                raise ValueError(f"No JSON found in output: {text}")
                
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"[VisionSafetyChecker] {error_msg}")
            return (json.dumps({"error": error_msg, "primary_subject": "", "secondary_subjects": [], "nsfw": False, "violence": False}),)


NODE_CLASS_MAPPINGS = {
    "VisionSafetyChecker": VisionSafetyChecker,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VisionSafetyChecker": "Vision Safety Checker (Qwen2.5-VL)",
}
