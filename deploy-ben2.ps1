# Quick Deploy Script for BEN2 Serverless Worker
# This will initialize git, commit files, and prepare for GitHub push

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "BEN2 Serverless Worker - Quick Deploy" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if git is available
Write-Host "Checking git installation..." -ForegroundColor Yellow
$gitVersion = git --version 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Git found: $gitVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Git not found!" -ForegroundColor Red
    Write-Host "Please install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Step 2: Initialize git repository if needed
if (-not (Test-Path ".git")) {
    Write-Host "Initializing git repository..." -ForegroundColor Yellow
    git init
    git branch -M main
    Write-Host "✓ Git initialized" -ForegroundColor Green
} else {
    Write-Host "✓ Git repository already exists" -ForegroundColor Green
}

Write-Host ""

# Step 3: Show what will be committed
Write-Host "Files to be committed:" -ForegroundColor Yellow
Write-Host "  - Dockerfile.ben2-serverless" -ForegroundColor White
Write-Host "  - .github/workflows/build-ben2-serverless.yml" -ForegroundColor White
Write-Host "  - build-ben2-serverless.ps1 and .sh" -ForegroundColor White
Write-Host "  - .dockerignore" -ForegroundColor White
Write-Host "  - BEN2_SERVERLESS_README.md" -ForegroundColor White
Write-Host "  - .memo/BEN2_*.md" -ForegroundColor White
Write-Host "  - ComfyUI workflows and custom nodes" -ForegroundColor White
Write-Host ""

# Step 4: Stage files
Write-Host "Staging files..." -ForegroundColor Yellow
git add .gitignore
git add Dockerfile.ben2-serverless
git add .github/workflows/build-ben2-serverless.yml
git add build-ben2-serverless.ps1
git add build-ben2-serverless.sh
git add .dockerignore
git add BEN2_SERVERLESS_README.md
git add SETUP_GITHUB.md
git add deploy-ben2.ps1
git add .memo/BEN2_*.md

# Add ComfyUI structure (but models are excluded by .gitignore)
git add ComfyUI/custom_nodes/ComfyUI_BEN2_ONNX/
git add ComfyUI/custom_nodes/comfyui-florence2/
git add ComfyUI/custom_nodes/ComfyUI_LocalJSONExtractor/
git add ComfyUI/custom_nodes/comfyui-custom-scripts/
git add ComfyUI/custom_nodes/comfyui-kjnodes/
git add ComfyUI/custom_nodes/save_image_no_metadata.py
git add ComfyUI/user/default/workflows/BG_remove_BEN2_simple_1st.json
git add ComfyUI/user/default/workflows/BG_remove_BEN2_simple_2nd.json

Write-Host "✓ Files staged" -ForegroundColor Green
Write-Host ""

# Step 5: Show git status
Write-Host "Git status:" -ForegroundColor Yellow
git status --short
Write-Host ""

# Step 6: Commit
Write-Host "Creating commit..." -ForegroundColor Yellow
git commit -m "Add BEN2 serverless worker - background removal with safety checks

- BEN2 ONNX for background removal
- Florence-2 for image captioning
- NudeNet for NSFW detection
- Llama 3.1 for safety classification
- All models baked into ~9-10 GB Docker image
- GitHub Actions auto-build workflow
- Optimized for RunPod Serverless deployment"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Commit created" -ForegroundColor Green
} else {
    Write-Host "✗ Commit failed or no changes to commit" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next Steps" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Create GitHub repository:" -ForegroundColor White
Write-Host "   - Go to https://github.com/new" -ForegroundColor Gray
Write-Host "   - Name: comfy-ben2-serverless (or your choice)" -ForegroundColor Gray
Write-Host "   - Visibility: Public (for free Actions and GHCR)" -ForegroundColor Gray
Write-Host "   - DON'T initialize with README" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Connect and push:" -ForegroundColor White
Write-Host "   git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git" -ForegroundColor Gray
Write-Host "   git push -u origin main" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Watch build on GitHub:" -ForegroundColor White
Write-Host "   - Go to repository → Actions tab" -ForegroundColor Gray
Write-Host "   - Build takes ~30-60 minutes" -ForegroundColor Gray
Write-Host "   - Creates: ghcr.io/YOUR_USERNAME/comfyui-ben2-serverless:latest" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Deploy to RunPod:" -ForegroundColor White
Write-Host "   - Container Image: ghcr.io/YOUR_USERNAME/comfyui-ben2-serverless:latest" -ForegroundColor Gray
Write-Host "   - GPU: RTX 4090" -ForegroundColor Gray
Write-Host "   - No network volume needed!" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Ready to push! Create your GitHub repo and run the git remote/push commands above." -ForegroundColor Green
