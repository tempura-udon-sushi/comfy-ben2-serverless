"""
BiRefNet_HR Background Removal Node for ComfyUI
Uses safetensors/transformers for high-resolution processing (2048x2048)
MIT License - Free for commercial use
"""

import os
import torch
import numpy as np
from PIL import Image, ImageFilter
import folder_paths
import torch.nn.functional as F
from torchvision import transforms

# Register BiRefNet_HR models directory
birefnet_hr_dir = os.path.join(folder_paths.models_dir, "birefnet_hr")
os.makedirs(birefnet_hr_dir, exist_ok=True)
if birefnet_hr_dir not in folder_paths.folder_names_and_paths:
    folder_paths.folder_names_and_paths["birefnet_hr"] = ([birefnet_hr_dir], set())

try:
    from transformers import AutoModelForImageSegmentation
except ImportError:
    print("Warning: transformers not installed. Install with: pip install transformers")
    AutoModelForImageSegmentation = None


class BiRefNet_HR_RemoveBg:
    """
    BiRefNet High Resolution Background Removal Node
    Uses transformers library to load BiRefNet_HR model
    Supports up to 2048x2048 resolution natively
    MIT License
    """
    
    def __init__(self):
        self.model = None
        self.model_name = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "model_variant": (["BiRefNet_HR", "BiRefNet_HR-matting"], {"default": "BiRefNet_HR"}),
            },
            "optional": {
                "background_color": (["none", "white", "black", "red", "green", "blue", "custom"], {"default": "none"}),
                "custom_hex_color": ("STRING", {"default": "#FFFFFF", "multiline": False}),
                "sensitivity": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "mask_blur": ("INT", {"default": 0, "min": 0, "max": 64, "step": 1}),
                "mask_offset": ("INT", {"default": 0, "min": -64, "max": 64, "step": 1}),
                "process_resolution": ("INT", {"default": 2048, "min": 1024, "max": 2560, "step": 256, "tooltip": "Higher resolution for better quality. BiRefNet_HR supports up to 2560x2560"}),
                "use_fp16": ("BOOLEAN", {"default": True, "tooltip": "Use half precision (faster, less VRAM)"}),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "remove_background"
    CATEGORY = "image/preprocessing"
    
    def load_model(self, model_variant, use_fp16=True):
        """Load BiRefNet model from local ComfyUI models directory"""
        if AutoModelForImageSegmentation is None:
            raise ImportError("transformers library not installed. Install with: pip install transformers")
        
        # Only reload if model changed
        if self.model is None or self.model_name != model_variant:
            # Get local model path in ComfyUI models directory
            model_path = os.path.join(birefnet_hr_dir, model_variant)
            
            # Check if model exists locally
            if not os.path.exists(model_path):
                # Try to download from HuggingFace as fallback
                model_repos = {
                    "BiRefNet_HR": "ZhengPeng7/BiRefNet_HR",
                    "BiRefNet_HR-matting": "ZhengPeng7/BiRefNet_HR-matting",
                }
                repo_id = model_repos.get(model_variant, "ZhengPeng7/BiRefNet_HR")
                
                print(f"Model not found at {model_path}")
                print(f"Downloading {model_variant} from HuggingFace: {repo_id}")
                print(f"This will be saved to: {model_path}")
                print("For RunPod serverless, pre-download models to avoid cold start delays!")
                
                try:
                    self.model = AutoModelForImageSegmentation.from_pretrained(
                        repo_id,
                        trust_remote_code=True,
                        cache_dir=model_path
                    )
                except Exception as e:
                    raise RuntimeError(
                        f"Failed to download model from HuggingFace.\n"
                        f"For offline/serverless deployment, download the model manually:\n"
                        f"1. Run: huggingface-cli download {repo_id} --local-dir {model_path}\n"
                        f"2. Or use Python: AutoModelForImageSegmentation.from_pretrained('{repo_id}').save_pretrained('{model_path}')\n"
                        f"Error: {str(e)}"
                    )
            else:
                print(f"Loading BiRefNet_HR model from: {model_path}")
                try:
                    self.model = AutoModelForImageSegmentation.from_pretrained(
                        model_path,
                        trust_remote_code=True,
                        local_files_only=True
                    )
                except Exception as e:
                    raise RuntimeError(f"Failed to load BiRefNet_HR model from {model_path}: {str(e)}")
            
            self.model.to(self.device)
            self.model.eval()
            
            # Use FP16 for faster processing
            if use_fp16 and self.device == "cuda":
                self.model = self.model.half()
                print("BiRefNet_HR loaded in FP16 mode")
            else:
                print("BiRefNet_HR loaded in FP32 mode")
            
            self.model_name = model_variant
            
            # Set precision for matmul operations
            torch.set_float32_matmul_precision('high')
    
    def tensor2pil(self, image):
        """Convert tensor to PIL Image"""
        return Image.fromarray(np.clip(255. * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))
    
    def pil2tensor(self, image):
        """Convert PIL Image to tensor"""
        return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)
    
    def parse_hex_color(self, hex_color):
        """Parse hex color to RGB tuple"""
        hex_color = hex_color.strip().lstrip('#')
        
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        
        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return (r, g, b)
        except (ValueError, IndexError):
            print(f"Invalid hex color: {hex_color}, using white as fallback")
            return (255, 255, 255)
    
    def preprocess_image(self, image_tensor, process_resolution, use_fp16):
        """Preprocess image for BiRefNet_HR"""
        pil_image = self.tensor2pil(image_tensor)
        
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        original_size = pil_image.size
        
        # BiRefNet_HR transform
        transform_image = transforms.Compose([
            transforms.Resize((process_resolution, process_resolution)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        
        input_tensor = transform_image(pil_image).unsqueeze(0).to(self.device)
        
        if use_fp16 and self.device == "cuda":
            input_tensor = input_tensor.half()
        
        return input_tensor, pil_image, original_size
    
    def postprocess_mask(self, result_tensor, original_size):
        """Postprocess model output to get mask"""
        # BiRefNet returns list of predictions, take the last one
        if isinstance(result_tensor, list):
            result = result_tensor[-1]
        else:
            result = result_tensor
        
        # Apply sigmoid and move to CPU
        result = result.sigmoid().cpu()
        
        # Remove batch dimension and get first channel
        result = result.squeeze()
        if len(result.shape) == 3:
            result = result[0]
        
        # Resize to original size
        w, h = original_size
        result = F.interpolate(
            result.unsqueeze(0).unsqueeze(0),
            size=(h, w),
            mode='bilinear',
            align_corners=False
        ).squeeze()
        
        # Normalize to [0, 1]
        ma = torch.max(result)
        mi = torch.min(result)
        if ma > mi:
            result = (result - mi) / (ma - mi)
        
        # Convert to numpy array [0, 255]
        mask_array = (result * 255).cpu().data.numpy().astype(np.uint8)
        
        return mask_array
    
    def remove_background(self, image, model_variant="BiRefNet_HR", 
                         background_color="none", custom_hex_color="#FFFFFF",
                         sensitivity=1.0, mask_blur=0, mask_offset=0,
                         process_resolution=2048, use_fp16=True):
        """Remove background using BiRefNet_HR model"""
        # Load model
        self.load_model(model_variant, use_fp16)
        
        # Determine background color
        color_presets = {
            "white": (255, 255, 255),
            "black": (0, 0, 0),
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
        }
        
        if background_color == "custom":
            bg_color = self.parse_hex_color(custom_hex_color)
        elif background_color in color_presets:
            bg_color = color_presets[background_color]
        else:
            bg_color = None  # None means transparent (RGBA)
        
        # Process each image in batch
        batch_size = image.shape[0]
        output_images = []
        output_masks = []
        
        for i in range(batch_size):
            # Preprocess
            input_tensor, original_pil, original_size = self.preprocess_image(
                image[i], process_resolution, use_fp16
            )
            
            # Run inference
            with torch.no_grad():
                preds = self.model(input_tensor)
            
            # Postprocess to get mask
            mask_array = self.postprocess_mask(preds, original_size)
            
            # Apply sensitivity adjustment
            mask_tensor = torch.from_numpy(mask_array.astype(np.float32) / 255.0)
            mask_tensor = mask_tensor * (1 + (1 - sensitivity))
            mask_tensor = torch.clamp(mask_tensor, 0, 1)
            mask_array = (mask_tensor.numpy() * 255).astype(np.uint8)
            
            mask_pil = Image.fromarray(mask_array)
            
            # Apply mask blur
            if mask_blur > 0:
                mask_pil = mask_pil.filter(ImageFilter.GaussianBlur(radius=mask_blur))
            
            # Apply mask offset (expand/contract)
            if mask_offset > 0:
                for _ in range(mask_offset):
                    mask_pil = mask_pil.filter(ImageFilter.MaxFilter(3))
            elif mask_offset < 0:
                for _ in range(-mask_offset):
                    mask_pil = mask_pil.filter(ImageFilter.MinFilter(3))
            
            # Create RGBA image with alpha channel
            result_image = original_pil.copy()
            if result_image.mode != 'RGBA':
                result_image = result_image.convert('RGBA')
            result_image.putalpha(mask_pil)
            
            # Handle background based on user choice
            if bg_color is None:
                # Keep RGBA format (4 channels with transparency)
                result_tensor = self.pil2tensor(result_image)
            else:
                # Add solid background color and convert to RGB
                bg_image = Image.new('RGB', result_image.size, bg_color)
                bg_image.paste(result_image, mask=mask_pil)
                result_tensor = self.pil2tensor(bg_image)
            
            # Convert mask to tensor (single channel)
            mask_tensor = torch.from_numpy(mask_array.astype(np.float32) / 255.0).unsqueeze(0).unsqueeze(0)
            
            output_images.append(result_tensor)
            output_masks.append(mask_tensor)
        
        # Stack all results
        final_images = torch.cat(output_images, dim=0)
        final_masks = torch.cat(output_masks, dim=0).squeeze(1)  # Remove channel dimension for mask
        
        return (final_images, final_masks)


NODE_CLASS_MAPPINGS = {
    "BiRefNet_HR_RemoveBg": BiRefNet_HR_RemoveBg
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BiRefNet_HR_RemoveBg": "BiRefNet HR Remove Background"
}
