import requests
import json
import base64
from pathlib import Path
from datetime import datetime

# Your RunPod endpoint URL - UPDATE THIS AFTER DEPLOYMENT
ENDPOINT_URL = "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync"
API_KEY = "YOUR_RUNPOD_API_KEY"  # Get from https://www.runpod.io/console/user/settings

print("="*60)
print("BiRefNet Serverless Test - CPU VERSION")
print("="*60)

# Load workflow
workflow_path = "ComfyUI/user/default/workflows/API/BG_remove_BiRefNet_plus_2nd_API.json"
print(f"Loading workflow: {workflow_path}")

with open(workflow_path, "r", encoding="utf-8") as f:
    prompt = json.load(f)

print(f"✓ Workflow loaded ({len(prompt)} nodes)")

# Add timestamp to output filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
if "7" in prompt and prompt["7"]["class_type"] == "SaveImageNoMetadata":
    prompt["7"]["inputs"]["filename_prefix"] = f"birefnet_cpu_{timestamp}"
    print(f"✓ Set output filename prefix: birefnet_cpu_{timestamp}")

# Verify BiRefNet node is set to CPU
if "17" in prompt and prompt["17"]["class_type"] == "BiRefNet_ONNX_RemoveBg":
    prompt["17"]["inputs"]["provider"] = "CPU"
    print(f"✓ BiRefNet provider set to CPU")
    print(f"✓ Model variant: {prompt['17']['inputs']['model_variant']}")

# Load input image
print("\nLoading input image...")
image_path = "test_images/7db25b86b25d358fc3a7ed63f59eba756974b026.jpeg"
with open(image_path, "rb") as img:
    image_data = base64.b64encode(img.read()).decode('utf-8')

print(f"✓ Image loaded: {image_path}")
print(f"✓ Encoded size: {len(image_data)} bytes")

# Update LoadImage node
if "1" in prompt and prompt["1"]["class_type"] == "LoadImage":
    prompt["1"]["inputs"]["image"] = "input_image.png"
    print("✓ Updated LoadImage node to use uploaded image")

# Prepare payload
payload = {
    "input": {
        "workflow": prompt,
        "images": [
            {
                "name": "input_image.png",
                "image": image_data
            }
        ]
    }
}

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

print("\nSending request to RunPod CPU endpoint...")
print(f"Endpoint: {ENDPOINT_URL}")

