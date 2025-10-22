"""
Image Resize Utility Nodes for ComfyUI
Useful for preparing images for background removal and scaling outputs
"""

import torch
import numpy as np
from PIL import Image


class ImageResizeForProcessing:
    """
    Resize images to specific resolutions (512, 1024, 2048, etc.)
    Useful for preparing images before background removal processing
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "target_resolution": (["512", "768", "1024", "1280", "1536", "2048", "custom"], {"default": "1024"}),
            },
            "optional": {
                "custom_width": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 64}),
                "custom_height": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 64}),
                "resize_mode": (["stretch", "fit", "fill"], {"default": "fit"}),
                "interpolation": (["bilinear", "bicubic", "nearest", "lanczos"], {"default": "bilinear"}),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "resize_image"
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
            "bilinear": Image.BILINEAR,
            "bicubic": Image.BICUBIC,
            "nearest": Image.NEAREST,
            "lanczos": Image.LANCZOS,
        }
        return modes.get(mode, Image.BILINEAR)
    
    def resize_image(self, image, target_resolution="1024", custom_width=1024, custom_height=1024,
                     resize_mode="fit", interpolation="bilinear"):
        """Resize image to target resolution"""
        batch_size = image.shape[0]
        output_images = []
        
        # Determine target size
        if target_resolution == "custom":
            target_width = custom_width
            target_height = custom_height
        else:
            size = int(target_resolution)
            target_width = size
            target_height = size
        
        interp_mode = self.get_interpolation(interpolation)
        
        for i in range(batch_size):
            pil_image = self.tensor2pil(image[i])
            orig_width, orig_height = pil_image.size
            
            if resize_mode == "stretch":
                # Simply stretch to target size
                resized = pil_image.resize((target_width, target_height), interp_mode)
            
            elif resize_mode == "fit":
                # Fit inside target size, maintain aspect ratio
                pil_image.thumbnail((target_width, target_height), interp_mode)
                resized = pil_image
            
            elif resize_mode == "fill":
                # Fill target size, crop if needed, maintain aspect ratio
                aspect_ratio = orig_width / orig_height
                target_aspect = target_width / target_height
                
                if aspect_ratio > target_aspect:
                    # Image is wider, scale by height
                    new_height = target_height
                    new_width = int(target_height * aspect_ratio)
                else:
                    # Image is taller, scale by width
                    new_width = target_width
                    new_height = int(target_width / aspect_ratio)
                
                pil_image = pil_image.resize((new_width, new_height), interp_mode)
                
                # Crop to target size (center crop)
                left = (new_width - target_width) // 2
                top = (new_height - target_height) // 2
                resized = pil_image.crop((left, top, left + target_width, top + target_height))
            
            output_images.append(self.pil2tensor(resized))
        
        return (torch.cat(output_images, dim=0),)


class ImageResizeToReference:
    """
    Resize images to match reference image size or apply scale factors
    Useful for scaling background removal outputs
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "scale_mode": (["reference", "scale_factor", "dimensions"], {"default": "reference"}),
            },
            "optional": {
                "reference_image": ("IMAGE",),
                "scale_factor": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 8.0, "step": 0.1}),
                "target_width": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 64}),
                "target_height": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 64}),
                "interpolation": (["bilinear", "bicubic", "nearest", "lanczos"], {"default": "lanczos"}),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "resize_to_reference"
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
            "bilinear": Image.BILINEAR,
            "bicubic": Image.BICUBIC,
            "nearest": Image.NEAREST,
            "lanczos": Image.LANCZOS,
        }
        return modes.get(mode, Image.LANCZOS)
    
    def resize_to_reference(self, image, scale_mode="reference", reference_image=None,
                           scale_factor=1.0, target_width=1024, target_height=1024,
                           interpolation="lanczos"):
        """Resize image based on mode"""
        batch_size = image.shape[0]
        output_images = []
        interp_mode = self.get_interpolation(interpolation)
        
        for i in range(batch_size):
            pil_image = self.tensor2pil(image[i])
            orig_width, orig_height = pil_image.size
            
            if scale_mode == "reference":
                # Match reference image size
                if reference_image is not None:
                    ref_idx = min(i, reference_image.shape[0] - 1)
                    ref_pil = self.tensor2pil(reference_image[ref_idx])
                    new_width, new_height = ref_pil.size
                else:
                    # No reference, keep original size
                    new_width, new_height = orig_width, orig_height
            
            elif scale_mode == "scale_factor":
                # Apply scale factor
                new_width = int(orig_width * scale_factor)
                new_height = int(orig_height * scale_factor)
            
            elif scale_mode == "dimensions":
                # Use explicit dimensions
                new_width = target_width
                new_height = target_height
            
            # Resize
            resized = pil_image.resize((new_width, new_height), interp_mode)
            output_images.append(self.pil2tensor(resized))
        
        return (torch.cat(output_images, dim=0),)


class ImageScaleByFactor:
    """
    Quick scale by common factors (0.5x, 1x, 1.5x, 2x, etc.)
    Convenient for common scaling operations
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "scale_factor": (["0.25x", "0.5x", "0.75x", "1x", "1.25x", "1.5x", "2x", "3x", "4x"], {"default": "1x"}),
                "interpolation": (["bilinear", "bicubic", "nearest", "lanczos"], {"default": "lanczos"}),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "scale_image"
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
            "bilinear": Image.BILINEAR,
            "bicubic": Image.BICUBIC,
            "nearest": Image.NEAREST,
            "lanczos": Image.LANCZOS,
        }
        return modes.get(mode, Image.LANCZOS)
    
    def scale_image(self, image, scale_factor="1x", interpolation="lanczos"):
        """Scale image by factor"""
        # Parse scale factor
        factor = float(scale_factor.replace('x', ''))
        
        batch_size = image.shape[0]
        output_images = []
        interp_mode = self.get_interpolation(interpolation)
        
        for i in range(batch_size):
            pil_image = self.tensor2pil(image[i])
            orig_width, orig_height = pil_image.size
            
            new_width = int(orig_width * factor)
            new_height = int(orig_height * factor)
            
            resized = pil_image.resize((new_width, new_height), interp_mode)
            output_images.append(self.pil2tensor(resized))
        
        return (torch.cat(output_images, dim=0),)


NODE_CLASS_MAPPINGS = {
    "ImageResizeForProcessing": ImageResizeForProcessing,
    "ImageResizeToReference": ImageResizeToReference,
    "ImageScaleByFactor": ImageScaleByFactor,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageResizeForProcessing": "Image Resize (Pre-process)",
    "ImageResizeToReference": "Image Resize to Reference",
    "ImageScaleByFactor": "Image Scale by Factor",
}
