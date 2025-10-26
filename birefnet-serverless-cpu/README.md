# BiRefNet Serverless Worker - CPU Version

✅ **Fast CPU-based background removal** using BiRefNet ONNX models on RunPod.

**Model**: BiRefNet ONNX (Bilateral Reference Network)  
**Version**: v1.1-cpu (Oct 26, 2025)  
**Purpose**: Production-ready background removal without GPU costs

**Latest Update**: Fixed ONNX Runtime pthread errors - see [CHANGELOG.md](CHANGELOG.md)

---

## 🎯 Why BiRefNet CPU?

- **⚡ Fast**: 20-40 seconds per image on CPU
- **💰 Cost-effective**: ~$0.0012-0.002 per job
- **🎨 High quality**: State-of-the-art segmentation
- **📦 Lightweight**: No AI models, just background removal
- **🚀 Production-ready**: Simpler and faster than BEN2+Llama stack

---

## 📦 What's Inside

### Docker Image
- **Base**: `runpod/worker-comfyui:5.4.1-base`
- **PyTorch**: CPU-only (2.5.0+cpu)
- **Size**: ~2.5 GB (much smaller than BEN2 full stack)

### Models (Pre-loaded)
- **BiRefNet-general** (~400 MB) - High quality, general purpose
- **BiRefNet-general-lite** (~200 MB) - Faster, good quality

### Custom Nodes
- ComfyUI_BEN2_ONNX (includes BiRefNet support)
- comfyui-kjnodes (utilities)
- save_image_no_metadata.py

---

## 🚀 Quick Start

### 1. Build Image

```bash
# From Comfy_vanila directory
cd birefnet-serverless-cpu

# Build
docker build -f Dockerfile -t birefnet-serverless-cpu:v1.1-cpu ..

# Tag for Docker Hub
docker tag birefnet-serverless-cpu:v1.1-cpu YOUR_USERNAME/birefnet-serverless-cpu:v1.1-cpu
docker tag birefnet-serverless-cpu:v1.1-cpu YOUR_USERNAME/birefnet-serverless-cpu:latest

# Push
docker push YOUR_USERNAME/birefnet-serverless-cpu:v1.1-cpu
docker push YOUR_USERNAME/birefnet-serverless-cpu:latest
```

### 2. Deploy to RunPod

