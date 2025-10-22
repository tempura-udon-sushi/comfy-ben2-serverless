# BEN2 Serverless Worker for RunPod

Self-contained Docker image for background removal workflows with safety checking. All models baked in - no network volume required.

## 🎯 Overview

This serverless worker runs two ComfyUI workflows for background removal:

1. **Full Pipeline** (`BG_remove_BEN2_simple_1st.json`)
   - BEN2 background removal
   - Florence-2 image captioning
   - NudeNet NSFW detection
   - Llama 3.1 multi-domain safety classification
   - Hybrid safety gating

2. **Simple Pipeline** (`BG_remove_BEN2_simple_2nd.json`)
   - BEN2 background removal only
   - Fast processing

## 📦 What's Included

### Models (All Baked In)
- **BEN2_Base.onnx** (223 MB) - Background removal
- **Florence-2-base** (230 MB) - Vision & captioning
- **NudeNet** (100 MB) - NSFW detection
- **Llama-3.1-8B-Instruct-Q5_K_M** (5.4 GB) - Safety classification

**Total**: ~6 GB of models + 3-4 GB base = **~9-10 GB image**

### Custom Nodes
- ComfyUI_BEN2_ONNX
- comfyui-florence2
- ComfyUI_LocalJSONExtractor
- comfyui-custom-scripts
- comfyui-kjnodes
- save_image_no_metadata

## 🚀 Quick Start

### Option 1: Pull Pre-built Image

```bash
docker pull ghcr.io/your-username/comfyui-ben2-serverless:latest
```

### Option 2: Build Locally

**Windows (PowerShell):**
```powershell
.\build-ben2-serverless.ps1
```

**Linux/Mac:**
```bash
chmod +x build-ben2-serverless.sh
./build-ben2-serverless.sh
```

**Manual Build:**
```bash
docker build -f Dockerfile.ben2-serverless -t comfyui-ben2-serverless:latest .
```

Build takes ~30-60 minutes (downloads ~6 GB of models).

## 🎮 Local Testing

If you have an NVIDIA GPU with Docker GPU support:

```bash
docker run --gpus all -p 8188:8188 comfyui-ben2-serverless:latest
```

Then open: http://localhost:8188

## ☁️ Deploy to RunPod Serverless

### Step 1: Push to Registry

**GitHub Container Registry (recommended):**
```bash
# Tag image
docker tag comfyui-ben2-serverless:latest ghcr.io/your-username/comfyui-ben2-serverless:latest

# Login
echo $GITHUB_TOKEN | docker login ghcr.io -u your-username --password-stdin

# Push
docker push ghcr.io/your-username/comfyui-ben2-serverless:latest
```

### Step 2: Create RunPod Endpoint

1. Go to **RunPod** → **Serverless**
2. Click **New Endpoint**
3. Configure:
   - **Name**: BEN2 Background Removal
   - **Container Image**: `ghcr.io/your-username/comfyui-ben2-serverless:latest`
   - **Container Disk**: 20 GB
   - **GPU Type**: RTX 4090 (or 24GB VRAM GPU)
   - **Max Workers**: 3-5
   - **Idle Timeout**: 5 seconds
   - **Network Volume**: ❌ None needed!
   - **Container Start Command**: `/start.sh` (default)

4. Click **Deploy**

### Step 3: Test Endpoint

Get your endpoint ID and API key from RunPod dashboard.

**Test with curl:**
```bash
curl -X POST "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d @test_workflow.json
```

## 📊 Performance Expectations

### Startup Times
- **Cold start**: 15-30 seconds (vs 60-180s with network volume)
- **Warm start**: 5-10 seconds

### Processing Times (RTX 4090)
- **Simple workflow**: 5-15 seconds
- **Full workflow**: 20-40 seconds
  - Background removal: 3-8s
  - Florence-2 captioning: 5-10s
  - NudeNet check: 3-5s
  - Llama safety: 8-15s

### Cost Estimates
- **Per job**: ~$0.005-0.010 (RTX 4090 serverless)
- **Idle time**: $0 (with proper timeout settings)

## 🔧 Customization

### Use Different Llama Model

Edit `Dockerfile.ben2-serverless` and change:

