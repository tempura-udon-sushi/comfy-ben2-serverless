# BiRefNet Serverless Worker - CPU Version
# Fast background removal using BiRefNet ONNX models

FROM runpod/worker-comfyui:5.4.1-base

# ============================================================================
# STAGE 1: System Dependencies
# ============================================================================

WORKDIR /comfyui

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# STAGE 2: Copy Custom Nodes
# ============================================================================

# Copy ComfyUI_BEN2_ONNX (includes BiRefNet support)
COPY ComfyUI/custom_nodes/ComfyUI_BEN2_ONNX /comfyui/custom_nodes/ComfyUI_BEN2_ONNX

# Copy utility nodes
COPY ComfyUI/custom_nodes/comfyui-kjnodes /comfyui/custom_nodes/comfyui-kjnodes
COPY ComfyUI/custom_nodes/save_image_no_metadata.py /comfyui/custom_nodes/save_image_no_metadata.py

# Note: Workflow is sent via API, no need to copy into image

# ============================================================================
# STAGE 3: Install Python Dependencies
# ============================================================================

# Install dependencies for custom nodes
RUN pip install --no-cache-dir \
    onnxruntime>=1.18.0 \
    onnx>=1.15.0 \
    opencv-python-headless>=4.8.0 \
    pillow>=10.0.0 \
    numpy>=1.24.0

# ============================================================================
# STAGE 4: Download BiRefNet Models
# ============================================================================

# Download BiRefNet ONNX models
RUN mkdir -p /comfyui/models/birefnet_onnx && \
    echo "Downloading BiRefNet model..." && \
    \
    # BiRefNet-general (main model, ~928MB)
    wget --progress=bar:force:noscroll \
        -O /comfyui/models/birefnet_onnx/BiRefNet-general.onnx \
        https://huggingface.co/onnx-community/BiRefNet-ONNX/resolve/main/onnx/model.onnx && \
    \
    echo "==========================" && \
    echo "BiRefNet model downloaded:" && \
    ls -lh /comfyui/models/birefnet_onnx/ && \
    du -sh /comfyui/models/birefnet_onnx/ && \
    echo "==========================" && \
    # Set permissions
    chmod -R 755 /comfyui/models/birefnet_onnx && \
    chown -R root:root /comfyui

# ============================================================================
# STAGE 5: Install CPU-only PyTorch & Environment
# ============================================================================

# CRITICAL: Install CPU-only PyTorch to prevent CUDA errors
RUN pip uninstall -y torch torchvision torchaudio && \
    pip install --no-cache-dir \
    torch==2.5.0+cpu \
    torchvision==0.20.0+cpu \
    torchaudio==2.5.0+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# CPU-specific environment
ENV CUDA_VISIBLE_DEVICES="" \
    FORCE_CUDA=0 \
    PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=8 \
    MKL_NUM_THREADS=8

# Copy CPU-optimized start script
COPY birefnet-serverless-cpu/start_cpu.sh /start.sh
RUN chmod +x /start.sh

# Metadata
LABEL build.date="2025-10-26" \
      version="1.0-cpu" \
      model="BiRefNet-ONNX" \
      variants="general,general-lite" \
      pytorch="cpu-only"

# Use CPU-optimized start script
CMD ["/start.sh"]
