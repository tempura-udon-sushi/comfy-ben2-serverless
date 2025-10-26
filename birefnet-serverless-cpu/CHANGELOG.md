# BiRefNet CPU Serverless - Changelog

## v1.1-cpu (Oct 26, 2025)

### 🐛 Bug Fixes

**Fixed ONNX Runtime pthread_setaffinity_np errors**

**Problem**: 
RunPod logs showed multiple pthread errors when ONNX Runtime tried to set thread affinity on CPUs that don't exist in the container:

```
[E:onnxruntime:Default, env.cc:226 ThreadMain] pthread_setaffinity_np failed for thread: 113, index: 28, mask: {30, }, error code: 22 error msg: Invalid argument. Specify the number of threads explicitly so the affinity is not set.
```

**Root Cause**:
ONNX Runtime was trying to automatically detect and use all available CPUs, attempting to bind threads to specific CPU cores (0-31). However, RunPod CPU containers may have fewer CPUs allocated (e.g., 4-8 vCPUs), causing affinity setting to fail.

**Solution**:
Set explicit thread counts in ONNX session options instead of letting ONNX auto-detect:

```python
# In birefnet_onnx_node.py and ben2_onnx_node.py
sess_options = onnxruntime.SessionOptions()
sess_options.intra_op_num_threads = int(os.environ.get('OMP_NUM_THREADS', '8'))
sess_options.inter_op_num_threads = int(os.environ.get('OMP_NUM_THREADS', '8'))
sess_options.execution_mode = onnxruntime.ExecutionMode.ORT_SEQUENTIAL

self.session = onnxruntime.InferenceSession(
    model_path, 
    sess_options=sess_options, 
    providers=providers
)
```

**Impact**:
- ✅ No more pthread errors in logs
- ✅ Better thread management
- ✅ Respects OMP_NUM_THREADS environment variable (default: 8)
- ✅ Works reliably on containers with any CPU count

**Files Changed**:
- `ComfyUI/custom_nodes/ComfyUI_BEN2_ONNX/birefnet_onnx_node.py`
- `ComfyUI/custom_nodes/ComfyUI_BEN2_ONNX/ben2_onnx_node.py`

---

## Performance Analysis

### Test Results (5 consecutive runs)

| Run | Total Time | Execution Time | Status | Notes |
|-----|------------|----------------|--------|-------|
| 1 | 33s | 27.5s | ✅ | Cold start |
| 2 | **7s** | 0.15s | ✅ | **Warm worker** |
| 3 | 76s | 27.4s | ✅ | Worker deallocated |
| 4 | **5s** | 0.38s | ✅ | **Warm worker** |
| 5 | 35s | 27.2s | ✅ | Normal |

**Key Insights**:
1. **Warm worker performance is incredible**: 0.15-0.38s execution time! 🚀
2. **Total time = Queue time + Execution time**
   - Warm: 5-7s total (mostly queue/networking)
   - Cold: 30-35s total (27s BiRefNet processing)
3. **BiRefNet ONNX processing is consistent**: ~27s regardless of warm/cold
4. **Queue time varies**: 0-50s depending on worker state

### Recommendation

**For consistent performance**:
```
RunPod Endpoint Settings:
- Active Workers: 1 (keep warm)
- Idle Timeout: 120-300s
```

**Trade-off**:
- **Cost**: ~$0.17/hr = $122/month for 1 idle worker
- **Benefit**: 5-7s response time vs 30-35s with cold starts
- **ROI**: Worth it for production with regular traffic

---

## v1.0-cpu (Oct 26, 2025)

### 🎉 Initial Release

**Features**:
- BiRefNet ONNX background removal on CPU
- Docker image: 2.5 GB (vs 13.6 GB for BEN2 full)
- Processing time: 20-40s per image
- Cost: ~$0.0015 per job
- Models included:
  - BiRefNet-general (928 MB)

**Custom Nodes**:
- ComfyUI_BEN2_ONNX (BiRefNet support)
- comfyui-kjnodes (utilities)
- save_image_no_metadata

**Documentation**:
- README.md
- QUEUE_MANAGEMENT.md
- IMPROVEMENTS_SUMMARY.md

**Test Script**:
- BiRefNet_serverless_test_CPU.py with:
  - Error handling
  - Queue time tracking
  - Automatic job cancellation
  - Retry logic

---

## Deployment Instructions

### Update to v1.1-cpu

**Option 1: RunPod Console**
1. Go to your endpoint settings
2. Change container image to: `zerocalory/birefnet-serverless-cpu:v1.1-cpu`
3. Save and redeploy

**Option 2: Keep Latest**
If you're using `:latest` tag, RunPod will pull v1.1 automatically on next worker spin-up.

### Verify Fix

After deployment, check logs - you should see:
```
Loading BiRefNet ONNX model (general) from /comfyui/models/birefnet_onnx/BiRefNet-general.onnx with providers: ['CPUExecutionProvider']
Thread settings: intra=8, inter=8
```

And **NO** pthread_setaffinity_np errors! ✅

---

## Migration Notes

### Breaking Changes
None - fully backward compatible with v1.0

### Configuration Changes
None - uses same environment variables

### Performance Impact
- **Same or slightly better** due to explicit thread management
- **Cleaner logs** without pthread errors
- **More predictable** thread behavior

---

## Known Issues

None currently! 🎉

---

## Roadmap

### Future Improvements
- [ ] Add BiRefNet-general-lite model (faster variant)
- [ ] Implement model caching for faster cold starts
- [ ] Add batch processing support
- [ ] Optimize thread count based on container vCPU count
- [ ] Add health check endpoint
- [ ] Implement metrics collection

---

**Docker Image**: `zerocalory/birefnet-serverless-cpu:v1.1-cpu`  
**Status**: ✅ Production Ready  
**Recommended**: Yes - fixes log errors from v1.0
