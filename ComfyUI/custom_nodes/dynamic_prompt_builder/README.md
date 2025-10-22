# Dynamic Prompt Builder with Content Safety

Custom ComfyUI nodes for Minne product photo background removal with content safety checks.

## Nodes

### 1. Dynamic Prompt Builder
Extracts product type from Florence2 caption and builds dynamic prompts for Qwen image editing.

**Features:**
- 200+ Minne product categories (jewelry, bags, clothing, home goods, etc.)
- Smart product type detection from Florence2 captions
- Customizable prompt templates with `{product}` placeholder

**Inputs:**
- `florence_caption` (STRING): Caption from Florence2Run node
- `prompt_template` (STRING): Template with `{product}` placeholder

**Outputs:**
- `dynamic_prompt` (STRING): Generated prompt with product type inserted

**Example:**
```
Input Caption: "A pair of handmade earrings on a red box"
Template: "Cut out the {product} and place it on pure white background..."
Output: "Cut out the earrings and place it on pure white background..."
```

---

### 2. Content Safety Checker ⚠️
Blocks inappropriate content (NSFW, violence) from being processed.

**Features:**
- Detects explicit, suggestive, violent content
- Customizable strict/normal mode
- Stops workflow with clear error message
- Protects your app from abuse

**Inputs:**
- `florence_caption` (STRING): Caption from Florence2Run node
- `strict_mode` (BOOLEAN): 
  - `True` = Block explicit + suggestive content (recommended for public apps)
  - `False` = Block only explicit content (allows swimwear, fashion)

**Outputs:**
- `safe_caption` (STRING): Original caption if safe
- `is_safe` (BOOLEAN): Always True if passes (otherwise raises error)

**Detected Categories:**
- **NSFW Explicit**: nudity, sexual content, explicit imagery
- **NSFW Suggestive**: revealing clothing, provocative poses (strict mode only)
- **Violence Explicit**: blood, gore, death, torture
- **Violence Weapons**: guns, knives, weapons
- **Violence Action**: fighting, attacking, assault
- **Disturbing**: self-harm, abuse, severe injury

**Usage:**
Place between Florence2Run and Dynamic Prompt Builder to filter content before processing.

---

### 3. Content Safety Bypass (Admin Only) 🔒
Allows authorized users to bypass safety checks for legitimate edge cases.

**Inputs:**
- `florence_caption` (STRING): Caption from Florence2Run node
- `bypass_password` (STRING): Admin password

**Security:**
- Change default password in `safety_checker.py` line 133
- Only use for testing or trusted admin accounts
- Not recommended for public-facing apps

---

## Workflow Integration

### Basic Workflow (No Safety Check)
```
[Load Image]
     ↓
[Florence2Run]
     ↓ (caption)
[Dynamic Prompt Builder]
     ↓ (dynamic_prompt)
[TextEncodeQwenImageEdit]
     ↓
[KSampler] → [Save Image]
```

### Recommended Workflow (With Safety Check)
```
[Load Image]
     ↓
[Florence2Run]
     ↓ (caption)
[Content Safety Checker] ← Set strict_mode: True
     ↓ (safe_caption)
[Dynamic Prompt Builder]
     ↓ (dynamic_prompt)
[TextEncodeQwenImageEdit]
     ↓
[KSampler] → [Save Image]
```

### If Unsafe Content Detected
The workflow will **stop immediately** with an error message:
```
⚠️ CONTENT SAFETY WARNING ⚠️

The uploaded image appears to contain inappropriate content.
Category: nsfw_explicit
Detected keywords: nudity, explicit

For safety reasons, this image cannot be processed.
Please upload appropriate product photos only.
```

---

## Configuration

### For Minne App (Recommended Settings)

**Content Safety Checker:**
- `strict_mode`: `True` (blocks all inappropriate content)

**Dynamic Prompt Builder:**
- Default template works well for most products
- Customize for specific use cases if needed

### Customizing Product Categories

Edit `nodes.py` line 33 to add/remove product types:
```python
products = [
    'your_custom_product',
    # ... existing categories
]
```

### Customizing Safety Keywords

Edit `safety_checker.py` line 30 to modify unsafe keywords:
```python
def get_unsafe_keywords(self):
    return {
        'your_category': ['keyword1', 'keyword2'],
        # ... existing categories
    }
```

---

## Use Cases

### ✅ Perfect For:
- E-commerce product photos (Minne, Etsy, etc.)
- Handcraft marketplace listings
- Background removal services
- Automated product photo editing

### ⚠️ Not Suitable For:
- General image editing (use strict_mode=False)
- Art/fashion photography with revealing content
- Medical/educational imagery

---

## Business Integration Tips

### For SaaS/API Service:
1. Always enable `strict_mode=True` for public users
2. Log flagged content for abuse monitoring
3. Consider rate limiting after multiple flags
4. Add user education about acceptable content

### Error Handling in Your App:
```python
try:
    # Run ComfyUI workflow
    result = run_workflow(image)
except ValueError as e:
    if "CONTENT SAFETY WARNING" in str(e):
        # Show user-friendly message
        return "Please upload appropriate product photos"
    else:
        # Handle other errors
        raise
```

### User Communication:
- Be transparent about content filtering
- Provide clear guidelines on acceptable photos
- Offer examples of good product photos
- Add appeal process for false positives

---

## Installation

1. Files are already in: `ComfyUI/custom_nodes/dynamic_prompt_builder/`
2. Restart ComfyUI to load nodes
3. Find nodes in menu: **Add Node → text**

---

## Support

For issues or feature requests related to Minne integration, modify the nodes to fit your specific needs.

---

## License

Same as ComfyUI main project.
