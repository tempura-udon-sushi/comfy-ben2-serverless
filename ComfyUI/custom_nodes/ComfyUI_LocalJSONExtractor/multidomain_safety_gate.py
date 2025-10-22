# multidomain_safety_gate.py
# Safety gate for Multi-Domain Safety Classifier output
import json


class MultiDomainSafetyGate:
    """
    Safety gate that blocks workflow if multi-domain classifier detects violations.
    
    Supports tri-state output (SAFE/BORDERLINE/UNSAFE) from MultiDomainSafetyClassifier.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "classification_json": ("STRING", {"forceInput": True}),
            },
            "optional": {
                "block_unsafe": ("BOOLEAN", {"default": True}),
                "block_borderline": ("BOOLEAN", {"default": False}),
                "check_sexual": ("BOOLEAN", {"default": True}),
                "check_violence": ("BOOLEAN", {"default": True}),
                "check_hate": ("BOOLEAN", {"default": True}),
                "check_disturbing": ("BOOLEAN", {"default": True}),
                "check_drugs": ("BOOLEAN", {"default": True}),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "status")
    FUNCTION = "check_and_gate"
    CATEGORY = "LLM/Local/Safety"
    
    def check_and_gate(
        self,
        image,
        classification_json: str,
        block_unsafe: bool = True,
        block_borderline: bool = False,
        check_sexual: bool = True,
        check_violence: bool = True,
        check_hate: bool = True,
        check_disturbing: bool = True,
        check_drugs: bool = True,
    ):
        try:
            data = json.loads(classification_json)
        except json.JSONDecodeError as e:
            error = f"Invalid JSON from classifier: {e}"
            print(f"[MultiDomainSafetyGate] {error}")
            return (image, f"ERROR: {error}")
        
        # Extract classification
        if "classification" not in data:
            error = "Missing 'classification' in JSON"
            print(f"[MultiDomainSafetyGate] {error}")
            return (image, f"ERROR: {error}")
        
        classification = data["classification"]
        reasons = data.get("reasons", [])
        confidence = data.get("confidence", 0.0)
        
        print(f"[MultiDomainSafetyGate] Checking content safety:")
        print(f"  Sexual: {classification.get('sexual', 'UNKNOWN')}")
        print(f"  Violence: {classification.get('violence', 'UNKNOWN')}")
        print(f"  Hate: {classification.get('hate', 'UNKNOWN')}")
        print(f"  Disturbing: {classification.get('disturbing', 'UNKNOWN')}")
        print(f"  Drugs: {classification.get('drugs', 'UNKNOWN')}")
        print(f"  Confidence: {confidence:.2f}")
        
        # Check for violations
        violations = []
        
        if check_sexual:
            status = classification.get("sexual", "SAFE")
            if block_unsafe and status == "UNSAFE":
                violations.append(f"Sexual content ({status})")
            elif block_borderline and status == "BORDERLINE":
                violations.append(f"Sexual content ({status})")
        
        if check_violence:
            status = classification.get("violence", "SAFE")
            if block_unsafe and status == "UNSAFE":
                violations.append(f"Violent content ({status})")
            elif block_borderline and status == "BORDERLINE":
                violations.append(f"Violent content ({status})")
        
        if check_hate:
            status = classification.get("hate", "SAFE")
            if block_unsafe and status == "UNSAFE":
                violations.append(f"Hate content ({status})")
            elif block_borderline and status == "BORDERLINE":
                violations.append(f"Hate content ({status})")
        
        if check_disturbing:
            status = classification.get("disturbing", "SAFE")
            if block_unsafe and status == "UNSAFE":
                violations.append(f"Disturbing content ({status})")
            elif block_borderline and status == "BORDERLINE":
                violations.append(f"Disturbing content ({status})")
        
        if check_drugs:
            status = classification.get("drugs", "SAFE")
            if block_unsafe and status == "UNSAFE":
                violations.append(f"Drug/crime content ({status})")
            elif block_borderline and status == "BORDERLINE":
                violations.append(f"Drug/crime content ({status})")
        
        # Block if violations found
        if violations:
            reason_text = " | ".join(violations)
            if reasons:
                reason_text += f" | Reasons: {', '.join(reasons)}"
            
            error_msg = f"Content blocked by multi-domain safety gate: {reason_text}"
            print(f"[MultiDomainSafetyGate] ❌ BLOCKED: {reason_text}")
            raise ValueError(error_msg)
        
        # All safe, pass through
        status_msg = "SAFE: All domains passed safety check"
        print(f"[MultiDomainSafetyGate] ✅ {status_msg}")
        return (image, status_msg)


NODE_CLASS_MAPPINGS = {
    "MultiDomainSafetyGate": MultiDomainSafetyGate,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MultiDomainSafetyGate": "Multi-Domain Safety Gate",
}
