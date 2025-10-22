# ComfyUI BEN2 & BiRefNet ONNX Background Removal

ComfyUI custom nodes for background removal using **BEN2** and **BiRefNet** ONNX models. This is a **non-GPL alternative** to avoid GPL3 licensing issues.

## Features

### BEN2 ONNX Node
- Uses BEN2 ONNX model for fast, accurate background removal
- Apache 2.0 License - Free for commercial use
- Single model variant

### BiRefNet ONNX Node
- Uses BiRefNet ONNX models for high-quality segmentation
- **MIT License** - Completely free for commercial use
- Multiple model variants:
  - **general**: Balanced performance for general use
  - **portrait**: Optimized for human/portrait matting
  - **general-lite**: Lightweight version for faster processing
  - **matting**: Specialized for image matting tasks
- Fixed 1024x1024 processing (ONNX limitation)

### BiRefNet HR Node ⭐ NEW
- Uses BiRefNet_HR with transformers/safetensors for **native high-resolution** processing
- **MIT License** - Completely free for commercial use
- **2048x2048 native support** (up to 2560x2560)
- Model variants:
  - **BiRefNet_HR**: High-resolution general purpose
  - **BiRefNet_HR-matting**: High-resolution matting
- FP16 support for faster processing on GPU
- Best quality for high-resolution images

### Common Features
- Supports CPU, CUDA, and DirectML execution providers
- Customizable background colors (including hex codes)
- Advanced mask refinement (sensitivity, blur, offset)
- Returns both processed image and alpha mask
- Batch processing support

## Installation

