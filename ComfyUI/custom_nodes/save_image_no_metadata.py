from __future__ import annotations
import torch
import os
import numpy as np
from PIL import Image
import folder_paths
from datetime import datetime


class SaveImageNoMetadata:
    """
    Custom node to save images without any metadata.
    This removes all workflow information and prompts from the saved image file.
    """
    
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "The images to save without metadata."}),
                "filename_prefix": ("STRING", {"default": "Untitled image", "tooltip": "The prefix for the file to save."})
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "image"
    DESCRIPTION = "Saves images without any metadata (no workflow, no prompts)."

    def save_images(self, images, filename_prefix="Untitled image"):
        filename_prefix += self.prefix_append
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(
            filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0]
        )
        results = list()
        
        # Generate timestamp once for this batch
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        for (batch_number, image) in enumerate(images):
            # Convert tensor to numpy array
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            
            # No metadata - this is the key difference from SaveImage
            # We simply don't pass pnginfo parameter
            
            # Use timestamp instead of counter
            if batch_number > 0:
                # For batches, append batch number to timestamp
                file = f"{filename_prefix}_{timestamp}_{batch_number}.png"
            else:
                file = f"{filename_prefix}_{timestamp}.png"
            
            # Save without metadata
            img.save(os.path.join(full_output_folder, file), compress_level=self.compress_level)
            
            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": self.type
            })

        return { "ui": { "images": results } }


# Node registration
NODE_CLASS_MAPPINGS = {
    "SaveImageNoMetadata": SaveImageNoMetadata
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveImageNoMetadata": "Save Image (No Metadata)"
}