try:
    # Validate credentials first
    if "YOUR_ENDPOINT_ID" in ENDPOINT_URL or "YOUR_RUNPOD_API_KEY" in API_KEY:
        print("\n❌ Error: Please update ENDPOINT_URL and API_KEY with your actual values!")
        print("\n📝 How to fix:")
        print("  1. Get your API key from: https://www.runpod.io/console/user/settings")
        print("  2. Get your endpoint ID from: https://www.runpod.io/console/serverless")
        print("  3. Update lines 8-9 in this file")
        exit(1)
    
    # Use /run endpoint for async execution
    async_endpoint = ENDPOINT_URL.replace("/runsync", "/run")
    response = requests.post(async_endpoint, json=payload, headers=headers, timeout=30)
    print(f"\n✓ Job submitted!")
    print(f"Status Code: {response.status_code}")
    
    # Handle authentication errors
    if response.status_code == 401:
        print(f"\n❌ Authentication failed!")
        print(f"   - Check your API key is correct")
        print(f"   - Get it from: https://www.runpod.io/console/user/settings")
        exit(1)
    
    if response.status_code != 200:
        print(f"\n❌ Request failed: {response.text}")
        exit(1)
    
    result = response.json()
    job_id = result.get("id")
    print(f"Job ID: {job_id}")
    
    # Poll for result
    endpoint_id = ENDPOINT_URL.split("/v2/")[1].split("/")[0]
    status_endpoint = f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}"
    print("\n⏳ Polling for result (BiRefNet CPU: 20-40s expected)...")
    
    import time
    max_wait = 180  # 3 minutes total
    max_queue_time = 60  # Max time in queue before warning
    max_progress_time = 90  # Max time in IN_PROGRESS before considering stuck (BiRefNet takes ~15s)
    start_time = time.time()
    queue_start_time = None
    progress_start_time = None
    last_status = None
    status_change_count = 0
    
    while time.time() - start_time < max_wait:
        time.sleep(5)
        
        try:
            status_response = requests.get(status_endpoint, headers=headers, timeout=10)
            status_result = status_response.json()
        except requests.exceptions.Timeout:
            elapsed = int(time.time() - start_time)
            print(f"  [{elapsed}s] ⚠️  Status check timeout, retrying...")
            continue
        except Exception as e:
            elapsed = int(time.time() - start_time)
            print(f"  [{elapsed}s] ⚠️  Error checking status: {e}")
            continue
        
        status = status_result.get("status")
        elapsed = int(time.time() - start_time)
        
        # Track status changes
        if status != last_status:
            status_change_count += 1
        
        # Track queue time
        if status == "IN_QUEUE":
            if queue_start_time is None:
                queue_start_time = time.time()
            queue_time = int(time.time() - queue_start_time)
            
            # Reset progress timer
            progress_start_time = None
            
            # Warn if stuck in queue too long
            if queue_time > max_queue_time:
                print(f"  [{elapsed}s] ⚠️  Status: {status} (queued for {queue_time}s - worker may be scaling)")
            else:
                print(f"  [{elapsed}s] Status: {status}")
        
        # Track IN_PROGRESS time to detect stuck jobs
        elif status == "IN_PROGRESS":
            if progress_start_time is None:
                progress_start_time = time.time()
                # Show queue time when starting progress
                if queue_start_time:
                    queue_duration = int(time.time() - queue_start_time)
                    print(f"  [{elapsed}s] ✓ Worker started after {queue_duration}s in queue")
                    queue_start_time = None
            
            progress_time = int(time.time() - progress_start_time)
            
            # Check for stuck job (normal BiRefNet execution is 12-15s, warn after 90s)
            if progress_time > max_progress_time:
                print(f"  [{elapsed}s] 🚨 STUCK: IN_PROGRESS for {progress_time}s (expected ~15s)")
                print(f"       This indicates a desync between client and server")
                print(f"       Cancelling and exiting...")
                
                # Try to cancel the stuck job
                try:
                    cancel_response = requests.post(f"{status_endpoint}/cancel", headers=headers, timeout=5)
                    if cancel_response.status_code == 200:
                        print(f"       ✓ Job cancelled")
                except:
                    pass
                
                print(f"\n💡 Recommendation:")
                print(f"   - Check RunPod console for actual job status")
                print(f"   - Job may have completed but status update failed")
                print(f"   - Try again with fewer concurrent requests")
                break
            elif progress_time > 30:
                # Warn after 30s (2x normal time)
                print(f"  [{elapsed}s] ⚠️  Status: {status} (processing for {progress_time}s, expected ~15s)")
            else:
                print(f"  [{elapsed}s] Status: {status}")
        
        else:
            # Reset both timers for other statuses
            if last_status == "IN_QUEUE" and status not in ["IN_QUEUE", "IN_PROGRESS"]:
                if queue_start_time:
                    queue_duration = int(time.time() - queue_start_time)
                    print(f"  [{elapsed}s] ✓ Completed after {queue_duration}s in queue")
            queue_start_time = None
            progress_start_time = None
            print(f"  [{elapsed}s] Status: {status}")
        
        last_status = status
        
        if status == "COMPLETED":
            print("\n✅ SUCCESS! Workflow completed.")
            
            # Save output images
            output = status_result.get("output", {})
            images = output.get("images", [])
            
            print(f"\n📋 Output info:")
            print(f"  Images count: {len(images)}")
            
            if images:
                print(f"\n💾 Saving {len(images)} output image(s)...")
                output_dir = Path("output_birefnet_cpu")
                output_dir.mkdir(exist_ok=True)
                
                for idx, img_data in enumerate(images):
                    # RunPod returns dict with 'data' key
                    if isinstance(img_data, dict):
                        image_b64 = img_data.get("data", "")
                    else:
                        image_b64 = img_data
                    
                    if image_b64:
                        output_path = output_dir / f"birefnet_cpu_{timestamp}_{idx}.png"
                        decoded_data = base64.b64decode(image_b64)
                        print(f"  Image {idx}: {len(decoded_data)} bytes")
                        with open(output_path, "wb") as f:
                            f.write(decoded_data)
                        print(f"  ✓ Saved: {output_path}")
                    else:
                        print(f"  ⚠️  Image {idx} has no data!")
            
            # Save response for debugging
            response_file = output_dir / f"response_{timestamp}.json"
            with open(response_file, "w") as f:
                json.dump(status_result, f, indent=2)
            print(f"\n📄 Response saved to: {response_file}")
            
            # Show timing breakdown
            total_time = time.time() - start_time
            delay_time = status_result.get("delayTime", 0) / 1000  # Convert ms to seconds
            execution_time = status_result.get("executionTime", 0) / 1000
            
            print(f"\n⏱️  Timing Breakdown:")
            print(f"   Total time: {total_time:.2f}s")
            print(f"   Queue time: {delay_time:.2f}s")
            print(f"   Execution time: {execution_time:.2f}s")
            print(f"   Status changes: {status_change_count}")
            
            break
        
        elif status == "FAILED":
            print(f"\n❌ FAILED: {status_result.get('error', 'Unknown error')}")
            print(f"\nFull Response:")
            print(json.dumps(status_result, indent=2))
            break
    
    else:
        print(f"\n⏰ Timeout after {max_wait}s")
        print(f"Job ID: {job_id}")
        print(f"\n💡 Troubleshooting:")
        print(f"  1. Job may still be processing - check RunPod console")
        print(f"  2. Worker may be scaling - increase 'max_wait' value")
        print(f"  3. Endpoint may be overloaded - try again later")
        print(f"  4. To cancel job, run:")
        print(f"     curl -X POST '{status_endpoint}/cancel' -H 'Authorization: Bearer {API_KEY}'")
        
        # Try to cancel the stuck job
        try:
            cancel_response = requests.post(f"{status_endpoint}/cancel", headers=headers, timeout=5)
            if cancel_response.status_code == 200:
                print(f"\n✓ Job cancelled automatically")
        except:
            pass  # Ignore cancellation errors

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
