"""
Smart Resize Nodes for Background Removal Models
Optimized for BEN2 (1024²) and BiRefNet (2048²) by maintaining aspect ratio
while targeting optimal total pixel count
"""

import torch
import numpy as np
from PIL import Image
import math


class SmartResizeForModel:
    """
    Smart resize that maintains aspect ratio while targeting optimal pixel count
    for background removal models (1024² or 2048²)
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "target_model": (["1024 (BEN2/BiRefNet)", "2048 (BiRefNet_HR)"], {"default": "2048 (BiRefNet_HR)"}),
                "resize_mode": (["smart", "always_resize", "only_if_needed"], {"default": "smart"}),
            },
            "optional": {
                "interpolation": (["lanczos", "bicubic", "bilinear"], {"default": "lanczos"}),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "INT", "INT")
    RETURN_NAMES = ("image", "original_width", "original_height")
    FUNCTION = "smart_resize"
    CATEGORY = "image/transform"
    
    def tensor2pil(self, image):
        """Convert tensor to PIL Image"""
        return Image.fromarray(np.clip(255. * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))
    
    def pil2tensor(self, image):
        """Convert PIL Image to tensor"""
        return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)
    
    def get_interpolation(self, mode):
        """Get PIL interpolation mode"""
        modes = {
            "lanczos": Image.LANCZOS,
            "bicubic": Image.BICUBIC,
            "bilinear": Image.BILINEAR,
        }
        return modes.get(mode, Image.LANCZOS)
    
    def calculate_target_dimensions(self, orig_width, orig_height, target_pixels):
        """
        Calculate target dimensions maintaining aspect ratio to match target pixel count
        
        Args:
            orig_width: Original image width
            orig_height: Original image height
            target_pixels: Target total pixel count (e.g., 1024*1024 or 2048*2048)
        
        Returns:
            (new_width, new_height) maintaining aspect ratio with total pixels ≈ target_pixels
        """
        aspect_ratio = orig_width / orig_height
        
        # Calculate dimensions: w * h = target_pixels and w/h = aspect_ratio
        # So: w = aspect_ratio * h
        # Therefore: aspect_ratio * h² = target_pixels
        # h = sqrt(target_pixels / aspect_ratio)
        
        new_height = math.sqrt(target_pixels / aspect_ratio)
        new_width = aspect_ratio * new_height
        
        # Round to even numbers for better compatibility
        new_width = int(round(new_width / 2) * 2)
        new_height = int(round(new_height / 2) * 2)
        
        return new_width, new_height
    
    def smart_resize(self, image, target_model="2048 (BiRefNet_HR)", 
                     resize_mode="smart", interpolation="lanczos"):
        """
        Smart resize maintaining aspect ratio while targeting optimal pixel count
        """
        batch_size = image.shape[0]
        output_images = []
        interp_mode = self.get_interpolation(interpolation)
        
        # Determine target pixel count based on model
        if "1024" in target_model:
            target_pixels = 1024 * 1024  # 1,048,576
            model_name = "1024"
        else:  # 2048
            target_pixels = 2048 * 2048  # 4,194,304
            model_name = "2048"
        
        # Process first image to get original dimensions
        first_pil = self.tensor2pil(image[0])
        orig_width, orig_height = first_pil.size
        orig_pixels = orig_width * orig_height
        
        # Determine if resize is needed
        should_resize = True
        
        if resize_mode == "only_if_needed":
            # Only resize if significantly different from target (±10% tolerance)
            tolerance = 0.1
            if abs(orig_pixels - target_pixels) / target_pixels < tolerance:
                should_resize = False
        elif resize_mode == "smart":
            # Resize if not close to target
            tolerance = 0.05
            if abs(orig_pixels - target_pixels) / target_pixels < tolerance:
                should_resize = False
        # "always_resize" always resizes
        
        if should_resize:
            new_width, new_height = self.calculate_target_dimensions(
                orig_width, orig_height, target_pixels
            )
            
            print(f"Smart Resize: {orig_width}x{orig_height} ({orig_pixels:,} px) → "
                  f"{new_width}x{new_height} ({new_width*new_height:,} px) "
                  f"[Target: {model_name}² = {target_pixels:,} px]")
        else:
            new_width, new_height = orig_width, orig_height
            print(f"Smart Resize: Keeping original size {orig_width}x{orig_height} "
                  f"({orig_pixels:,} px) - close enough to target {target_pixels:,} px")
        
        # Resize all images in batch
        for i in range(batch_size):
            pil_image = self.tensor2pil(image[i])
            
            if should_resize:
                resized = pil_image.resize((new_width, new_height), interp_mode)
            else:
                resized = pil_image
            
            output_images.append(self.pil2tensor(resized))
        
        final_images = torch.cat(output_images, dim=0)
        
        return (final_images, orig_width, orig_height)


class RestoreOriginalSize:
    """
    Restore image to original dimensions after processing
    Works with output from SmartResizeForModel
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "original_width": ("INT", {"default": 1024, "min": 1, "max": 16384}),
                "original_height": ("INT", {"default": 1024, "min": 1, "max": 16384}),
            },
            "optional": {
                "interpolation": (["lanczos", "bicubic", "bilinear"], {"default": "lanczos"}),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "restore_size"
    CATEGORY = "image/transform"
    
    def tensor2pil(self, image):
        """Convert tensor to PIL Image"""
        return Image.fromarray(np.clip(255. * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))
    
    def pil2tensor(self, image):
        """Convert PIL Image to tensor"""
        return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)
    
    def get_interpolation(self, mode):
        """Get PIL interpolation mode"""
        modes = {
            "lanczos": Image.LANCZOS,
            "bicubic": Image.BICUBIC,
            "bilinear": Image.BILINEAR,
        }
        return modes.get(mode, Image.LANCZOS)
    
    def restore_size(self, image, original_width, original_height, interpolation="lanczos"):
        """Restore to original dimensions"""
        batch_size = image.shape[0]
        output_images = []
        interp_mode = self.get_interpolation(interpolation)
        
        for i in range(batch_size):
            pil_image = self.tensor2pil(image[i])
            current_width, current_height = pil_image.size
            
            if current_width != original_width or current_height != original_height:
                print(f"Restoring size: {current_width}x{current_height} → "
                      f"{original_width}x{original_height}")
                resized = pil_image.resize((original_width, original_height), interp_mode)
            else:
                resized = pil_image
            
            output_images.append(self.pil2tensor(resized))
        
        return (torch.cat(output_images, dim=0),)


NODE_CLASS_MAPPINGS = {
    "SmartResizeForModel": SmartResizeForModel,
    "RestoreOriginalSize": RestoreOriginalSize,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SmartResizeForModel": "Smart Resize (BG Removal)",
    "RestoreOriginalSize": "Restore Original Size",
}
