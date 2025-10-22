"""
Content Safety Checker for Florence2 captions
Blocks NSFW and violent content from processing
"""
import re

class ContentSafetyChecker:
    """
    Checks Florence2 caption for inappropriate content (NSFW, violence)
    Raises an error to stop workflow if unsafe content is detected
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "florence_caption": ("STRING", {"forceInput": True}),
                "strict_mode": ("BOOLEAN", {"default": True}),
            },
        }
    
    RETURN_TYPES = ("STRING", "BOOLEAN")
    RETURN_NAMES = ("safe_caption", "is_safe")
    FUNCTION = "check_safety"
    CATEGORY = "text"

    def get_unsafe_keywords(self):
        """
        Keywords that indicate NSFW or violent content
        Organized by category for easier maintenance
        """
        return {
            'nsfw_explicit': [
                'naked', 'nude', 'nudity', 'topless', 'bottomless',
                'sex', 'sexual', 'porn', 'pornographic', 'erotic',
                'breast', 'breasts', 'nipple', 'nipples', 'genitalia',
                'underwear', 'lingerie', 'bra', 'panties',
            ],
            'nsfw_suggestive': [
                'bikini', 'swimsuit', 'revealing', 'provocative',
                'seductive', 'intimate', 'sensual',
            ],
            'violence_explicit': [
                'blood', 'bloody', 'bleeding', 'gore', 'gory',
                'dead', 'death', 'dying', 'corpse', 'cadaver',
                'murder', 'killing', 'killed', 'stabbing', 'stabbed',
                'shooting', 'shot', 'beaten', 'torture', 'tortured',
                'dismembered', 'decapitated', 'mutilated',
            ],
            'violence_weapons': [
                'gun', 'knife', 'sword', 'weapon', 'rifle', 'pistol',
                'blade', 'dagger', 'assault',
            ],
            'violence_action': [
                'fighting', 'attacking', 'attack', 'violence', 'violent',
                'assault', 'assaulting', 'hitting', 'punching',
            ],
            'disturbing': [
                'hanging', 'suicide', 'self-harm', 'abuse', 'abused',
                'injury', 'injured', 'wound', 'wounded',
            ]
        }

    def check_caption_safety(self, caption, strict_mode=True):
        """
        Check if caption contains unsafe content
        
        Args:
            caption: Florence2 caption text
            strict_mode: If True, includes suggestive content. If False, only explicit content.
        
        Returns:
            (is_safe, category, matched_keywords)
        """
        caption_lower = caption.lower()
        unsafe_keywords = self.get_unsafe_keywords()
        
        # Categories to check based on mode
        if strict_mode:
            categories_to_check = list(unsafe_keywords.keys())
        else:
            # In non-strict mode, skip suggestive content
            categories_to_check = [k for k in unsafe_keywords.keys() if 'suggestive' not in k]
        
        # Check for unsafe keywords
        matched_keywords = []
        for category in categories_to_check:
            for keyword in unsafe_keywords[category]:
                # Use word boundaries to avoid false positives
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, caption_lower):
                    matched_keywords.append((category, keyword))
        
        if matched_keywords:
            return False, matched_keywords[0][0], [kw[1] for kw in matched_keywords]
        
        return True, None, []

    def check_safety(self, florence_caption, strict_mode=True):
        """
        Check content safety and return results or raise error
        """
        is_safe, category, matched_keywords = self.check_caption_safety(florence_caption, strict_mode)
        
        if not is_safe:
            # Create detailed error message
            keywords_str = ', '.join(matched_keywords[:3])  # Show first 3 matched keywords
            error_msg = f"""
⚠️ CONTENT SAFETY WARNING ⚠️

The uploaded image appears to contain inappropriate content.
Category: {category}
Detected keywords: {keywords_str}

For safety reasons, this image cannot be processed.
Please upload appropriate product photos only.

If you believe this is an error, try:
1. Using a different photo angle
2. Ensuring good lighting and clear product visibility
3. Removing any background items that might be flagged
4. Disabling strict mode (for borderline cases like swimwear)
"""
            # Raise error to stop the workflow
            raise ValueError(error_msg)
        
        # If safe, return the caption and safety status
        return (florence_caption, True)


class ContentSafetyBypass:
    """
    Allows bypassing safety check for testing or trusted users
    Use with caution - only for authorized users
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "florence_caption": ("STRING", {"forceInput": True}),
                "bypass_password": ("STRING", {"default": ""}),
            },
        }
    
    RETURN_TYPES = ("STRING", "BOOLEAN")
    RETURN_NAMES = ("caption", "is_safe")
    FUNCTION = "bypass_check"
    CATEGORY = "text"
    
    def bypass_check(self, florence_caption, bypass_password):
        """
        Bypass safety check with password
        Change the password below for production use
        """
        # TODO: Change this password in production!
        BYPASS_PASSWORD = "minne_admin_2025"
        
        if bypass_password == BYPASS_PASSWORD:
            return (florence_caption, True)
        else:
            raise ValueError("Invalid bypass password. Safety check cannot be bypassed.")


NODE_CLASS_MAPPINGS = {
    "ContentSafetyChecker": ContentSafetyChecker,
    "ContentSafetyBypass": ContentSafetyBypass,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ContentSafetyChecker": "Content Safety Checker",
    "ContentSafetyBypass": "Content Safety Bypass (Admin Only)",
}