1. Clone or copy this folder to your ComfyUI `custom_nodes` directory:
   ```
   ComfyUI/custom_nodes/ComfyUI_BEN2_ONNX/
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   
   For GPU support (CUDA):
   ```bash
   pip install onnxruntime-gpu
   ```

3. Download the ONNX models:

   ### For BEN2:
   - Download `BEN2_Base.onnx` from: https://huggingface.co/PramaLLC/BEN2/resolve/main/BEN2_Base.onnx
   - Place it in: `ComfyUI/models/ben2_onnx/BEN2_Base.onnx`
   
   ```powershell
   # Windows (PowerShell)
   New-Item -ItemType Directory -Path "ComfyUI/models/ben2_onnx" -Force
   Invoke-WebRequest -Uri "https://huggingface.co/PramaLLC/BEN2/resolve/main/BEN2_Base.onnx" -OutFile "ComfyUI/models/ben2_onnx/BEN2_Base.onnx"
   ```

   ### For BiRefNet (choose the variants you need):
   Create directory: `ComfyUI/models/birefnet_onnx/`
   
   Download ONNX models from HuggingFace and rename them:
   
   **General (recommended):**
   - Download from: https://huggingface.co/onnx-community/BiRefNet-ONNX/resolve/main/onnx/model.onnx
   - Rename to: `BiRefNet-general.onnx`
   - Place in: `ComfyUI/models/birefnet_onnx/`
   
   ```powershell
   # Windows (PowerShell)
   New-Item -ItemType Directory -Path "ComfyUI/models/birefnet_onnx" -Force
   Invoke-WebRequest -Uri "https://huggingface.co/onnx-community/BiRefNet-ONNX/resolve/main/onnx/model.onnx" -OutFile "ComfyUI/models/birefnet_onnx/BiRefNet-general.onnx"
   ```
   
   **Portrait (for human/portrait matting):**
   - Download from: https://huggingface.co/onnx-community/BiRefNet-portrait-ONNX/resolve/main/onnx/model.onnx
   - Rename to: `BiRefNet-portrait.onnx`
   
   **General-Lite (faster, lightweight):**
   - Download from: https://huggingface.co/onnx-community/BiRefNet-general-lite-ONNX/resolve/main/onnx/model.onnx
   - Rename to: `BiRefNet-general-lite.onnx`
   
   **Matting (specialized matting):**
   - Download from: https://huggingface.co/onnx-community/BiRefNet-matting-ONNX/resolve/main/onnx/model.onnx
   - Rename to: `BiRefNet-matting.onnx`

   ### For BiRefNet HR (High Resolution) ⭐
   **No manual download needed!** Models auto-download from HuggingFace on first use.
   
   The node will automatically download from:
   - **BiRefNet_HR**: https://huggingface.co/ZhengPeng7/BiRefNet_HR
   - **BiRefNet_HR-matting**: https://huggingface.co/ZhengPeng7/BiRefNet_HR-matting
   
   Models will be cached in: `~/.cache/huggingface/hub/`
   
   **Sizes:**
   - BiRefNet_HR: ~390 MB (safetensors)
   - BiRefNet_HR-matting: ~390 MB (safetensors)

4. Restart ComfyUI

## Usage

### BEN2 ONNX Node

1. Add the **"BEN2 ONNX Remove Background"** node to your workflow
2. Connect an image input
3. Select execution provider (CPU/CUDA/DirectML)
4. Adjust parameters (background color, sensitivity, blur, offset)
5. Connect the outputs (image + mask)

### BiRefNet ONNX Node

1. Add the **"BiRefNet ONNX Remove Background"** node to your workflow
2. Connect an image input
3. Select **model variant**:
   - **general**: Best for most images
   - **portrait**: Best for people/portraits
   - **general-lite**: Faster processing
   - **matting**: For complex alpha matting
4. Select execution provider (CPU/CUDA/DirectML)
5. Adjust **process_resolution** (512-2048) - Note: most ONNX models use fixed 1024x1024
6. Adjust other parameters (background color, sensitivity, blur, offset)
7. Connect the outputs (image + mask)

### BiRefNet HR Node ⭐ (BEST QUALITY)

1. Add the **"BiRefNet HR Remove Background"** node to your workflow
2. Connect an image input
3. Select **model variant**:
   - **BiRefNet_HR**: High-res general purpose (recommended)
   - **BiRefNet_HR-matting**: High-res matting specialist
4. Adjust **process_resolution** (1024-2560, default: 2048)
   - 2048 = excellent quality
   - 2560 = maximum quality (slower, more VRAM)
5. Toggle **use_fp16** (default: True)
   - True = faster, less VRAM (recommended for GPU)
   - False = slightly better precision, more VRAM
6. Adjust other parameters (background color, sensitivity, blur, offset)
7. Connect the outputs (image + mask)

**First run**: Model will auto-download (~390 MB), this may take a few minutes.

## Inputs

### Common Parameters (Both Nodes)

- **image** (IMAGE): Input image(s) to process
- **provider** (dropdown): Execution provider (CPU/CUDA/DirectML)
- **background_color** (dropdown): Background color option
  - **none**: Transparent background (RGBA output)
  - **white**: White background (#FFFFFF)
  - **black**: Black background (#000000)
  - **red**: Red background (#FF0000)
  - **green**: Green background (#00FF00)
  - **blue**: Blue background (#0000FF)
  - **custom**: Use custom hex color (see below)
- **custom_hex_color** (STRING): Custom background color in hex format (e.g., "#FF5733", "A0D8F1")
  - Only used when background_color is set to "custom"
  - Supports both 6-digit (#RRGGBB) and 3-digit (#RGB) formats
  - With or without # prefix
- **sensitivity** (FLOAT): Adjust mask detection strength (0.0 - 1.0, default: 1.0)
  - Higher values = more aggressive foreground detection
  - Lower values = more conservative, may miss some foreground
  - Use to fine-tune the mask based on your image
- **mask_blur** (INT): Blur radius for mask edges (0 - 64, default: 0)
  - 0 = no blur (sharp edges)
  - Higher values = softer, more feathered edges
  - Useful for natural-looking composites
- **mask_offset** (INT): Expand or contract mask boundary (-64 to 64, default: 0)
  - Positive values = expand mask (include more pixels)
  - Negative values = contract mask (exclude edge pixels)
  - 0 = no adjustment
  - Useful to fix edge artifacts or refine mask boundaries

### BiRefNet-Specific Parameters

- **model_variant** (dropdown): BiRefNet model to use
  - **general**: Balanced performance for most images (default)
  - **portrait**: Optimized for human portraits and people
  - **general-lite**: Lightweight, faster processing
  - **matting**: Specialized for complex alpha matting tasks
- **process_resolution** (INT): Processing resolution (512-2048, default: 1024)
  - Higher values = better quality but slower processing
  - Recommended: 1024 for general use, 2048 for high detail
  - Model input is resized to this resolution before processing

## Outputs

- **image** (IMAGE): Processed image with background removed
  - RGBA format (4 channels) when background_color is "none"
  - RGB format (3 channels) when using any color background
- **mask** (MASK): Alpha mask showing foreground regions

## Examples

### Transparent Background
- Set `background_color` to **"none"**
- Output will be RGBA with transparency

### Preset Colors
- Set `background_color` to **"white"**, **"black"**, **"red"**, **"green"**, or **"blue"**
- No need to modify custom_hex_color

### Custom Hex Colors
- Set `background_color` to **"custom"**
- Set `custom_hex_color` to your desired color:
  - `#FF5733` - Orange
  - `#8B4513` - Brown
  - `#FFC0CB` - Pink
  - `A0D8F1` - Light blue (# is optional)
  - `F0F` - Magenta (short form)

### Fine-tuning the Mask

#### Sensitivity Adjustment
- **Too much background included?** Lower sensitivity (e.g., 0.8)
- **Missing foreground details?** Increase sensitivity (e.g., 1.2 - though max is 1.0 in UI)
- Start with default 1.0 and adjust in 0.1 increments

#### Edge Refinement
- **Sharp edges look too harsh?** Add `mask_blur` (try 2-5 for subtle softening)
- **Need feathered edges for compositing?** Use `mask_blur` 5-15
- **Edge artifacts or fringing?** Contract mask with `mask_offset` -2 to -5

#### Mask Expansion
- **Cutting off too much foreground?** Expand with `mask_offset` 2-5
- **Including too much background at edges?** Contract with `mask_offset` -2 to -5

## Model Information

### BEN2
- **Source**: https://huggingface.co/PramaLLC/BEN2
- **License**: Apache 2.0
- **Size**: ~223 MB
- **Processing**: 1024x1024 fixed resolution
- **Best for**: Fast general-purpose background removal

### BiRefNet (ONNX)
- **Source**: https://huggingface.co/ZhengPeng7/BiRefNet
- **ONNX Source**: https://huggingface.co/onnx-community/BiRefNet-ONNX
- **License**: MIT (completely free!)
- **Sizes**: 
  - General: ~135 MB
  - Portrait: ~135 MB
  - General-Lite: ~70 MB
  - Matting: ~135 MB
- **Processing**: Fixed 1024x1024 (ONNX limitation)
- **Best for**: Fast, high-quality segmentation with ONNX optimization

### BiRefNet_HR (Transformers) ⭐ RECOMMENDED
- **Source**: https://huggingface.co/ZhengPeng7/BiRefNet_HR
- **License**: MIT (completely free!)
- **Sizes**: 
  - BiRefNet_HR: ~390 MB (safetensors)
  - BiRefNet_HR-matting: ~390 MB (safetensors)
- **Processing**: Configurable 1024-2560 (native 2048x2048 support)
- **Features**: FP16 support, auto-download, highest quality
- **Best for**: **Maximum quality**, high-resolution images, professional work

## When to Use Which Model?

### Use BEN2 When:
- ✅ You need **fast processing**
- ✅ General background removal is enough
- ✅ You want a single, simple model
- ✅ Processing speed is priority
- ✅ 1024x1024 is sufficient

### Use BiRefNet ONNX When:
- ⭐ You want **good quality + ONNX speed**
- ⭐ You have limited disk space (~135 MB vs ~390 MB)
- ⭐ You prefer ONNX runtime
- ⭐ 1024x1024 processing is enough
- ⭐ You want model variants (general/portrait/lite/matting)

### Use BiRefNet_HR When: 🏆
- 🥇 You need **THE BEST QUALITY**
- 🥇 Working with **high-resolution images** (2K+)
- 🥇 Complex subjects with **fine details** (hair, fur, transparent objects)
- 🥇 **Professional/commercial work**
- 🥇 You have a **good GPU** (FP16 support)
- 🥇 Specialized **high-res matting** tasks
- 🥇 MIT license is important

**Recommendation**: Use **BiRefNet_HR** for best quality. Use **BiRefNet ONNX general** for speed/quality balance. Use **BEN2** if maximum speed is critical.

## License

This custom node code is provided as-is for use with ComfyUI.
- **BEN2 model**: Apache 2.0 License by PramaLLC
- **BiRefNet models**: MIT License by ZhengPeng7 (completely free!)
- **ONNX Runtime**: MIT License by Microsoft

## Troubleshooting

**Model not found error:**
- Make sure you downloaded `BEN2_Base.onnx` and placed it in `ComfyUI/models/ben2_onnx/`

**CUDA provider not available:**
- Install `onnxruntime-gpu` instead of `onnxruntime`
- Make sure you have CUDA installed on your system

**Out of memory:**
- Switch to CPU provider
- Process smaller batches
- Reduce input image resolution before processing

## Comparison with GPL3 Alternatives

This node avoids GPL3 dependencies by:
- Using ONNX runtime (MIT license)
- Direct model inference without GPL3-licensed libraries
- No dependency on `comfy-easy-use` GPL3 code

## Credits

- BEN2 Model: PramaLLC (https://github.com/PramaLLC/BEN2)
- ONNX Runtime: Microsoft (https://github.com/microsoft/onnxruntime)
