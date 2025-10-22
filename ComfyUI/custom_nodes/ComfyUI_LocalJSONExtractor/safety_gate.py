# safety_gate.py
# Safety gate node to stop workflow if content is flagged as NSFW or violent

import json

class LLMSafetyGate:
    """
    Safety gate that checks NSFW/violence flags and stops execution if flagged.
    Can work with either JSON string or boolean inputs.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "primary_subject": ("STRING", {"forceInput": True}),
            },
            "optional": {
                "nsfw": ("BOOLEAN", {"default": False, "forceInput": True}),
                "violence": ("BOOLEAN", {"default": False, "forceInput": True}),
                "stop_on_nsfw": ("BOOLEAN", {"default": True}),
                "stop_on_violence": ("BOOLEAN", {"default": True}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("safe_subject",)
    FUNCTION = "check_safety"
    CATEGORY = "LLM/Local"
    
    def check_safety(
        self, 
        primary_subject, 
        nsfw=False, 
        violence=False, 
        stop_on_nsfw=True, 
        stop_on_violence=True
    ):
        """
        Check safety flags and either pass through or stop execution
        """
        # Check flags
        is_nsfw = nsfw if isinstance(nsfw, bool) else False
        is_violent = violence if isinstance(violence, bool) else False
        
        print(f"[SafetyGate] Checking content: '{primary_subject[:50]}...'")
        print(f"[SafetyGate] NSFW: {is_nsfw}, Violence: {is_violent}")
        
        # Determine if we should block
        should_block = False
        reasons = []
        
        if stop_on_nsfw and is_nsfw:
            should_block = True
            reasons.append("NSFW content detected")
        
        if stop_on_violence and is_violent:
            should_block = True
            reasons.append("Violent content detected")
        
        if should_block:
            reason_text = " and ".join(reasons)
            error_msg = f"[SafetyGate] ❌ BLOCKED: {reason_text}. Subject: '{primary_subject}'"
            print(error_msg)
            
            # Raise exception to stop the workflow
            raise ValueError(f"Content blocked by safety gate: {reason_text}")
        
        # Content is safe, pass through
        print(f"[SafetyGate] ✅ SAFE: Content passed safety check")
        return (primary_subject,)


class LLMSafetyGateJSON:
    """
    Safety gate that works directly with JSON string from Local JSON Extractor.
    Parses JSON and checks flags in one step.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json_string": ("STRING", {"forceInput": True}),
            },
            "optional": {
                "stop_on_nsfw": ("BOOLEAN", {"default": True}),
                "stop_on_violence": ("BOOLEAN", {"default": True}),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "BOOLEAN", "BOOLEAN")
    RETURN_NAMES = ("primary_subject", "secondary_subjects_text", "nsfw", "violence")
    FUNCTION = "check_safety_json"
    CATEGORY = "LLM/Local"
    
    def check_safety_json(self, json_string, stop_on_nsfw=True, stop_on_violence=True):
        """
        Parse JSON and check safety flags, stopping execution if flagged
        """
        try:
            data = json.loads(json_string)
            
            primary_subject = data.get("primary_subject", "")
            secondary_subjects = data.get("secondary_subjects", [])
            nsfw = data.get("nsfw", False)
            violence = data.get("violence", False)
            
            secondary_text = ", ".join(secondary_subjects) if secondary_subjects else ""
            
            print(f"[SafetyGateJSON] Checking content: '{primary_subject[:50]}...'")
            print(f"[SafetyGateJSON] NSFW: {nsfw}, Violence: {violence}")
            
            # Check if content should be blocked
            should_block = False
            reasons = []
            
            if stop_on_nsfw and nsfw:
                should_block = True
                reasons.append("NSFW content detected")
            
            if stop_on_violence and violence:
                should_block = True
                reasons.append("Violent content detected")
            
            if should_block:
                reason_text = " and ".join(reasons)
                error_msg = f"[SafetyGateJSON] ❌ BLOCKED: {reason_text}. Subject: '{primary_subject}'"
                print(error_msg)
                
                # Raise exception to stop the workflow
                raise ValueError(f"Content blocked by safety gate: {reason_text}")
            
            # Content is safe, pass through all values
            print(f"[SafetyGateJSON] ✅ SAFE: Content passed safety check")
            return (primary_subject, secondary_text, nsfw, violence)
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse JSON: {str(e)}"
            print(f"[SafetyGateJSON] {error_msg}")
            raise ValueError(error_msg)
        except ValueError:
            # Re-raise safety gate blocks
            raise
        except Exception as e:
            error_msg = f"Error in safety gate: {str(e)}"
            print(f"[SafetyGateJSON] {error_msg}")
            raise ValueError(error_msg)


class ImageSafetyGate:
    """
    Safety gate for image workflows (e.g. BEN2, BiRefNet).
    Takes IMAGE input, checks safety flags from JSON analysis, and passes through IMAGE if safe.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "json_string": ("STRING", {"forceInput": True}),
            },
            "optional": {
                "stop_on_nsfw": ("BOOLEAN", {"default": True}),
                "stop_on_violence": ("BOOLEAN", {"default": True}),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING", "BOOLEAN", "BOOLEAN")
    RETURN_NAMES = ("image", "primary_subject", "nsfw", "violence")
    FUNCTION = "check_image_safety"
    CATEGORY = "LLM/Local"
    
    def check_image_safety(self, image, json_string, stop_on_nsfw=True, stop_on_violence=True):
        """
        Parse JSON safety analysis and pass through IMAGE if safe, otherwise block execution
        """
        try:
            data = json.loads(json_string)
            
            primary_subject = data.get("primary_subject", "")
            nsfw = data.get("nsfw", False)
            violence = data.get("violence", False)
            
            print(f"[ImageSafetyGate] Checking content: '{primary_subject[:50]}...'")
            print(f"[ImageSafetyGate] NSFW: {nsfw}, Violence: {violence}")
            
            # Check if content should be blocked
            should_block = False
            reasons = []
            
            if stop_on_nsfw and nsfw:
                should_block = True
                reasons.append("NSFW content detected")
            
            if stop_on_violence and violence:
                should_block = True
                reasons.append("Violent content detected")
            
            if should_block:
                reason_text = " and ".join(reasons)
                error_msg = f"[ImageSafetyGate] ❌ BLOCKED: {reason_text}. Subject: '{primary_subject}'"
                print(error_msg)
                
                # Raise exception to stop the workflow
                raise ValueError(f"Content blocked by safety gate: {reason_text}")
            
            # Content is safe, pass through IMAGE and analysis data
            print(f"[ImageSafetyGate] ✅ SAFE: Image passed safety check")
            return (image, primary_subject, nsfw, violence)
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse JSON: {str(e)}"
            print(f"[ImageSafetyGate] {error_msg}")
            raise ValueError(error_msg)
        except ValueError:
            # Re-raise safety gate blocks
            raise
        except Exception as e:
            error_msg = f"Error in safety gate: {str(e)}"
            print(f"[ImageSafetyGate] {error_msg}")
            raise ValueError(error_msg)


NODE_CLASS_MAPPINGS = {
    "LLMSafetyGate": LLMSafetyGate,
    "LLMSafetyGateJSON": LLMSafetyGateJSON,
    "ImageSafetyGate": ImageSafetyGate,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LLMSafetyGate": "LLM Safety Gate",
    "LLMSafetyGateJSON": "LLM Safety Gate (JSON)",
    "ImageSafetyGate": "Image Safety Gate",
}
