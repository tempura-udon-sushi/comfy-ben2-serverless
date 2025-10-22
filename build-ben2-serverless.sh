#!/bin/bash
# Build script for BEN2 Serverless Worker
# Run this from the project root directory

set -e  # Exit on error

# Configuration
IMAGE_NAME="comfyui-ben2-serverless"
IMAGE_TAG="latest"
REGISTRY="ghcr.io/tempura-udon-sushi"
FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "=========================================="
echo "Building BEN2 Serverless Worker"
echo "=========================================="
echo "Image: ${FULL_IMAGE_NAME}"
echo "Expected size: ~9-10 GB"
echo "Build time: ~30-60 minutes"
echo ""

# Check if we're in the right directory
if [ ! -f "Dockerfile.ben2-serverless" ]; then
    echo "Error: Dockerfile.ben2-serverless not found!"
    echo "Please run this script from the project root directory."
    exit 1
fi

# Check if custom nodes exist
if [ ! -d "ComfyUI/custom_nodes/ComfyUI_BEN2_ONNX" ]; then
    echo "Error: ComfyUI_BEN2_ONNX custom node not found!"
    exit 1
fi

echo "✓ Pre-flight checks passed"
echo ""

# Build the image
echo "🏗️  Starting Docker build..."
echo ""

docker build \
    -f Dockerfile.ben2-serverless \
    -t ${IMAGE_NAME}:${IMAGE_TAG} \
    -t ${FULL_IMAGE_NAME} \
    --progress=plain \
    .

echo ""
echo "=========================================="
echo "✅ Build Complete!"
echo "=========================================="

# Display image info
echo ""
echo "Image size:"
docker images ${IMAGE_NAME}:${IMAGE_TAG} --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

echo ""
echo "=========================================="
echo "Verifying Models in Image"
echo "=========================================="

# Verify models are in the image
echo "Checking BEN2 model..."
docker run --rm ${IMAGE_NAME}:${IMAGE_TAG} ls -lh /comfyui/models/ben2_onnx/BEN2_Base.onnx

echo ""
echo "Checking Llama model..."
docker run --rm ${IMAGE_NAME}:${IMAGE_TAG} ls -lh /comfyui/models/llm/Llama-3.1-8B-Instruct-Q5_K_M.gguf

echo ""
echo "Checking Florence-2 cache..."
docker run --rm ${IMAGE_NAME}:${IMAGE_TAG} ls /comfyui/models/LLM/

echo ""
echo "Total model size:"
docker run --rm ${IMAGE_NAME}:${IMAGE_TAG} du -sh /comfyui/models/

echo ""
echo "=========================================="
echo "Next Steps"
echo "=========================================="
echo ""
echo "1. Test locally (if you have GPU):"
echo "   docker run --gpus all -p 8188:8188 ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""
echo "2. Push to registry:"
echo "   docker push ${FULL_IMAGE_NAME}"
echo ""
echo "3. Deploy to RunPod:"
echo "   - Create new serverless endpoint"
echo "   - Container Image: ${FULL_IMAGE_NAME}"
echo "   - GPU: RTX 4090 (or similar 24GB VRAM)"
echo "   - No network volume needed!"
echo ""
echo "=========================================="
