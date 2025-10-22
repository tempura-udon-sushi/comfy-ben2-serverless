# json_parser.py
# Helper node to parse LLM JSON output and extract fields

import json

class LLMJSONParser:
    """
    Parses JSON output from Local JSON Extractor and outputs individual fields
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json_string": ("STRING", {"forceInput": True}),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "BOOLEAN", "BOOLEAN")
    RETURN_NAMES = ("primary_subject", "secondary_subjects_text", "nsfw", "violence")
    FUNCTION = "parse_json"
    CATEGORY = "LLM/Local"
    
    def parse_json(self, json_string):
        """
        Parse the JSON string and extract fields
        """
        try:
            data = json.loads(json_string)
            
            primary_subject = data.get("primary_subject", "")
            secondary_subjects = data.get("secondary_subjects", [])
            nsfw = data.get("nsfw", False)
            violence = data.get("violence", False)
            
            # Convert secondary_subjects array to comma-separated string
            secondary_text = ", ".join(secondary_subjects) if secondary_subjects else ""
            
            return (primary_subject, secondary_text, nsfw, violence)
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse JSON: {str(e)}"
            print(f"[LLMJSONParser] {error_msg}")
            return ("", "", False, False)
        except Exception as e:
            error_msg = f"Error in JSON parser: {str(e)}"
            print(f"[LLMJSONParser] {error_msg}")
            return ("", "", False, False)


NODE_CLASS_MAPPINGS = {
    "LLMJSONParser": LLMJSONParser,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LLMJSONParser": "LLM JSON Parser",
}
