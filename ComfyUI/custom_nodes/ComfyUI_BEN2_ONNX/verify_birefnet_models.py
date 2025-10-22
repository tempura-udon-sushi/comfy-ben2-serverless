"""
Verify BiRefNet_HR models are properly downloaded
Run this after manual download to confirm everything is correct
"""

import os
import sys

# Add ComfyUI to path
comfy_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, comfy_path)

import folder_paths


def verify_model(model_path):
    """Verify if model files exist"""
    if not os.path.exists(model_path):
        return False, "Directory does not exist"
    
    required_files = ["config.json"]
    model_files = ["model.safetensors", "pytorch_model.bin", "model.pt"]
    
    # Check config exists
    config_path = os.path.join(model_path, "config.json")
    if not os.path.exists(config_path):
        return False, "config.json not found"
    
    # Check at least one model file exists
    found_model_files = [f for f in model_files if os.path.exists(os.path.join(model_path, f))]
    
    if not found_model_files:
        return False, f"No model file found (looking for: {', '.join(model_files)})"
    
    # Get directory size
    total_size = 0
    file_count = 0
    for root, dirs, files in os.walk(model_path):
        for file in files:
            fp = os.path.join(root, file)
            total_size += os.path.getsize(fp)
            file_count += 1
    
    size_mb = total_size / (1024 * 1024)
    
    return True, f"Valid ({file_count} files, {size_mb:.1f} MB, model: {', '.join(found_model_files)})"


def main():
    models_dir = os.path.join(folder_paths.models_dir, "birefnet_hr")
    
    print("\n" + "="*60)
    print("BiRefNet_HR Model Verification")
    print("="*60)
    print(f"\nModels directory: {models_dir}\n")
    
    if not os.path.exists(models_dir):
        print(f"❌ Models directory does not exist!")
        print(f"   Please create: {models_dir}")
        print(f"   Then download models to this location.")
        return 1
    
    # Check for expected models
    expected_models = ["BiRefNet_HR", "BiRefNet_HR-matting"]
    
    valid_count = 0
    
    print("Checking models...\n")
    
    for model_name in expected_models:
        model_path = os.path.join(models_dir, model_name)
        is_valid, msg = verify_model(model_path)
        
        if is_valid:
            print(f"✅ {model_name}")
            print(f"   {msg}")
            print(f"   Path: {model_path}\n")
            valid_count += 1
        else:
            print(f"❌ {model_name}")
            print(f"   {msg}")
            print(f"   Path: {model_path}\n")
    
    print("="*60)
    print(f"Verification Summary: {valid_count}/{len(expected_models)} models valid")
    print("="*60)
    
    if valid_count == len(expected_models):
        print("\n✅ All models are ready!")
        print("You can now use BiRefNet_HR nodes in ComfyUI.")
        return 0
    else:
        print(f"\n⚠ {len(expected_models) - valid_count} model(s) missing or invalid")
        print("Please download manually using:")
        print("\nMethod 1 - HuggingFace CLI:")
        for model_name in expected_models:
            model_path = os.path.join(models_dir, model_name)
            if not verify_model(model_path)[0]:
                repo_id = f"ZhengPeng7/{model_name}"
                print(f'  huggingface-cli download {repo_id} --local-dir "{model_path}"')
        
        print("\nMethod 2 - Git LFS:")
        for model_name in expected_models:
            model_path = os.path.join(models_dir, model_name)
            if not verify_model(model_path)[0]:
                repo_id = f"ZhengPeng7/{model_name}"
                print(f'  git clone https://huggingface.co/{repo_id} "{model_path}"')
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
