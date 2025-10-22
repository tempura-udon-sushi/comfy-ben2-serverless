"""
Helper script to download the BEN2 ONNX model
"""

import os
import sys
from pathlib import Path

def download_model():
    """Download BEN2_Base.onnx model from HuggingFace"""
    
    # Determine model directory
    script_dir = Path(__file__).parent
    comfyui_dir = script_dir.parent.parent
    models_dir = comfyui_dir / "models" / "ben2_onnx"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = models_dir / "BEN2_Base.onnx"
    
    if model_path.exists():
        print(f"Model already exists at: {model_path}")
        response = input("Re-download? (y/n): ").lower()
        if response != 'y':
            print("Skipping download.")
            return
    
    print("Downloading BEN2_Base.onnx from HuggingFace...")
    print(f"Destination: {model_path}")
    
    try:
        import requests
        from tqdm import tqdm
    except ImportError:
        print("Installing required packages: requests, tqdm")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "tqdm"])
        import requests
        from tqdm import tqdm
    
    url = "https://huggingface.co/PramaLLC/BEN2/resolve/main/BEN2_Base.onnx"
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(model_path, 'wb') as f, tqdm(
            desc="Downloading",
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                size = f.write(chunk)
                pbar.update(size)
        
        print(f"\nModel downloaded successfully to: {model_path}")
        print(f"File size: {model_path.stat().st_size / (1024**2):.2f} MB")
        
    except Exception as e:
        print(f"Error downloading model: {e}")
        print("\nManual download instructions:")
        print(f"1. Download from: {url}")
        print(f"2. Place the file at: {model_path}")
        sys.exit(1)

if __name__ == "__main__":
    download_model()