```dockerfile
# For smaller/faster (2.3 GB):
Llama-3.2-3B-Instruct-Q5_K_M.gguf

# For larger/better (7.7 GB):
Llama-3.1-8B-Instruct-Q8_0.gguf
```

### Add Your Own Workflows

1. Place workflow JSON in `ComfyUI/user/default/workflows/`
2. Add COPY command in Dockerfile:
   ```dockerfile
   COPY ComfyUI/user/default/workflows/your_workflow.json /comfyui/user/default/workflows/
   ```

### Modify Custom Nodes

Edit the local custom nodes, then rebuild the image.

## 🐛 Troubleshooting

### Build Issues

**"Model download failed"**
- Check internet connection
- HuggingFace might be rate-limiting - try again later
- Verify URLs in Dockerfile are still valid

**"Out of disk space"**
- Docker build needs ~15-20 GB free space
- Clean old images: `docker system prune -a`

### Runtime Issues

**"CUDA out of memory"**
- Reduce batch size
- Use GPU with more VRAM (24GB recommended)
- Disable some safety checks

**"Model not found"**
- Verify build completed successfully
- Check model verification output during build
- Ensure models weren't excluded by .dockerignore

**"Slow first generation"**
- First run loads models into GPU memory (~10-20s)
- Subsequent runs are faster
- This is normal behavior

## 📈 Comparison with FLUX Setup

| Aspect | FLUX (Network Volume) | BEN2 (All-in-Image) |
|--------|----------------------|---------------------|
| **Storage** | 22 GB on volume | 6 GB in image |
| **Total Size** | 15 GB + volume | 9-10 GB total |
| **Cold Start** | 60-180s | 15-30s ✅ |
| **Setup** | Volume + symlinks | Just image ✅ |
| **Scaling** | Volume bottleneck | Easy horizontal ✅ |
| **Monthly Cost** | +$5 volume fee | $0 extra ✅ |

**Benefits**: Faster, simpler, cheaper, more reliable!

## 📝 Files Overview

```
├── Dockerfile.ben2-serverless    # Main Dockerfile
├── build-ben2-serverless.sh      # Linux/Mac build script
├── build-ben2-serverless.ps1     # Windows build script
├── .dockerignore                 # Excludes unnecessary files
├── .github/workflows/
│   └── build-ben2-serverless.yml # Auto-build on push
└── BEN2_SERVERLESS_README.md     # This file
```

## 🔐 License Notes

All models use permissive licenses:
- **BEN2**: Apache 2.0 ✅
- **Florence-2**: MIT ✅
- **NudeNet**: MIT ✅
- **Llama 3.1**: Meta Community License ✅ (allows commercial use)

Safe for commercial deployment!

## 🆘 Support

### Common Questions

**Q: Can I use a different GPU?**  
A: Yes, but ensure 24GB VRAM for full pipeline. Simple pipeline works with 16GB.

**Q: How do I update models?**  
A: Edit Dockerfile URLs, rebuild, push new image.

**Q: Can I run multiple endpoints?**  
A: Yes! Each endpoint can scale independently.

**Q: What about network volume approach?**  
A: This all-in-image approach is simpler and faster for smaller models like BEN2.

### Getting Help

1. Check logs in RunPod dashboard
2. Test locally with `docker run --gpus all`
3. Verify models with `docker run --rm IMAGE ls /comfyui/models/`
4. Review `.memo/BEN2_Serverless_BuildSpec.md` for details

## 🎉 Success Checklist

- [ ] Docker image builds successfully
- [ ] Image size is ~9-10 GB
- [ ] All models verified in image
- [ ] Pushed to container registry
- [ ] RunPod endpoint created
- [ ] Test workflow runs successfully
- [ ] Cold start time < 30 seconds
- [ ] Background removal quality good
- [ ] Safety checks functioning

## 🚀 Next Steps

1. **Build the image** - Run build script
2. **Push to registry** - Make it accessible
3. **Deploy to RunPod** - Create endpoint
4. **Test thoroughly** - Verify workflows
5. **Monitor performance** - Optimize settings
6. **Scale up** - Add more workers as needed

---

**Built with**: ComfyUI + BEN2 + Florence-2 + NudeNet + Llama 3.1  
**For**: RunPod Serverless deployment  
**Date**: October 2025  
**Version**: 1.0
