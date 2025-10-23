# BEN2 Serverless Build Options

You're hitting disk space limits in GitHub Actions. Here are your options:

## 📊 Current Situation

**GitHub Actions ubuntu-latest**:
- Total space: ~70GB
- Free space after OS: ~14GB  
- Your build needs: ~15-20GB (with layers)
- **Result**: Out of space ❌

## ✅ Option 1: More Aggressive Cleanup (RECOMMENDED - Try First)

**Status**: Updated in workflow  
**What it does**: Removes 20+ GB of unused packages
- Removes .NET, Android SDK, LLVM, PHP, MongoDB, MySQL, Azure CLI, Chrome, Firefox, etc.
- Should free up **25-30 GB** total

**To try**:
```powershell
git add .github/workflows/build-ben2-serverless.yml
git commit -m "Add aggressive disk cleanup for GitHub Actions"
git push
```

**Expected result**: Build should complete ✅

---

## ✅ Option 2: Build Minimal Version First (FALLBACK)

If Option 1 still fails, temporarily **skip Llama model** to make build succeed.

**Models included**:
- ✅ BEN2 (~223 MB) - Background removal
- ✅ Florence-2 (~230 MB) - Image captioning  
- ✅ NudeNet (~100 MB) - NSFW detection
- ❌ Llama (~5.4 GB) - Advanced safety (skip for now)

**Total size**: ~4 GB (vs 9-10 GB)

**How to do it**:

### Comment out Llama in Dockerfile:
```dockerfile
# Skip Llama for minimal build - add back after testing
# RUN echo "Downloading Llama-3.1-8B-Instruct-Q5_K_M.gguf..." && \
#     huggingface-cli download bartowski/Meta-Llama-3.1-8B-Instruct-GGUF \
#     --include "Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf" \
#     --local-dir /comfyui/models/llm && \
#     echo "Llama 3.1 model downloaded successfully"
```

### Also comment out llama-cpp-python:
```dockerfile
# Skip for minimal build
# RUN pip install --no-cache-dir llama-cpp-python \
#     --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
```

**Result**: Image builds in ~15 min, ~4 GB final size

**Note**: Simple workflow (BG_remove_BEN2_simple_2nd.json) works fine without Llama!

---

## ✅ Option 3: Use Larger GitHub Actions Runner

**GitHub Actions Large Runners** (if you have access):
- Available on: GitHub Team/Enterprise
- Disk space: Up to 150 GB
- Cost: ~$0.008/min

**To use**:
```yaml
runs-on: ubuntu-latest-8-cores  # or ubuntu-latest-16-cores
```

---

## ✅ Option 4: Build Locally with Docker

**If you install Docker Desktop**:

### 1. Install Docker Desktop for Windows
https://www.docker.com/products/docker-desktop/

### 2. Build locally
```powershell
docker build -f Dockerfile.ben2-serverless -t ghcr.io/tempura-udon-sushi/comfyui-ben2-serverless:latest .
```

### 3. Push to GHCR
```powershell
# Login to GitHub Container Registry
echo YOUR_GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# Push image
docker push ghcr.io/tempura-udon-sushi/comfyui-ben2-serverless:latest
```

**Pros**: Full control, no time limits  
**Cons**: Requires Docker installation, 30-60 min build time locally

---

## ✅ Option 5: Build on RunPod GPU Pod

**Use RunPod itself to build**:

### 1. Launch GPU Pod
- Any GPU (RTX 4090 recommended)
- Ubuntu template
- 100GB disk

### 2. Install Docker (if not present)
```bash
sudo apt-get update
sudo apt-get install -y docker.io
```

### 3. Clone and build
```bash
git clone https://github.com/tempura-udon-sushi/comfy-ben2-serverless.git
cd comfy-ben2-serverless
docker build -f Dockerfile.ben2-serverless -t ghcr.io/tempura-udon-sushi/comfyui-ben2-serverless:latest .
```

### 4. Push to GHCR
```bash
docker login ghcr.io
docker push ghcr.io/tempura-udon-sushi/comfyui-ben2-serverless:latest
```

**Pros**: Plenty of disk space, fast build on GPU  
**Cons**: Costs ~$0.40 for 1-hour pod rental

---

## 📝 My Recommendation

Try in this order:

### 1. **Try Option 1 first** (aggressive cleanup)
- Already implemented
- Just push the updated workflow
- Should work ✅

### 2. **If still fails**: Option 2 (minimal build)
- Comment out Llama temporarily
- Get working image deployed
- Add Llama back in v2

### 3. **If you want full build**: Option 5 (RunPod pod)
- Rent cheap pod for 1 hour
- Build there with plenty of space
- Push to GHCR

---

## 🎯 Quick Decision Guide

**Want it working NOW with minimal hassle?**
→ Option 2 (Minimal build - skip Llama)

**Have GitHub Team/Enterprise?**
→ Option 3 (Large runner)

**Can spend $0.40?**
→ Option 5 (RunPod pod build)

**Want to install Docker locally?**
→ Option 4 (Local build)

**Want to try free solution first?**
→ Option 1 (Aggressive cleanup) - **TRY THIS FIRST!**

---

Let me know which option you'd like to proceed with!
