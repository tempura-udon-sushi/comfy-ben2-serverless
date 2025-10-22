import re

class DynamicPromptBuilder:
    """
    Extracts product type from Florence2 caption and builds dynamic prompt
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "florence_caption": ("STRING", {"forceInput": True}),
                "prompt_template": ("STRING", {
                    "multiline": True,
                    "default": "Cut out the {product} and place it on a pure white background, like an e-commerce product photo. Preserve realistic texture, colors, and subtle shadows."
                }),
            },
        }
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("dynamic_prompt",)
    FUNCTION = "build_prompt"
    CATEGORY = "text"

    def extract_product_type(self, caption):
        """
        Extract product type from Florence2 caption
        Optimized for Minne (Japanese handcraft marketplace) categories
        
        Handles multi-object scenarios by prioritizing:
        1. Subject of sentence (appears first, before prepositions)
        2. Objects NOT in background positions (not after "next to", "behind", etc.)
        3. Most specific product terms
        """
        caption = caption.lower()
        
        # Common adjectives/materials to skip (not products themselves)
        skip_words = [
            'wooden', 'metal', 'silver', 'gold', 'brass', 'copper', 'leather', 'fabric',
            'cotton', 'wool', 'silk', 'linen', 'plastic', 'glass', 'ceramic', 'clay',
            'handmade', 'vintage', 'antique', 'modern', 'custom', 'unique', 'beautiful',
            'small', 'large', 'big', 'tiny', 'colorful', 'white', 'black', 'red', 'blue',
            'green', 'yellow', 'pink', 'purple', 'brown', 'gray', 'grey'
        ]
        
        # Background/support objects (NOT the main product)
        background_objects = [
            'table', 'desk', 'shelf', 'floor', 'ground', 'wall', 'surface', 'counter',
            'box', 'container', 'stand', 'holder', 'display', 'rack', 'board',
            'background', 'backdrop', 'cloth', 'fabric', 'sheet', 'paper',
            'wood', 'stone', 'marble', 'tile', 'carpet', 'mat'
        ]
        
        # Minne product categories (translated from Japanese)
        # Ordered by specificity - more specific terms first to avoid false matches
        products = [
            # Accessories & Jewelry (most common on Minne)
            'earrings', 'ear cuff', 'piercing', 'necklace', 'choker', 'bracelet', 'bangle',
            'ring', 'anklet', 'brooch', 'corsage', 'hair clip', 'barrette', 'hair band',
            'headband', 'turban', 'hair tie', 'scrunchie', 'hair pin', 'hairpin',
            'ponytail hook', 'kanzashi', 'watch', 'tie pin', 'cufflinks', 'cuff links',
            'keychain', 'key holder', 'strap', 'charm',
            
            # Fashion
            't-shirt', 'tshirt', 'dress', 'one-piece', 'blouse', 'shirt', 'cardigan',
            'sweater', 'sweatshirt', 'hoodie', 'parka', 'coat', 'jacket', 'pants',
            'trousers', 'skirt', 'kimono', 'yukata', 'jinbei', 'costume',
            'scarf', 'stole', 'muffler', 'neck warmer', 'handkerchief',
            'nail tips', 'nail art',
            
            # Bags & Wallets
            'tote bag', 'tote', 'eco bag', 'shopping bag', 'shoulder bag', 'pochette',
            'sacoche', 'backpack', 'rucksack', 'body bag', 'waist pouch', 'fanny pack',
            'handbag', 'boston bag', 'clutch bag', 'clutch', 'basket bag', 'basket',
            'bag', 'pouch', 'drawstring bag', 'wallet', 'purse', 'coin case',
            'key case', 'pass case', 'card case', 'bag charm', 'glasses case',
            'tissue case', 'compact mirror', 'mirror',
            
            # Hats & Footwear
            'hat', 'cap', 'beanie', 'beret', 'fedora', 'sun hat',
            'shoes', 'boots', 'sneakers', 'sandals', 'slippers', 'indoor shoes',
            'socks', 'stockings', 'tights', 'leg warmers',
            'umbrella', 'parasol',
            
            # Baby & Kids
            'bib', 'baby clothes', 'baby blanket', 'swaddle', 'maternity',
            'diaper pouch', 'mother and child notebook case', 'apron', 'smock',
            'name tag', 'name sticker', 'lesson bag', 'indoor shoe bag',
            'lunch bag', 'placemat', 'water bottle', 'drawstring pouch',
            
            # Home & Living
            'table', 'desk', 'chair', 'cushion', 'pillow', 'storage furniture',
            'bookshelf', 'magazine rack', 'tv stand', 'lamp', 'lighting', 'light',
            'clock', 'nameplate', 'doormat', 'bath mat', 'trash can',
            'storage box', 'basket', 'curtain', 'rug', 'mat', 'carpet',
            'tissue cover', 'vase', 'photo frame', 'frame', 'ornament', 'figurine',
            'wall sticker', 'wall decal', 'garland', 'tapestry', 'sun catcher',
            'wind chime', 'mobile',
            
            # Pet Goods
            'pet wear', 'pet collar', 'leash', 'pet toy', 'pet accessory',
            
            # Flowers & Garden
            'wreath', 'shimenawa', 'swag', 'flower arrangement', 'herbarium',
            'houseplant', 'plant', 'bouquet', 'dried flowers', 'preserved flowers',
            'planter', 'flower pot', 'pot',
            
            # Phone & Tech
            'cell phone', 'smartphone', 'phone', 'mobile phone', 'iphone', 'android',
            'phone case', 'smartphone case', 'phone ring', 'phone grip',
            'earphone jack', 'phone strap', 'cord holder', 'phone pouch',
            'phone stand', 'tablet case', 'tablet', 'pc case', 'laptop case',
            'camera bag', 'camera strap', 'camera',
            
            # Tableware & Kitchen
            'glass', 'cup', 'tumbler', 'mug', 'coffee cup', 'teacup', 'saucer',
            'sake cup', 'sake set', 'plate', 'dish', 'rice bowl', 'bowl',
            'chopsticks', 'cutlery', 'spoon', 'fork', 'knife', 'chopstick rest',
            'tray', 'coaster', 'cooking utensil', 'cutting board', 'cookie cutter',
            'spice rack', 'storage container', 'pot holder', 'pot mat', 'trivet',
            'kitchen cloth', 'dish towel', 'tablecloth', 'lunch box', 'bento box',
            'thermos', 'bottle holder',
            
            # Candles & Aroma
            'candle', 'candle holder', 'aroma diffuser', 'aroma stone',
            'sachet', 'potpourri', 'incense holder',
            
            # Stationery
            'stamp', 'seal', 'seal case', 'sticker', 'masking tape', 'washi tape',
            'postcard', 'message card', 'business card', 'letter set', 'envelope',
            'money envelope', 'gift envelope', 'book cover', 'bookmark',
            'notebook', 'notepad', 'planner', 'diary', 'calendar', 'pen', 'pencil',
            'pen case', 'pencil case', 'paper craft', 'card stand', 'magnet',
            
            # Toys & Crafts
            'stuffed animal', 'plush toy', 'plush', 'amigurumi', 'doll', 'felt',
            'toy', 'figure', 'figurine', 'miniature', 'educational toy',
            'sculpture', 'statue', 'carving', 'ornament',
            
            # Masks
            'mask', 'mask cover', 'inner mask', 'mask case', 'mask holder', 'mask strap',
            
            # Food (less common but exists on Minne)
            'bread', 'rice', 'pasta', 'granola', 'cookie', 'cake', 'sweets', 'candy',
            'coffee', 'tea', 'jam', 'syrup', 'cheese', 'seasoning', 'spice',
            
            # Generic fallbacks
            'jewelry', 'accessory', 'accessories', 'clothing', 'wear', 'item'
        ]
        
        # Background position indicators - objects after these are usually NOT the main product
        background_phrases = [
            'sitting on', 'placed on', 'lying on', 'resting on', 'standing on',
            'on top of', 'on a', 'on the',
            'next to', 'beside', 'behind', 'in front of', 'near',
            'against', 'by', 'with a', 'with the', 'and a', 'and the',
            'in a', 'in the', 'inside'
        ]
        
        # Step 1: Split caption at background phrases to isolate main subject
        main_part = caption
        background_part = ""
        for phrase in background_phrases:
            if phrase in caption:
                # Split into main subject and background
                parts = caption.split(phrase, 1)
                main_part = parts[0]
                background_part = phrase + parts[1] if len(parts) > 1 else ""
                break
        
        # Step 2: Find all matching products in the main part (skip adjectives only)
        # Note: Don't skip background_objects here - they might be the main product!
        found_products = []
        for product in products:
            if product in main_part:
                # Only skip adjectives/materials, not background objects
                # (e.g., "A handmade table" - table is the main product here)
                if product not in skip_words:
                    # Check if this product also appears in background_part
                    # If yes, and it's a background_object, it's likely NOT the main product
                    if product in background_objects and product in background_part:
                        continue  # Skip this one, it's in the background
                    
                    # Store product with its position (earlier = more important)
                    position = main_part.find(product)
                    found_products.append((product, position))
        
        # Step 3: If found in main part, return the earliest/most specific one
        if found_products:
            # Sort by position (earlier in sentence = more likely to be subject)
            found_products.sort(key=lambda x: x[1])
            return found_products[0][0]
        
        # Step 4: If nothing in main part, check full caption as fallback (skip adjectives & background objects)
        for product in products:
            if product in caption and product not in skip_words and product not in background_objects:
                return product
        
        # Step 5: Extract nouns after "a/an/the" from main part (skip adjectives & background objects)
        # Pattern to capture up to 3 words after article to handle "wooden bear sculpture"
        pattern = r'\b(?:a|an|the)\s+((?:\w+\s+){0,2}\w+)'
        matches = re.findall(pattern, main_part)
        for match in matches:
            words = match.strip().split()
            # Return the last word (noun) if not a skip_word or background_object
            for word in reversed(words):
                if word not in skip_words and word not in background_objects and len(word) > 2:
                    return word
        
        # Final fallback
        return "product"

    def build_prompt(self, florence_caption, prompt_template):
        """
        Build dynamic prompt by inserting extracted product type
        """
        product_type = self.extract_product_type(florence_caption)
        
        # Replace {product} placeholder in template
        dynamic_prompt = prompt_template.replace("{product}", product_type)
        
        return (dynamic_prompt,)


NODE_CLASS_MAPPINGS = {
    "DynamicPromptBuilder": DynamicPromptBuilder
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DynamicPromptBuilder": "Dynamic Prompt Builder"
}