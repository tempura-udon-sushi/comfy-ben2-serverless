# Build script for BEN2 Serverless Worker (PowerShell)
# Run this from the project root directory

$ErrorActionPreference = "Stop"

# Configuration
$IMAGE_NAME = "comfyui-ben2-serverless"
$IMAGE_TAG = "latest"
$REGISTRY = "ghcr.io/tempura-udon-sushi"
$FULL_IMAGE_NAME = "${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Building BEN2 Serverless Worker" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Image: $FULL_IMAGE_NAME"
Write-Host "Expected size: ~9-10 GB"
Write-Host "Build time: ~30-60 minutes"
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "Dockerfile.ben2-serverless")) {
    Write-Host "Error: Dockerfile.ben2-serverless not found!" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory." -ForegroundColor Red
    exit 1
}

# Check if custom nodes exist
if (-not (Test-Path "ComfyUI\custom_nodes\ComfyUI_BEN2_ONNX")) {
    Write-Host "Error: ComfyUI_BEN2_ONNX custom node not found!" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Pre-flight checks passed" -ForegroundColor Green
Write-Host ""

# Build the image
Write-Host "🏗️  Starting Docker build..." -ForegroundColor Yellow
Write-Host ""

docker build `
    -f Dockerfile.ben2-serverless `
    -t "${IMAGE_NAME}:${IMAGE_TAG}" `
    -t $FULL_IMAGE_NAME `
    --progress=plain `
    .

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "✅ Build Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# Display image info
Write-Host ""
Write-Host "Image size:"
docker images "${IMAGE_NAME}:${IMAGE_TAG}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Verifying Models in Image" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Verify models are in the image
Write-Host "Checking BEN2 model..."
docker run --rm "${IMAGE_NAME}:${IMAGE_TAG}" ls -lh /comfyui/models/ben2_onnx/BEN2_Base.onnx

Write-Host ""
Write-Host "Checking Llama model..."
docker run --rm "${IMAGE_NAME}:${IMAGE_TAG}" ls -lh /comfyui/models/llm/Llama-3.1-8B-Instruct-Q5_K_M.gguf

Write-Host ""
Write-Host "Checking Florence-2 cache..."
docker run --rm "${IMAGE_NAME}:${IMAGE_TAG}" ls /comfyui/models/LLM/

Write-Host ""
Write-Host "Total model size:"
docker run --rm "${IMAGE_NAME}:${IMAGE_TAG}" du -sh /comfyui/models/

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Next Steps" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Test locally (if you have GPU):"
Write-Host "   docker run --gpus all -p 8188:8188 ${IMAGE_NAME}:${IMAGE_TAG}"
Write-Host ""
Write-Host "2. Push to registry:"
Write-Host "   docker push $FULL_IMAGE_NAME"
Write-Host ""
Write-Host "3. Deploy to RunPod:"
Write-Host "   - Create new serverless endpoint"
Write-Host "   - Container Image: $FULL_IMAGE_NAME"
Write-Host "   - GPU: RTX 4090 (or similar 24GB VRAM)"
Write-Host "   - No network volume needed!"
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
