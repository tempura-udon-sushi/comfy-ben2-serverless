"""
Output Processing Nodes for Minne Background Removal
Handles background colors, image sizing, and output safety
"""
import torch
import numpy as np
from PIL import Image


class BackgroundColorSelector:
    """
    Replaces white background with custom color or makes transparent
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "background_type": (["white", "light_gray", "cream", "soft_blue", "transparent", "custom"],),
            },
            "optional": {
                "custom_color_hex": ("STRING", {"default": "#FFFFFF"}),
            },
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "change_background"
    CATEGORY = "image/postprocessing"
    
    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def change_background(self, image, background_type, custom_color_hex="#FFFFFF"):
        """
        Change background color of processed image
        Assumes white/light background from Qwen output
        """
        # Convert ComfyUI image format (B, H, W, C) to numpy
        img_np = image.cpu().numpy()
        batch_size = img_np.shape[0]
        processed_images = []
        
        # Color presets
        colors = {
            'white': (255, 255, 255),
            'light_gray': (245, 245, 245),
            'cream': (255, 253, 208),
            'soft_blue': (240, 248, 255),
        }
        
        for i in range(batch_size):
            img = (img_np[i] * 255).astype(np.uint8)
            
            if background_type == 'transparent':
                # For transparent, we need to detect the background
                # Assume white/light areas are background
                # Create alpha channel based on brightness
                gray = np.mean(img, axis=2)
                # Pixels close to white (>240) become transparent
                alpha = np.where(gray > 240, 0, 255).astype(np.uint8)
                
                # Add alpha channel
                img_rgba = np.dstack([img, alpha])
                processed_images.append(img_rgba)
                
            else:
                # Replace white background with chosen color
                if background_type == 'custom':
                    try:
                        target_color = self.hex_to_rgb(custom_color_hex)
                    except:
                        target_color = (255, 255, 255)  # Fallback to white
                else:
                    target_color = colors[background_type]
                
                # Detect white/near-white pixels
                brightness = np.mean(img, axis=2)
                is_background = brightness > 240
                
                # Replace background color
                for c in range(3):
                    img[:, :, c] = np.where(is_background, target_color[c], img[:, :, c])
                
                processed_images.append(img)
        
        # Convert back to ComfyUI format
        processed_np = np.stack(processed_images, axis=0).astype(np.float32) / 255.0
        
        # Handle RGBA vs RGB
        if background_type == 'transparent':
            processed_np = processed_np[:, :, :, :3]  # Remove alpha for ComfyUI compatibility
        
        return (torch.from_numpy(processed_np),)


class ImageSizePresets:
    """
    Resize image to common e-commerce sizes with smart padding
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "size_preset": (["minne_standard", "minne_large", "instagram_square", "instagram_portrait", "custom"],),
                "padding_mode": (["center", "fit", "fill"],),
            },
            "optional": {
                "custom_width": ("INT", {"default": 1024, "min": 256, "max": 4096}),
                "custom_height": ("INT", {"default": 1024, "min": 256, "max": 4096}),
            },
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "resize_image"
    CATEGORY = "image/transform"
    
    def resize_image(self, image, size_preset, padding_mode, custom_width=1024, custom_height=1024):
        """
        Resize image to target size with smart padding
        """
        # Size presets
        sizes = {
            'minne_standard': (640, 640),
            'minne_large': (1200, 1200),
            'instagram_square': (1080, 1080),
            'instagram_portrait': (1080, 1350),
            'custom': (custom_width, custom_height),
        }
        
        target_width, target_height = sizes[size_preset]
        
        # Convert to PIL for easier processing
        img_np = (image.cpu().numpy()[0] * 255).astype(np.uint8)
        img_pil = Image.fromarray(img_np)
        
        orig_width, orig_height = img_pil.size
        
        if padding_mode == "center":
            # Maintain aspect ratio, add padding
            aspect = orig_width / orig_height
            target_aspect = target_width / target_height
            
            if aspect > target_aspect:
                # Image is wider
                new_width = target_width
                new_height = int(target_width / aspect)
            else:
                # Image is taller
                new_height = target_height
                new_width = int(target_height * aspect)
            
            # Resize
            img_resized = img_pil.resize((new_width, new_height), Image.LANCZOS)
            
            # Create canvas with white background
            canvas = Image.new('RGB', (target_width, target_height), (255, 255, 255))
            
            # Paste centered
            x_offset = (target_width - new_width) // 2
            y_offset = (target_height - new_height) // 2
            canvas.paste(img_resized, (x_offset, y_offset))
            
            result = canvas
            
        elif padding_mode == "fit":
            # Fit to dimensions, maintain aspect ratio (may have letterboxing)
            img_pil.thumbnail((target_width, target_height), Image.LANCZOS)
            
            # Create white canvas
            canvas = Image.new('RGB', (target_width, target_height), (255, 255, 255))
            x_offset = (target_width - img_pil.width) // 2
            y_offset = (target_height - img_pil.height) // 2
            canvas.paste(img_pil, (x_offset, y_offset))
            
            result = canvas
            
        else:  # fill
            # Stretch to fill (may distort aspect ratio)
            result = img_pil.resize((target_width, target_height), Image.LANCZOS)
        
        # Convert back to ComfyUI format
        result_np = np.array(result).astype(np.float32) / 255.0
        result_tensor = torch.from_numpy(result_np).unsqueeze(0)
        
        return (result_tensor,)