1. Go to [RunPod Serverless](https://www.runpod.io/console/serverless)
2. Click **"+ New Endpoint"**
3. Select **CPU Worker Type**
4. Configuration:
   - **Name**: `birefnet-cpu`
   - **Instance**: 4-8 vCPUs, 8-16 GB RAM
   - **Container Image**: `zerocalory/birefnet-serverless-cpu:v1.1-cpu`
   - **Container Disk**: 10 GB
5. Deploy!

### 3. Test

```bash
# Update endpoint ID in test script
python BiRefNet_serverless_test_CPU.py
```

---

## ⚡ Performance

### CPU Performance (4-8 vCPUs)

| Model | Time | Cost/Job | Quality |
|-------|------|----------|---------|
| **BiRefNet-general** | 20-40s | $0.0012-0.002 | ⭐⭐⭐⭐⭐ Excellent |
| **BiRefNet-general-lite** | 15-30s | $0.0009-0.0015 | ⭐⭐⭐⭐ Very Good |

### vs Other Solutions

| Solution | Time | Cost | Use Case |
|----------|------|------|----------|
| **BiRefNet CPU** | 20-40s | $0.0015 | ✅ Production BG removal |
| BEN2 CPU (fast) | 30-40s | $0.0020 | BG removal only |
| BEN2 CPU (full) | 5-8 min | $0.035 | With AI safety check |
| BiRefNet GPU | 3-5s | $0.0008 | High-volume processing |

**Recommendation**: Use BiRefNet CPU for cost-effective production background removal!

---

## 🎨 Model Variants

### BiRefNet-general (Default)
- **Size**: ~400 MB
- **Quality**: Highest
- **Speed**: 20-40s on CPU
- **Best for**: Production, high quality needed

### BiRefNet-general-lite
- **Size**: ~200 MB  
- **Quality**: Very good
- **Speed**: 15-30s on CPU
- **Best for**: High volume, speed priority

To switch models, edit workflow JSON:
```json
{
  "17": {
    "inputs": {
      "model_variant": "general-lite"  // Change to "general-lite"
    }
  }
}
```

---

## 📊 Workflow Structure

```
Input Image
    ↓
SmartResize (to 1024x1024)
    ↓
BiRefNet Background Removal (CPU)
    ↓
Restore Original Size
    ↓
Free Memory
    ↓
Save Output
```

**Total nodes**: 6 (vs 13 in BEN2 full workflow)
**Processing time**: 20-40 seconds
**No AI models**: Just segmentation!

---

## 🔧 Configuration Options

### Background Color

```python
# In workflow JSON, node 17
"background_color": "none"     # Transparent (PNG)
"background_color": "white"    # White background
"background_color": "black"    # Black background
"background_color": "custom"   # Use custom_hex_color
```

### Sensitivity

```python
"sensitivity": 1.0   # Default (0.0 - 1.0)
```
- Higher = more aggressive removal
- Lower = preserve more detail

### Mask Adjustments

```python
"mask_blur": 0       # Blur mask edges (0-64)
"mask_offset": -1    # Expand/contract mask (-64 to 64)
```

---

## 🛠️ Troubleshooting

### Model Not Found Error
```
FileNotFoundError: BiRefNet-general.onnx not found
```

**Solution**: Model download failed during build. Rebuild:
```bash
docker build --no-cache -f Dockerfile -t birefnet-serverless-cpu:v1.0 ..
```

### Slow Performance

**Solutions**:
1. Use `general-lite` model (30% faster)
2. Increase vCPUs to 8
3. Use CPU5 instances (5+ GHz)

### Memory Issues

**Solutions**:
1. Increase RAM to 16 GB
2. Set `unload_models: true` in FreeVRAMInline node
3. Process smaller batches

---

## 💡 Optimization Tips

### 1. Use Lite Model
Switch to `general-lite` for 30% speed boost with minimal quality loss.

### 2. Batch Processing
Process multiple images in one job to amortize startup cost:

```python
payload = {
    "input": {
        "workflow": prompt,
        "images": [
            {"name": "img1.png", "image": img1_b64},
            {"name": "img2.png", "image": img2_b64},
            {"name": "img3.png", "image": img3_b64}
        ]
    }
}
```

### 3. Cache Results
Cache processed images to avoid re-processing duplicates.

### 4. Keep Workers Warm
Set longer idle timeout to keep workers ready.

---

## 📈 Cost Analysis

### 10,000 images/month

| Configuration | Time/Image | Cost/Image | Monthly Cost |
|---------------|------------|------------|--------------|
| 4 vCPUs, general | 35s | $0.0018 | $18 |
| 8 vCPUs, general | 25s | $0.0016 | $16 |
| 8 vCPUs, lite | 20s | $0.0013 | $13 |

**vs GPU (RTX 4090)**:
- Time: 4s
- Cost/Image: $0.0008
- Monthly (10k): $8

**Recommendation**: 
- **Low-medium volume**: Use CPU (cheaper infrastructure)
- **High volume**: Use GPU (faster processing)

---

## 🔗 Related Resources

- **BiRefNet Paper**: [arXiv:2401.17258](https://arxiv.org/abs/2401.17258)
- **ONNX Models**: [HuggingFace - BiRefNet-ONNX](https://huggingface.co/onnx-community/BiRefNet-ONNX)
- **CPU Implementation Guide**: [../ben2-serverless-cpu/CPU_IMPLEMENTATION_GUIDE.md](../ben2-serverless-cpu/CPU_IMPLEMENTATION_GUIDE.md)
- **Test Script**: [../BiRefNet_serverless_test_CPU.py](../BiRefNet_serverless_test_CPU.py)

---

## ✅ Ready for Production

BiRefNet CPU is production-ready for:
- ✅ E-commerce product photography
- ✅ Profile picture background removal
- ✅ Batch image processing
- ✅ Cost-sensitive applications
- ✅ Medium-volume workflows

For high-volume or real-time needs, consider the GPU version.

---

**Built with**: Oct 26, 2025  
**Version**: v1.1-cpu  
**Docker Image**: `zerocalory/birefnet-serverless-cpu:v1.1-cpu`  
**Status**: ✅ Production Ready (pthread errors fixed)
