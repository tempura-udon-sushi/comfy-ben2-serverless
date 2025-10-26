"""
BEN2 ONNX Background Removal Node for ComfyUI
Uses ONNX runtime for inference - no GPL3 dependencies
"""

import os
import torch
import numpy as np
from PIL import Image, ImageFilter
import folder_paths
import torch.nn.functional as F

try:
    import onnxruntime
except ImportError:
    print("Warning: onnxruntime not installed. Install with: pip install onnxruntime or onnxruntime-gpu")
    onnxruntime = None


class BEN2_ONNX_RemoveBg:
    """
    BEN2 ONNX Background Removal Node
    Uses the ONNX model from PramaLLC/BEN2 for background removal
    """
    
    def __init__(self):
        self.session = None
        self.model_path = None
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "provider": (["CPU", "CUDA", "DirectML"], {"default": "CPU"}),
            },
            "optional": {
                "background_color": (["none", "white", "black", "red", "green", "blue", "custom"], {"default": "none"}),
                "custom_hex_color": ("STRING", {"default": "#FFFFFF", "multiline": False}),
                "sensitivity": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "mask_blur": ("INT", {"default": 0, "min": 0, "max": 64, "step": 1}),
                "mask_offset": ("INT", {"default": 0, "min": -64, "max": 64, "step": 1}),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "remove_background"
    CATEGORY = "image/preprocessing"
    
    def get_model_path(self):
        """Get the path to the BEN2 ONNX model"""
        model_dir = os.path.join(folder_paths.models_dir, "ben2_onnx")
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, "BEN2_Base.onnx")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"BEN2_Base.onnx not found at {model_path}\n"
                f"Please download from: https://huggingface.co/PramaLLC/BEN2/resolve/main/BEN2_Base.onnx\n"
                f"And place it in: {model_dir}"
            )
        
        return model_path
    
    def load_model(self, provider="CPU"):
        """Load the ONNX model with specified provider"""
        if onnxruntime is None:
            raise ImportError("onnxruntime not installed. Install with: pip install onnxruntime or onnxruntime-gpu")
        
        model_path = self.get_model_path()
        
        # Only reload if model path changed or session doesn't exist
        if self.session is None or self.model_path != model_path:
            providers_map = {
                "CPU": ["CPUExecutionProvider"],
                "CUDA": ["CUDAExecutionProvider", "CPUExecutionProvider"],
                "DirectML": ["DmlExecutionProvider", "CPUExecutionProvider"],
            }
            
            providers = providers_map.get(provider, ["CPUExecutionProvider"])
            
            # Create session options with explicit thread settings
            # This prevents pthread_setaffinity_np errors on containers with limited CPUs
            sess_options = onnxruntime.SessionOptions()
            sess_options.intra_op_num_threads = int(os.environ.get('OMP_NUM_THREADS', '8'))
            sess_options.inter_op_num_threads = int(os.environ.get('OMP_NUM_THREADS', '8'))
            sess_options.execution_mode = onnxruntime.ExecutionMode.ORT_SEQUENTIAL
            
            print(f"Loading BEN2 ONNX model from {model_path} with providers: {providers}")
            print(f"Thread settings: intra={sess_options.intra_op_num_threads}, inter={sess_options.inter_op_num_threads}")
            self.session = onnxruntime.InferenceSession(model_path, sess_options=sess_options, providers=providers)
            self.model_path = model_path
    
    def tensor2pil(self, image):
        """Convert tensor to PIL Image"""
        return Image.fromarray(np.clip(255. * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))
    
    def pil2tensor(self, image):
        """Convert PIL Image to tensor"""
        return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)
    
    def parse_hex_color(self, hex_color):
        """Parse hex color to RGB tuple"""
        # Remove # if present
        hex_color = hex_color.strip().lstrip('#')
        
        # Handle short form (e.g., "FFF" -> "FFFFFF")
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        
        # Convert to RGB
        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return (r, g, b)
        except (ValueError, IndexError):
            print(f"Invalid hex color: {hex_color}, using white as fallback")
            return (255, 255, 255)
    
    def preprocess_image(self, image_tensor):
        """Preprocess image for model input"""
        # Convert ComfyUI tensor format to PIL
        pil_image = self.tensor2pil(image_tensor)
        
        # Convert to RGB if needed
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        original_size = pil_image.size
        
        # Resize to 1024x1024
        resized = pil_image.resize((1024, 1024), Image.BILINEAR)
        
        # Convert to tensor and normalize to [0, 1]
        img_array = np.array(resized).astype(np.float32) / 255.0
        
        # Transpose to CHW format
        img_array = img_array.transpose(2, 0, 1)
        
        # Add batch dimension
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array, pil_image, original_size
    
    def postprocess_mask(self, result_np, original_size):
        """Postprocess model output to get mask"""
        result = torch.from_numpy(result_np)
        
        if len(result.shape) == 3:
            result = result.unsqueeze(0)
        
        # Resize to original size
        w, h = original_size
        result = torch.squeeze(F.interpolate(result, size=(h, w), mode='bilinear'), 0)
        
        # Normalize to [0, 1]
        ma = torch.max(result)
        mi = torch.min(result)
        if ma > mi:
            result = (result - mi) / (ma - mi)
        
        # Convert to numpy array [0, 255]
        mask_array = (result * 255).permute(1, 2, 0).cpu().data.numpy().astype(np.uint8)
        mask_array = np.squeeze(mask_array)
        
        return mask_array
    
    def remove_background(self, image, provider="CPU", background_color="none", custom_hex_color="#FFFFFF", 
                         sensitivity=1.0, mask_blur=0, mask_offset=0):
        """Remove background from image using BEN2 ONNX model"""
        # Load model
        self.load_model(provider)
        
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
            input_data, original_pil, original_size = self.preprocess_image(image[i])
            
            # Run inference
            input_name = self.session.get_inputs()[0].name
            outputs = self.session.run(None, {input_name: input_data})
            
            # Postprocess to get mask
            mask_array = self.postprocess_mask(outputs[0], original_size)
            
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
                # Expand mask
                for _ in range(mask_offset):
                    mask_pil = mask_pil.filter(ImageFilter.MaxFilter(3))
            elif mask_offset < 0:
                # Contract mask
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
    "BEN2_ONNX_RemoveBg": BEN2_ONNX_RemoveBg
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BEN2_ONNX_RemoveBg": "BEN2 ONNX Remove Background"
}
