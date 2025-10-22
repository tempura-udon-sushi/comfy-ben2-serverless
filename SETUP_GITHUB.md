# Setup GitHub & Deploy BEN2 Serverless Worker

Quick guide to get your BEN2 worker deployed via GitHub Actions.

## 📋 Prerequisites

- GitHub account
- Git installed on your machine
- GitHub personal access token (for GHCR)

## 🚀 Step-by-Step Setup

### Step 1: Initialize Git Repository

```powershell
# Navigate to project root (you're already here)
cd C:\Users\genfp\AI_avatar\Comfy_vanila

# Initialize git
git init

# Add .gitignore (important!)
# Create .gitignore file first (see below)
```

### Step 2: Create .gitignore

Create `.gitignore` file to exclude large files:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.venv

# ComfyUI Runtime (exclude large runtime files)
ComfyUI/output/
ComfyUI/input/
ComfyUI/temp/

# Models (we download these in Dockerfile, don't commit)
*.safetensors
*.ckpt
*.pth
*.onnx
*.gguf
*.bin
ComfyUI/models/checkpoints/
ComfyUI/models/vae/
ComfyUI/models/clip/
ComfyUI/models/diffusion_models/
ComfyUI/models/text_encoders/
ComfyUI/models/ben2_onnx/*.onnx
ComfyUI/models/llm/*.gguf
ComfyUI/models/LLM/

# Keep directory structure but not models
!.gitkeep

# Logs
*.log
logs/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Environment
.env
.env.local

# Temporary
*.tmp
tmp/
temp/

# Test files
analyze_workflows.py

# Large images
*.png
*.jpg
*.jpeg
*.gif
input.png
```

### Step 3: Add Files to Git

```powershell
# Add all project files (excluding what's in .gitignore)
git add .

# Check what will be committed
git status

# Commit
git commit -m "Initial commit: BEN2 serverless worker setup"
```

### Step 4: Create GitHub Repository

1. Go to https://github.com
2. Click "New Repository"
3. **Repository name**: `comfy-ben2-serverless` (or your preferred name)
4. **Visibility**: 
   - Public (free GitHub Actions, free GHCR)
   - Private (if you have GitHub Pro)
5. **DON'T** initialize with README (we already have files)
6. Click "Create Repository"

### Step 5: Connect to GitHub

GitHub will show you commands. Use these:

```powershell
# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/comfy-ben2-serverless.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

**Alternative with SSH:**
```powershell
git remote add origin git@github.com:YOUR_USERNAME/comfy-ben2-serverless.git
git push -u origin main
```

### Step 6: Watch GitHub Actions Build

1. Go to your repository on GitHub
2. Click "Actions" tab
3. You'll see "Build BEN2 Serverless Worker" workflow running
4. Click on it to watch progress
5. Build takes ~30-60 minutes

### Step 7: Verify Image in GHCR

After build completes:
1. Go to your GitHub profile
2. Click "Packages"
3. Find `comfyui-ben2-serverless`
4. Image URL: `ghcr.io/YOUR_USERNAME/comfyui-ben2-serverless:latest`

---

## 🎯 Quick Commands Reference

```powershell
# First time setup
git init
git add .
git commit -m "Initial commit: BEN2 serverless worker"
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
git push -u origin main

# Future updates
git add .
git commit -m "Update description"
git push

# Check status
git status

# View commit history
git log --oneline

# Create new branch (for testing)
git checkout -b test-build
git push -u origin test-build
```

---

## 🔧 Troubleshooting

### "fatal: not a git repository"
```powershell
git init
```

### "Permission denied (publickey)"
Use HTTPS instead:
```powershell
git remote set-url origin https://github.com/YOUR_USERNAME/REPO_NAME.git
```

### "Repository not found"
- Check repository exists on GitHub
- Verify username and repo name are correct
- Ensure you have access (private repos)

### GitHub Actions not running
- Check if Actions are enabled in repo settings
- Verify `.github/workflows/` files are committed
- Check workflow file syntax (YAML is indent-sensitive)

### GHCR authentication failed
- Go to GitHub Settings → Developer settings → Personal access tokens
- Create token with `write:packages` and `read:packages` scopes
- Use token when pushing images manually

---

## 🚀 Alternative: Use Existing Git Repo

If you already have a GitHub repo for ComfyUI:

```powershell
# Just add the new files
git add Dockerfile.ben2-serverless
git add .github/workflows/build-ben2-serverless.yml
git add build-ben2-serverless.*
git add .dockerignore
git add BEN2_SERVERLESS_README.md
git add .memo/BEN2_*.md

git commit -m "Add BEN2 serverless worker"
git push
```

---

## 📦 What Gets Built

When you push, GitHub Actions will:

1. ✅ Checkout your code
2. ✅ Set up Docker Buildx
3. ✅ Login to GitHub Container Registry
4. ✅ Build Docker image with all models
5. ✅ Push to `ghcr.io/YOUR_USERNAME/comfyui-ben2-serverless:latest`
6. ✅ Create deployment summary

---

## 🎉 After Build Completes

### Deploy to RunPod

1. **RunPod Dashboard** → **Serverless** → **New Endpoint**

2. **Configuration**:
   ```
   Name: BEN2 Background Removal
   Container Image: ghcr.io/YOUR_USERNAME/comfyui-ben2-serverless:latest
   Container Disk: 20 GB
   GPU Type: RTX 4090
   Max Workers: 3
   Idle Timeout: 5 seconds
   Network Volume: None
   ```

3. **Deploy & Test**

---

## 💡 Tips

### Make Image Public on GHCR

After first build:
1. Go to package on GitHub
2. Package settings → Change visibility → Public
3. Now RunPod can pull without authentication

### Test Locally First (If you have Docker)

```powershell
docker pull ghcr.io/YOUR_USERNAME/comfyui-ben2-serverless:latest
docker run --gpus all -p 8188:8188 ghcr.io/YOUR_USERNAME/comfyui-ben2-serverless:latest
```

### Monitor Build Progress

Watch build in real-time:
- GitHub Actions tab shows live logs
- Each step is collapsible
- Look for model download progress
- Verify final image size (~9-10 GB)

---

**Next**: Once you've pushed to GitHub, the build starts automatically! ⚡
