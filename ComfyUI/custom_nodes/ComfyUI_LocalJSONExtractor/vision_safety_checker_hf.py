# vision_safety_checker_hf.py
# Vision-based safety checker using Qwen2.5-VL via HuggingFace transformers
import os
import json
import torch
from pathlib import Path
from torchvision.transforms import ToPILImage
import folder_paths

try:
    from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
    from qwen_vl_utils import process_vision_info
    import model_management
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("[VisionSafetyCheckerHF] WARNING: transformers or qwen_vl_utils not installed")


class VisionSafetyCheckerHF:
    """
    Vision-based safety checker using Qwen2.5-VL (HuggingFace transformers)
    More accurate than GGUF version
    """
    
    def __init__(self):
        self.model_checkpoint = None
        self.processor = None
        self.model = None
        self.device = model_management.get_torch_device() if TRANSFORMERS_AVAILABLE else "cuda"
        self.bf16_support = (
            torch.cuda.is_available()
            and torch.cuda.get_device_capability(self.device)[0] >= 8
        ) if TRANSFORMERS_AVAILABLE else False
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "subject_priority": (["auto", "product", "person"], {"default": "product"}),
                "model": (
                    ["Qwen2.5-VL-3B-Instruct", "Qwen2.5-VL-7B-Instruct"],
                    {"default": "Qwen2.5-VL-3B-Instruct"},
                ),
                "quantization": (["none", "4bit", "8bit"], {"default": "8bit"}),
                "keep_model_loaded": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "temperature": ("FLOAT", {"default": 0.5, "min": 0.1, "max": 1.0, "step": 0.05}),
                "max_new_tokens": ("INT", {"default": 512, "min": 128, "max": 2048, "step": 64}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("json",)
    FUNCTION = "analyze_image"
    CATEGORY = "LLM/Local"
    
    def analyze_image(
        self,
        image,
        subject_priority="product",
        model="Qwen2.5-VL-3B-Instruct",
        quantization="8bit",
        keep_model_loaded=True,
        temperature=0.5,
        max_new_tokens=512,
    ):
        if not TRANSFORMERS_AVAILABLE:
            error = "transformers or qwen_vl_utils not installed. Install: pip install transformers qwen-vl-utils"
            return (json.dumps({"error": error, "primary_subject": "", "secondary_subjects": [], "nsfw": False, "violence": False}),)
        
        try:
            # Setup model paths
            model_id = f"Qwen/{model}"
            self.model_checkpoint = os.path.join(
                folder_paths.models_dir, "prompt_generator", os.path.basename(model_id)
            )
            
            # Download model if needed
            if not os.path.exists(self.model_checkpoint):
                print(f"[VisionSafetyCheckerHF] Downloading {model}...")
                from huggingface_hub import snapshot_download
                snapshot_download(
                    repo_id=model_id,
                    local_dir=self.model_checkpoint,
                    local_dir_use_symlinks=False,
                )
            
            # Load processor
            if self.processor is None:
                print(f"[VisionSafetyCheckerHF] Loading processor...")
                self.processor = AutoProcessor.from_pretrained(
                    self.model_checkpoint,
                    min_pixels=256 * 28 * 28,
                    max_pixels=1280 * 28 * 28
                )
            
            # Load model with quantization
            if self.model is None:
                print(f"[VisionSafetyCheckerHF] Loading model with {quantization} quantization...")
                
                if quantization == "4bit":
                    quantization_config = BitsAndBytesConfig(load_in_4bit=True)
                elif quantization == "8bit":
                    quantization_config = BitsAndBytesConfig(load_in_8bit=True)
                else:
                    quantization_config = None
                
                self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                    self.model_checkpoint,
                    torch_dtype=torch.bfloat16 if self.bf16_support else torch.float16,
                    device_map="auto",
                    attn_implementation="eager",
                    quantization_config=quantization_config,
                )
                print(f"[VisionSafetyCheckerHF] Model loaded successfully")
            
            # Convert ComfyUI image to PIL and save temporarily
            # Ensure tensor is on CPU before converting to PIL
            image_tensor = image[0].cpu() if image[0].is_cuda else image[0]
            pil_image = ToPILImage()(image_tensor.permute(2, 0, 1))
            temp_path = Path(folder_paths.temp_directory) / "vision_safety_temp.png"
            pil_image.save(temp_path)
            
            # Build prompt based on priority
            if subject_priority == "product":
                focus_instruction = "If there's both a person and a product/object, focus on the PRODUCT/OBJECT as the primary subject, not the person."
            elif subject_priority == "person":
                focus_instruction = "If there's both a person and objects, focus on the PERSON as the primary subject."
            else:
                focus_instruction = ""
            
            prompt = f"""Analyze this image and return JSON with EXACTLY this structure:
{{
  "primary_subject": "main object description as a SINGLE STRING",
  "secondary_subjects": ["item 1", "item 2"],
  "nsfw": false,
  "violence": false
}}

Rules:
- primary_subject must be a STRING (e.g., "wooden striped bowl"), NOT an object
- secondary_subjects must be an ARRAY OF STRINGS (e.g., ["forest background", "sunlight"]), NOT objects
- Describe the main object's material, color, and shape in primary_subject
{focus_instruction}

Return ONLY valid JSON matching this structure exactly."""
            
            # Create messages
            messages = [
                {
                    "role": "system",
                    "content": "You are a vision analysis assistant that returns structured JSON data."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": f"file://{temp_path}"},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            
            # Process and generate
            print(f"[VisionSafetyCheckerHF] Analyzing image...")
            
            with torch.no_grad():
                text = self.processor.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
                image_inputs, video_inputs = process_vision_info(messages)
                inputs = self.processor(
                    text=[text],
                    images=image_inputs,
                    videos=video_inputs,
                    padding=True,
                    return_tensors="pt",
                )
                inputs = inputs.to(self.device)
                
                generated_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=max(temperature, 0.3),  # Minimum temperature for coherent output
                    do_sample=True if temperature > 0.1 else False,
                    top_p=0.9,
                    top_k=50,
                )
                
                generated_ids_trimmed = [
                    out_ids[len(in_ids):]
                    for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
                ]
                
                result = self.processor.batch_decode(
                    generated_ids_trimmed,
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=False,
                )[0]
            
            print(f"[VisionSafetyCheckerHF] Raw output: {result}")
            
            # Parse JSON
            start = result.find("{")
            end = result.rfind("}")
            if start != -1 and end != -1:
                json_str = result[start:end+1]
                data = json.loads(json_str)
                
                # Validate and normalize schema
                # Fix primary_subject if it's a dict
                if "primary_subject" not in data:
                    data["primary_subject"] = ""
                elif isinstance(data["primary_subject"], dict):
                    # Flatten dict to string
                    parts = [str(v) for v in data["primary_subject"].values() if v]
                    data["primary_subject"] = " ".join(parts)
                
                # Fix secondary_subjects if items are dicts
                if "secondary_subjects" not in data or not isinstance(data["secondary_subjects"], list):
                    data["secondary_subjects"] = []
                else:
                    # Flatten any dict items to strings
                    normalized = []
                    for item in data["secondary_subjects"]:
                        if isinstance(item, dict):
                            # Extract description or join values
                            if "description" in item:
                                normalized.append(item["description"])
                            else:
                                normalized.append(" ".join(str(v) for v in item.values() if v))
                        else:
                            normalized.append(str(item))
                    data["secondary_subjects"] = normalized
                
                if "nsfw" not in data:
                    data["nsfw"] = False
                if "violence" not in data:
                    data["violence"] = False
                
                json_str = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
                print(f"[VisionSafetyCheckerHF] Result: {json_str}")
                
                # Cleanup
                if not keep_model_loaded:
                    print(f"[VisionSafetyCheckerHF] Unloading model...")
                    del self.processor
                    del self.model
                    self.processor = None
                    self.model = None
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                        torch.cuda.ipc_collect()
                
                return (json_str,)
            else:
                raise ValueError(f"No JSON found in output: {result}")
        
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"[VisionSafetyCheckerHF] {error_msg}")
            return (json.dumps({"error": error_msg, "primary_subject": "", "secondary_subjects": [], "nsfw": False, "violence": False}),)


NODE_CLASS_MAPPINGS = {
    "VisionSafetyCheckerHF": VisionSafetyCheckerHF,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VisionSafetyCheckerHF": "Vision Safety Checker (Qwen2.5-VL-HF)",
}
