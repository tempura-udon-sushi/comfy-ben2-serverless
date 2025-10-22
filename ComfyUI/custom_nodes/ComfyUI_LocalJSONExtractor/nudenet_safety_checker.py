# nudenet_safety_checker.py
# NudeNet integration for accurate nudity detection
import os
import json
import numpy as np
from PIL import Image
import folder_paths

try:
    from nudenet import NudeDetector
    NUDENET_AVAILABLE = True
except ImportError:
    NUDENET_AVAILABLE = False
    print("[NudeNetSafetyChecker] WARNING: nudenet not installed. Run: pip install nudenet")


class NudeNetSafetyChecker:
    """
    Specialized nudity detector using NudeNet.
    More accurate than text-based classification for sexual content.
    """
    
    def __init__(self):
        self.detector = None
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "threshold": ("FLOAT", {"default": 0.6, "min": 0.0, "max": 1.0, "step": 0.05}),
            }
        }
    
    RETURN_TYPES = ("STRING", "BOOLEAN", "FLOAT")
    RETURN_NAMES = ("json", "is_nsfw", "max_score")
    FUNCTION = "check_nudity"
    CATEGORY = "LLM/Local/Safety"
    
    def check_nudity(self, image, threshold=0.6):
        if not NUDENET_AVAILABLE:
            error = "nudenet not installed. Install: pip install nudenet"
            return (
                json.dumps({"error": error, "is_nsfw": False, "detections": []}),
                False,
                0.0
            )
        
        try:
            # Load detector if not loaded
            if self.detector is None:
                print("[NudeNetSafetyChecker] Loading NudeNet model...")
                self.detector = NudeDetector()
                print("[NudeNetSafetyChecker] Model loaded")
            
            # Convert ComfyUI tensor to PIL Image
            img_tensor = image[0].cpu() if image[0].is_cuda else image[0]
            img_np = (img_tensor.numpy() * 255).astype(np.uint8)
            pil_image = Image.fromarray(img_np)
            
            # Save temporarily for NudeNet (it requires file path)
            temp_dir = os.path.join(folder_paths.get_temp_directory(), "nudenet")
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, "check.jpg")
            pil_image.save(temp_path, quality=95)
            
            print("[NudeNetSafetyChecker] Analyzing image with NudeNet...")
            
            # Run detection
            detections = self.detector.detect(temp_path)
            
            # Clean up temp file
            try:
                os.remove(temp_path)
            except:
                pass
            
            # Classify detections
            nsfw_labels = [
                "FEMALE_BREAST_EXPOSED",
                "FEMALE_GENITALIA_EXPOSED",
                "MALE_GENITALIA_EXPOSED",
                "ANUS_EXPOSED",
                "BUTTOCKS_EXPOSED"
            ]
            
            nsfw_detections = []
            max_score = 0.0
            
            for detection in detections:
                label = detection.get("class", "")
                score = detection.get("score", 0.0)
                
                if label in nsfw_labels and score >= threshold:
                    nsfw_detections.append({
                        "label": label,
                        "score": score,
                        "box": detection.get("box", [])
                    })
                    max_score = max(max_score, score)
            
            is_nsfw = len(nsfw_detections) > 0
            
            print(f"[NudeNetSafetyChecker] Results:")
            print(f"  NSFW: {is_nsfw}")
            print(f"  Max Score: {max_score:.3f}")
            print(f"  Detections: {len(nsfw_detections)}")
            
            if is_nsfw:
                for det in nsfw_detections:
                    print(f"    - {det['label']}: {det['score']:.3f}")
            
            result = {
                "is_nsfw": is_nsfw,
                "max_score": max_score,
                "threshold": threshold,
                "detections": nsfw_detections,
                "all_detections_count": len(detections),
                "model": "NudeNet"
            }
            
            return (json.dumps(result, indent=2), is_nsfw, max_score)
        
        except Exception as e:
            error_msg = f"Error in NudeNetSafetyChecker: {str(e)}"
            print(f"[NudeNetSafetyChecker] {error_msg}")
            import traceback
            traceback.print_exc()
            return (
                json.dumps({"error": error_msg, "is_nsfw": False, "detections": []}),
                False,
                0.0
            )


