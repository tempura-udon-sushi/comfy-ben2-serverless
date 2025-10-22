"""
Download BiRefNet_HR models to ComfyUI models directory
For RunPod serverless deployment preparation
"""

import os
import sys

# Add ComfyUI to path
comfy_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, comfy_path)

import folder_paths

try:
    from huggingface_hub import snapshot_download
except ImportError:
    print("Error: huggingface_hub not installed")
    print("Install with: pip install huggingface_hub")
    sys.exit(1)


def verify_model(model_path):
    """Verify if model files exist"""
    required_files = ["config.json"]
    model_files = ["model.safetensors", "pytorch_model.bin", "model.pt"]
    
    # Check config exists
    if not os.path.exists(os.path.join(model_path, "config.json")):
        return False, "config.json not found"
    
    # Check at least one model file exists
    has_model = any(
        os.path.exists(os.path.join(model_path, f)) for f in model_files
    )
    
    if not has_model:
        return False, f"No model file found (looking for: {', '.join(model_files)})"
    
    return True, "Valid"


def download_model(model_variant, repo_id, models_dir):
    """Download model to ComfyUI models directory"""
    model_path = os.path.join(models_dir, model_variant)
    
    if os.path.exists(model_path):
        print(f"✓ Model already exists at: {model_path}")
        return True
    
    print(f"\n{'='*60}")
    print(f"Downloading: {model_variant}")
    print(f"From: {repo_id}")
    print(f"To: {model_path}")
    print(f"{'='*60}\n")
    
    try:
        # Download entire repository
        snapshot_download(
            repo_id=repo_id,
            local_dir=model_path,
            local_dir_use_symlinks=False,
            resume_download=True
        )
        
        print(f"\n✓ Successfully downloaded {model_variant}")
        print(f"  Saved to: {model_path}")
        return True
        
    except Exception as e:
        print(f"\n✗ Failed to download {model_variant}")
        print(f"  Error: {str(e)}")
        print(f"\n  Manual download command:")
        print(f"  huggingface-cli download {repo_id} --local-dir \"{model_path}\"")
        return False


def main():
    # Create BiRefNet_HR models directory
    models_dir = os.path.join(folder_paths.models_dir, "birefnet_hr")
    os.makedirs(models_dir, exist_ok=True)
    
    print("\n" + "="*60)
    print("BiRefNet_HR Model Downloader for RunPod Serverless")
    print("="*60)
    print(f"\nModels directory: {models_dir}\n")
    
    # Define models to download
    models = {
        "BiRefNet_HR": "ZhengPeng7/BiRefNet_HR",
        "BiRefNet_HR-matting": "ZhengPeng7/BiRefNet_HR-matting",
    }
    
    success_count = 0
    failed_models = []
    total_count = len(models)
    
    # Try to download models
    for model_variant, repo_id in models.items():
        model_path = os.path.join(models_dir, model_variant)
        
        # Check if already exists and valid
        if os.path.exists(model_path):
            is_valid, msg = verify_model(model_path)
            if is_valid:
                print(f"✓ {model_variant}: Already downloaded and verified")
                success_count += 1
                continue
            else:
                print(f"⚠ {model_variant}: Exists but invalid ({msg}). Will try to download...")
        
        # Try download
        if download_model(model_variant, repo_id, models_dir):
            # Verify after download
            is_valid, msg = verify_model(model_path)
            if is_valid:
                success_count += 1
            else:
                print(f"⚠ Downloaded but verification failed: {msg}")
                failed_models.append((model_variant, repo_id, model_path))
        else:
            failed_models.append((model_variant, repo_id, model_path))
    
    print(f"\n{'='*60}")
    print(f"Download Summary: {success_count}/{total_count} successful")
    print(f"{'='*60}\n")
    
    if success_count == total_count:
        print("✓ All models ready for RunPod serverless deployment!")
        print(f"\nModels location: {models_dir}")
        print("\nFor Docker deployment, include this directory in your image.")
    else:
        print(f"⚠ {len(failed_models)} model(s) need manual download\n")
        print("="*60)
        print("MANUAL DOWNLOAD INSTRUCTIONS")
        print("="*60)
        
        for model_variant, repo_id, model_path in failed_models:
            print(f"\n📥 {model_variant}:")
            print(f"\n   Method 1 - Using HuggingFace CLI (Recommended):")
            print(f"   huggingface-cli download {repo_id} --local-dir \"{model_path}\"\n")
            
            print(f"   Method 2 - Using Git LFS:")
            print(f"   git lfs install")
            print(f"   git clone https://huggingface.co/{repo_id} \"{model_path}\"\n")
            
            print(f"   Method 3 - Direct from Web:")
            print(f"   Visit: https://huggingface.co/{repo_id}/tree/main")
            print(f"   Download all files to: {model_path}\n")
        
        print("="*60)
        print("\nAfter manual download, run this script again to verify.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
