# BEN2 vs FLUX Serverless Setup - Quick Comparison

Since you already built FLUX with GitHub Actions, here's what's different with BEN2.

## 🔄 Same Process, Different Models

### What Stays the Same
- ✅ **GitHub Actions workflow** - Same auto-build process
- ✅ **GitHub Container Registry** - Same `ghcr.io/tempura-udon-sushi/...`
- ✅ **RunPod Serverless** - Same deployment target
- ✅ **No network volume** - Baked-in approach (like FLUX but you also tested network volume)

### What's Different

| Aspect | FLUX Setup | BEN2 Setup |
|--------|-----------|------------|
| **Image Name** | `comfyui-img2img:latest` | `comfyui-ben2-serverless:latest` |
| **Base Image** | `runpod/worker-comfyui:5.4.1-base` | Same |
| **Total Size** | ~15 GB (FLUX models) | **~9-10 GB** (smaller!) |
| **Models** | FLUX Kontext + Krea (~16 GB) | BEN2 + Florence + NudeNet + Llama (~6 GB) |
| **Use Case** | Image generation (diffusion) | Background removal + safety |
| **Build Time** | ~45-90 min | **~30-60 min** (faster!) |
| **Cold Start** | 15-30s (your optimized) | **15-30s** (expected similar) |

## 📦 Model Comparison

### FLUX Setup Had:
```
flux1-dev-kontext_fp8_scaled.safetensors    ~8 GB
flux1-krea-dev_fp8_scaled.safetensors       ~8 GB
clip_l.safetensors                          ~0.5 GB
t5xxl_fp16.safetensors                      ~5 GB
ae.safetensors                              ~0.3 GB
────────────────────────────────────────────────
TOTAL:                                      ~22 GB
```

### BEN2 Setup Has:
```
BEN2_Base.onnx                              ~223 MB
Florence-2-base                             ~230 MB
NudeNet                                     ~100 MB
Llama-3.1-8B-Instruct-Q5_K_M.gguf          ~5.4 GB
────────────────────────────────────────────────
TOTAL:                                      ~6 GB
```

**BEN2 is 73% smaller!** 🎉

## 🔧 Custom Nodes Comparison

### FLUX Used:
- WAS Node Suite (for ReferenceLatent)
- LoadImageFromUrl
- Standard ComfyUI nodes

### BEN2 Uses:
- ComfyUI_BEN2_ONNX (background removal)
- comfyui-florence2 (vision AI)
- ComfyUI_LocalJSONExtractor (Llama + safety)
- comfyui-custom-scripts (utilities)
- save_image_no_metadata

**Different nodes, different purpose!**

## 🚀 Deployment Differences

### FLUX Deployment:
```yaml
Container Image: ghcr.io/tempura-udon-sushi/comfyui-img2img:latest
GPU: RTX 4090 (24GB VRAM needed)
Network Volume: Optional (you tested both)
Workflows: flux-kontext-with-reference.json
```

### BEN2 Deployment:
```yaml
Container Image: ghcr.io/tempura-udon-sushi/comfyui-ben2-serverless:latest
GPU: RTX 4090 (or 16GB+ for simple workflow)
Network Volume: ❌ Not needed (all baked in)
Workflows: BG_remove_BEN2_simple_1st.json (full)
           BG_remove_BEN2_simple_2nd.json (simple)
```

## 📊 Expected Performance

### FLUX Performance (Your Experience):
- Cold start: 60-180s (network volume) → 15-30s (baked-in)
- Warm worker: 23-45s
- Generation: High quality product photos
- Cost: ~$0.0135-0.0405 per image

### BEN2 Expected Performance:
- Cold start: **15-30s** (baked-in, similar to optimized FLUX)
- Warm worker: **10-20s** (expected)
- Simple workflow: **5-15s**
- Full workflow: **20-40s** (with all safety checks)
- Cost: **~$0.005-0.010** per job (cheaper! Less GPU time)

## 🔐 License Differences

### FLUX:
- FLUX models: Black Forest Labs license (check terms)
- WAS Node Suite: Mixed licenses

### BEN2:
- ✅ **All models permissive licenses**:
  - BEN2: Apache 2.0
  - Florence-2: MIT
  - NudeNet: MIT
  - Llama 3.1: Meta Community License (allows commercial)