class HybridSafetyGate:
    """
    Combines NudeNet (for sexual content) + Multi-Domain Classifier (for other categories).
    Best of both worlds: specialized model + contextual understanding.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "nudenet_json": ("STRING", {"forceInput": True}),
                "multidomain_json": ("STRING", {"forceInput": True}),
            },
            "optional": {
                "block_unsafe": ("BOOLEAN", {"default": True}),
                "block_borderline": ("BOOLEAN", {"default": False}),
                "nudenet_overrides_llama": ("BOOLEAN", {"default": True}),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "status")
    FUNCTION = "check_hybrid"
    CATEGORY = "LLM/Local/Safety"
    
    def check_hybrid(
        self,
        image,
        nudenet_json: str,
        multidomain_json: str,
        block_unsafe: bool = True,
        block_borderline: bool = False,
        nudenet_overrides_llama: bool = True,
    ):
        violations = []
        
        try:
            # Parse NudeNet results
            nudenet_data = json.loads(nudenet_json)
            is_nsfw = nudenet_data.get("is_nsfw", False)
            nudenet_score = nudenet_data.get("max_score", 0.0)
            
            # Parse Multi-Domain results
            multidomain_data = json.loads(multidomain_json)
            classification = multidomain_data.get("classification", {})
            
            print("[HybridSafetyGate] Combined Safety Check:")
            print(f"  NudeNet NSFW: {is_nsfw} (score: {nudenet_score:.3f})")
            
            # Check NudeNet (sexual content)
            if is_nsfw:
                violations.append(f"Sexual content detected by NudeNet (score: {nudenet_score:.3f})")
            elif not nudenet_overrides_llama:
                # Also check Llama's sexual classification if NudeNet didn't override
                sexual_status = classification.get("sexual", "SAFE")
                if block_unsafe and sexual_status == "UNSAFE":
                    violations.append(f"Sexual content (Llama: {sexual_status})")
                elif block_borderline and sexual_status == "BORDERLINE":
                    violations.append(f"Sexual content (Llama: {sexual_status})")
            
            # Check other domains from Multi-Domain Classifier
            for domain in ["violence", "hate", "disturbing", "drugs"]:
                status = classification.get(domain, "SAFE")
                print(f"  {domain.capitalize()}: {status}")
                
                if block_unsafe and status == "UNSAFE":
                    violations.append(f"{domain.capitalize()} content ({status})")
                elif block_borderline and status == "BORDERLINE":
                    violations.append(f"{domain.capitalize()} content ({status})")
            
            # Block if violations found
            if violations:
                reason_text = " | ".join(violations)
                error_msg = f"Content blocked by hybrid safety gate: {reason_text}"
                print(f"[HybridSafetyGate] ❌ BLOCKED: {reason_text}")
                raise ValueError(error_msg)
            
            # All safe
            status_msg = "SAFE: Passed NudeNet + Multi-Domain checks"
            print(f"[HybridSafetyGate] ✅ {status_msg}")
            return (image, status_msg)
        
        except ValueError:
            # Re-raise blocking errors
            raise
        except Exception as e:
            error = f"Error in HybridSafetyGate: {str(e)}"
            print(f"[HybridSafetyGate] {error}")
            return (image, f"ERROR: {error}")


NODE_CLASS_MAPPINGS = {
    "NudeNetSafetyChecker": NudeNetSafetyChecker,
    "HybridSafetyGate": HybridSafetyGate,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NudeNetSafetyChecker": "NudeNet Safety Checker",
    "HybridSafetyGate": "Hybrid Safety Gate (NudeNet + Llama)",
}