class OutputQualityChecker:
    """
    Checks output image quality and provides metrics
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "min_quality_score": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 1.0, "step": 0.05}),
            },
        }
    
    RETURN_TYPES = ("IMAGE", "STRING", "FLOAT")
    RETURN_NAMES = ("image", "quality_report", "quality_score")
    FUNCTION = "check_quality"
    CATEGORY = "image/analysis"
    
    def check_quality(self, image, min_quality_score=0.7):
        """
        Analyze output image quality
        Returns image, quality report, and quality score
        """
        img_np = (image.cpu().numpy()[0] * 255).astype(np.uint8)
        
        # Quality checks
        scores = {}
        
        # 1. Check for excessive white space (background)
        white_pixels = np.sum(np.all(img_np > 240, axis=-1))
        total_pixels = img_np.shape[0] * img_np.shape[1]
        white_ratio = white_pixels / total_pixels
        scores['background_ratio'] = min(1.0, white_ratio / 0.7)  # Target 70% background
        
        # 2. Check edge smoothness (detect jagged edges)
        # Simple gradient check
        gray = np.mean(img_np, axis=2)
        grad_x = np.abs(np.gradient(gray, axis=1))
        grad_y = np.abs(np.gradient(gray, axis=0))
        edge_smoothness = 1.0 - min(1.0, np.mean(grad_x + grad_y) / 100)
        scores['edge_smoothness'] = edge_smoothness
        
        # 3. Check color preservation (not too washed out)
        color_std = np.std(img_np)
        color_score = min(1.0, color_std / 50.0)  # Higher std = better color variety
        scores['color_preservation'] = color_score
        
        # 4. Check for product presence (not all white/black)
        non_background = np.sum(np.any(img_np < 240, axis=-1))
        product_presence = min(1.0, non_background / (total_pixels * 0.2))  # At least 20% product
        scores['product_presence'] = product_presence
        
        # Overall quality score (weighted average)
        quality_score = (
            scores['background_ratio'] * 0.2 +
            scores['edge_smoothness'] * 0.3 +
            scores['color_preservation'] * 0.3 +
            scores['product_presence'] * 0.2
        )
        
        # Generate report
        report = f"""
🔍 Output Quality Report
━━━━━━━━━━━━━━━━━━━━━━
Overall Score: {quality_score:.2%}

Metrics:
• Background Ratio: {scores['background_ratio']:.2%}
• Edge Smoothness: {scores['edge_smoothness']:.2%}
• Color Preservation: {scores['color_preservation']:.2%}
• Product Presence: {scores['product_presence']:.2%}

Status: {"✅ PASS" if quality_score >= min_quality_score else "⚠️ NEEDS REVIEW"}
"""
        
        if quality_score < min_quality_score:
            report += f"\n⚠️ Warning: Quality score below threshold ({min_quality_score:.2%})"
            report += "\nSuggestions:"
            if scores['edge_smoothness'] < 0.6:
                report += "\n  • Edges appear jagged - try edge refinement"
            if scores['color_preservation'] < 0.5:
                report += "\n  • Colors may be washed out - check original image quality"
            if scores['product_presence'] < 0.7:
                report += "\n  • Product may be too small or cut off"
        
        return (image, report, quality_score)


NODE_CLASS_MAPPINGS = {
    "BackgroundColorSelector": BackgroundColorSelector,
    "ImageSizePresets": ImageSizePresets,
    "OutputQualityChecker": OutputQualityChecker,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BackgroundColorSelector": "Background Color Selector",
    "ImageSizePresets": "Image Size Presets (Minne)",
    "OutputQualityChecker": "Output Quality Checker",
}