- ✅ **Safer for commercial use**

## 🎯 Use Case Comparison

### When to Use FLUX:
- ✅ Image generation
- ✅ Product photography
- ✅ Background replacement with new scene
- ✅ Style transfer
- ✅ High denoise with ReferenceLatent
- ✅ Need 90%+ product preservation

### When to Use BEN2:
- ✅ Background removal (transparent/solid color)
- ✅ Need NSFW filtering
- ✅ Content safety classification
- ✅ Fast batch processing
- ✅ Simpler workflows
- ✅ Lower compute costs

**You can run both!** Different endpoints for different tasks.

## 📝 GitHub Actions - Key Differences

### FLUX Workflow File:
```yaml
# Likely: .github/workflows/build-img2img-docker.yml
name: Build FLUX Docker Image
image: comfyui-img2img:latest
```

### BEN2 Workflow File:
```yaml
# New: .github/workflows/build-ben2-serverless.yml
name: Build BEN2 Serverless Worker
image: comfyui-ben2-serverless:latest
```

**Both can coexist!** They won't conflict.

## 🔄 Migration Notes

### If You Want to Switch from FLUX to BEN2:
1. ❌ **DON'T delete FLUX image** - Keep it as separate endpoint
2. ✅ **Build BEN2 as new image** - Different name
3. ✅ **Create new RunPod endpoint** - Separate from FLUX
4. ✅ **Test both** - They serve different purposes
5. ✅ **Use appropriate endpoint** based on task

### Recommended Setup:
```
Endpoint 1 (FLUX):     ghcr.io/tempura-udon-sushi/comfyui-img2img:latest
  Purpose: Image generation, product photos
  
Endpoint 2 (BEN2):     ghcr.io/tempura-udon-sushi/comfyui-ben2-serverless:latest
  Purpose: Background removal, safety checking
```

## 🚦 Ready to Deploy?

Since you've done this before with FLUX, you just need to:

### Step 1: Commit and Push
```bash
git add Dockerfile.ben2-serverless
git add .github/workflows/build-ben2-serverless.yml
git add build-ben2-serverless.*
git add .dockerignore
git add BEN2_SERVERLESS_README.md
git add .memo/BEN2_*.md
git commit -m "Add BEN2 serverless worker (background removal + safety)"
git push
```

### Step 2: Watch GitHub Actions
Same as FLUX - go to Actions tab, watch build (~30-60 min)

### Step 3: Deploy to RunPod
Create **new endpoint** (keep FLUX endpoint separate):
- Image: `ghcr.io/tempura-udon-sushi/comfyui-ben2-serverless:latest`
- GPU: RTX 4090
- No network volume needed

### Step 4: Test
Run a test workflow to verify background removal works

## 💡 Pro Tips from FLUX Experience

### 1. Version Tagging (Like You Did with FLUX)
Don't overwrite `latest` tag immediately:
```bash
# Build as v1.0 first
git tag v1.0-ben2
git push --tags
```

GitHub Actions will create:
- `latest` tag
- `v1.0-ben2` tag
- Commit SHA tag

### 2. Protect Production Image
Like you did with FLUX (08ed8d0):
- Test new builds with different tags
- Only update `latest` when verified
- Keep old tags as backup

### 3. Monitor Performance
Track metrics like you did with FLUX:
- Cold start times
- Warm execution times
- Cost per job
- Success/failure rates

### 4. Gradual Rollout
- Start with low max workers (1-2)
- Test thoroughly
- Scale up once stable
- Same strategy as FLUX deployment

## ⚠️ Important Notes

### Storage Costs
- FLUX: Network volume cost ~$5/month
- BEN2: $0 extra (all baked in)
- **Save $5/month** if you don't need network volume

### Compute Costs
- BEN2 is **faster** (20-40s vs 60-90s)
- **~50% cheaper** per job
- Better for high-volume batch processing

### When to Use Each

**Use FLUX for**: Image generation, product photography, creative work

**Use BEN2 for**: Background removal, content moderation, batch processing

---

**Bottom Line**: This is the same GitHub Actions process you used for FLUX, just with different models and smaller image size. You already know how to do this! 🚀
