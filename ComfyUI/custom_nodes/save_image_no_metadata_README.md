# Save Image No Metadata - ComfyUI Custom Node

## Description
This custom node saves images without any metadata embedded in the file. Unlike the default `SaveImage` node in ComfyUI, this node strips all metadata including:
- Workflow information
- Prompt data
- Extra PNG info

This is useful when you want to:
- Share images without revealing your workflow
- Reduce file size slightly
- Keep your prompts and settings private

## Installation
This node is already installed as a standalone `.py` file in your `custom_nodes` directory. ComfyUI will automatically load it on startup.

## Usage
1. Restart ComfyUI (if it's already running)
2. In your workflow, look for the node under **"image"** category
3. The node is named **"Save Image (No Metadata)"**
4. Connect your image output to this node
5. Optionally, customize the filename prefix (default is "ComfyUI_NoMeta")
6. Images will be saved to your ComfyUI output directory without any metadata

## Inputs
- **images**: The images to save (IMAGE type)
- **filename_prefix**: The prefix for the saved files (default: "ComfyUI_NoMeta")

## Outputs
- Saves images to the output directory
- Returns the image list to the UI for preview

## Technical Details
The node works by:
1. Converting the image tensor to a PIL Image
2. Saving it **without** passing the `pnginfo` parameter (which normally contains all metadata)
3. This results in a clean PNG file with no embedded metadata

## Reference
Based on the approach described in: https://blog.xentoo.info/2023/07/23/comfyui-remove-metadata-from-image-files/
