# Manual Download Instructions for BiRefNet_HR Models

## Quick Commands

### Method 1: HuggingFace CLI (Recommended)

First, install the CLI if you haven't:
```bash
pip install huggingface_hub
```

Then download both models:

```bash
# BiRefNet_HR (main model)
huggingface-cli download ZhengPeng7/BiRefNet_HR --local-dir "C:\Users\genfp\AI_avatar\Comfy_vanila\ComfyUI\models\birefnet_hr\BiRefNet_HR"

# BiRefNet_HR-matting (matting variant)
huggingface-cli download ZhengPeng7/BiRefNet_HR-matting --local-dir "C:\Users\genfp\AI_avatar\Comfy_vanila\ComfyUI\models\birefnet_hr\BiRefNet_HR-matting"
```

---

### Method 2: Git LFS

First, install Git LFS if you haven't:
```bash
git lfs install
```

Then clone the repositories:

```bash
# BiRefNet_HR
git clone https://huggingface.co/ZhengPeng7/BiRefNet_HR "C:\Users\genfp\AI_avatar\Comfy_vanila\ComfyUI\models\birefnet_hr\BiRefNet_HR"

# BiRefNet_HR-matting
git clone https://huggingface.co/ZhengPeng7/BiRefNet_HR-matting "C:\Users\genfp\AI_avatar\Comfy_vanila\ComfyUI\models\birefnet_hr\BiRefNet_HR-matting"
```

---

### Method 3: Direct Download from Web

1. **BiRefNet_HR**:
   - Visit: https://huggingface.co/ZhengPeng7/BiRefNet_HR/tree/main
   - Click "Files and versions"
   - Download all files to: `C:\Users\genfp\AI_avatar\Comfy_vanila\ComfyUI\models\birefnet_hr\BiRefNet_HR`

2. **BiRefNet_HR-matting**:
   - Visit: https://huggingface.co/ZhengPeng7/BiRefNet_HR-matting/tree/main
   - Click "Files and versions"
   - Download all files to: `C:\Users\genfp\AI_avatar\Comfy_vanila\ComfyUI\models\birefnet_hr\BiRefNet_HR-matting`

---

## Expected Directory Structure

After download, you should have:

```
ComfyUI\models\birefnet_hr\
├── BiRefNet_HR\
│   ├── config.json
│   ├── model.safetensors (or pytorch_model.bin)
│   ├── preprocessor_config.json
│   └── [other files...]
└── BiRefNet_HR-matting\
    ├── config.json
    ├── model.safetensors (or pytorch_model.bin)
    ├── preprocessor_config.json
    └── [other files...]
```

---

## Verification

After download, verify the models:

```bash
cd ComfyUI\custom_nodes\ComfyUI_BEN2_ONNX
python verify_birefnet_models.py
```

You should see:
```
✅ BiRefNet_HR
   Valid (XX files, ~1500 MB)
✅ BiRefNet_HR-matting
   Valid (XX files, ~1500 MB)
```

---

## Troubleshooting

### Problem: "huggingface-cli: command not found"
**Solution**: Install huggingface_hub
```bash
pip install huggingface_hub
```

### Problem: "git lfs: command not found"
**Solution**: Install Git LFS from https://git-lfs.github.com/

### Problem: Download is very slow
**Solution**: 
- Use `huggingface-cli` with resume support
- Download will resume if interrupted
- Each model is ~1.5GB, be patient

### Problem: "Access Denied" or permission errors
**Solution**:
- Run terminal as administrator
- Check folder permissions
- Make sure path doesn't have special characters

### Problem: Model downloaded but verification fails
**Solution**:
- Check if `config.json` exists
- Check if `model.safetensors` or `pytorch_model.bin` exists
- Re-download if files are corrupted

---

## For RunPod / Docker Deployment

Once models are downloaded and verified locally:

1. **Include in Docker image**:
   ```dockerfile
   COPY ComfyUI/models/birefnet_hr /ComfyUI/models/birefnet_hr
   ```

2. **Or mount as volume**:
   ```bash
   -v /path/to/models/birefnet_hr:/ComfyUI/models/birefnet_hr
   ```

3. **Verify in container**:
   ```bash
   ls -la /ComfyUI/models/birefnet_hr/
   ```

---

## Model Information

- **BiRefNet_HR**: General purpose background removal (2048x2048)
- **BiRefNet_HR-matting**: Specialized for matting/portrait (2048x2048)
- **Size**: ~1.5GB per model
- **Format**: Safetensors or PyTorch
- **License**: Check HuggingFace repo for license info
