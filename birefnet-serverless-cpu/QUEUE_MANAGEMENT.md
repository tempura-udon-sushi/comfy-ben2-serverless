# RunPod Serverless Queue Management Guide

## Common Issue: Jobs Stuck in IN_QUEUE

### What's Happening?

When you see jobs stuck in `IN_QUEUE` status:
1. **Worker is scaling**: RunPod is spinning up a new container
2. **No workers available**: All workers are busy or deallocated
3. **Cold start**: First request after idle period
4. **Network delay**: Status update lag between client and server

---

## ✅ Solutions & Best Practices

### 1. Keep Workers Warm

**Problem**: Workers deallocate after idle timeout, causing cold starts

**Solution**: Configure endpoint settings

```
RunPod Console → Your Endpoint → Settings:

Idle Timeout: 30 seconds (default)
           → 120 seconds (recommended for testing)
           → 300+ seconds (production with steady traffic)

Active Workers: 0 (default - scales to 0)
             → 1 (keep 1 worker always running)
```

**Cost Impact**:
- 1 worker idle @ $0.17/hr = ~$122/month
- vs Cold start delay + user frustration

**Recommendation**: 
- Testing: Set 1 active worker
- Production: Use based on traffic patterns

---

### 2. Implement Retry Logic

Add exponential backoff for transient failures:

```python
import time

def submit_job_with_retry(payload, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(endpoint, json=payload, headers=headers)
            result = response.json()
            
            if response.status_code == 200:
                return result
            
            # Retry on server errors
            if response.status_code >= 500:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Server error, retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            # Don't retry on client errors
            return result
            
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Request failed: {e}, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
    
    raise Exception(f"Failed after {max_retries} attempts")
```

---

### 3. Queue Time Monitoring

Track how long jobs stay in queue:

```python
def poll_with_queue_monitoring(job_id, max_wait=180, max_queue_time=60):
    start_time = time.time()
    queue_start_time = None
    
    while time.time() - start_time < max_wait:
        status_result = get_status(job_id)
        status = status_result.get("status")
        
        if status == "IN_QUEUE":
            if queue_start_time is None:
                queue_start_time = time.time()
            
            queue_time = time.time() - queue_start_time
            
            # Alert if queue time exceeds threshold
            if queue_time > max_queue_time:
                print(f"⚠️  Job queued for {queue_time:.0f}s")
                print(f"   Consider:")
                print(f"   - Increasing worker count")
                print(f"   - Keeping workers warm")
                print(f"   - Using different endpoint")
                
        elif status == "IN_PROGRESS":
            if queue_start_time:
                queue_duration = time.time() - queue_start_time
                print(f"✓ Started after {queue_duration:.0f}s in queue")
                queue_start_time = None
        
        # ... rest of status handling
```

---

### 4. Graceful Timeout Handling

Detect and handle stuck jobs:

```python
def poll_with_timeout(job_id):
    max_wait = 180  # 3 minutes total
    max_queue_time = 60  # 1 minute in queue
    
    start_time = time.time()
    queue_start_time = None
    
    while time.time() - start_time < max_wait:
        status = get_status(job_id).get("status")
        elapsed = time.time() - start_time
        
        if status == "IN_QUEUE":
            if queue_start_time is None:
                queue_start_time = time.time()
            
            queue_time = time.time() - queue_start_time
            
            # Cancel if stuck in queue too long
            if queue_time > max_queue_time and elapsed > 90:
                print(f"⚠️  Job stuck in queue, cancelling...")
                cancel_job(job_id)
                return None
        
        # ... handle other statuses
        
        time.sleep(5)
    
    # Timeout - cancel and notify
    print(f"⏰ Timeout after {max_wait}s")
    cancel_job(job_id)
    return None

def cancel_job(job_id):
    """Cancel a stuck job"""
    cancel_url = f"https://api.runpod.ai/v2/{endpoint_id}/cancel/{job_id}"
    try:
        response = requests.post(cancel_url, headers=headers, timeout=5)
        return response.status_code == 200
    except:
        return False
```

---

### 5. Health Check Endpoint

Monitor endpoint availability:

```python
def check_endpoint_health(endpoint_id):
    """Check if endpoint is healthy before submitting jobs"""
    health_url = f"https://api.runpod.ai/v2/{endpoint_id}/health"
    
    try:
        response = requests.get(health_url, headers=headers, timeout=5)
        result = response.json()
        
        workers = result.get("workers", {})
        idle = workers.get("idle", 0)
        running = workers.get("running", 0)
        
        print(f"Endpoint Health:")
        print(f"  Idle workers: {idle}")
        print(f"  Running workers: {running}")
        
        return {
            "healthy": response.status_code == 200,
            "idle_workers": idle,
            "running_workers": running
        }
    except:
        return {"healthy": False, "idle_workers": 0, "running_workers": 0}

# Use before submitting
health = check_endpoint_health(endpoint_id)
if not health["healthy"]:
    print("⚠️  Endpoint unhealthy, consider waiting or using backup")
elif health["idle_workers"] == 0:
    print("⚠️  No idle workers, expect cold start delay")
```

---

### 6. Rate Limiting

Avoid overwhelming the endpoint:

```python
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_requests=5, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
    
    def wait_if_needed(self):
        now = time.time()
        
        # Remove old requests outside time window
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        # If at limit, wait
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0])
            if sleep_time > 0:
                print(f"⏳ Rate limit reached, waiting {sleep_time:.1f}s...")
                time.sleep(sleep_time)
        
        self.requests.append(now)

# Usage
limiter = RateLimiter(max_requests=5, time_window=60)

for image in images:
    limiter.wait_if_needed()
    submit_job(image)
```

---

## 📊 Monitoring Best Practices

### Track Key Metrics

```python
import json
from datetime import datetime

class JobMetrics:
    def __init__(self):
        self.jobs = []
    
    def record_job(self, job_id, submit_time, queue_time, process_time, status):
        self.jobs.append({
            "job_id": job_id,
            "submit_time": submit_time,
            "queue_time": queue_time,
            "process_time": process_time,
            "total_time": queue_time + process_time,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_stats(self):
        if not self.jobs:
            return {}
        
        completed = [j for j in self.jobs if j["status"] == "COMPLETED"]
        failed = [j for j in self.jobs if j["status"] == "FAILED"]
        
        return {
            "total_jobs": len(self.jobs),
            "completed": len(completed),
            "failed": len(failed),
            "success_rate": len(completed) / len(self.jobs) * 100,
            "avg_queue_time": sum(j["queue_time"] for j in completed) / len(completed) if completed else 0,
            "avg_process_time": sum(j["process_time"] for j in completed) / len(completed) if completed else 0,
            "avg_total_time": sum(j["total_time"] for j in completed) / len(completed) if completed else 0
        }
    
    def save_report(self, filename="job_metrics.json"):
        with open(filename, "w") as f:
            json.dump({
                "stats": self.get_stats(),
                "jobs": self.jobs
            }, f, indent=2)

# Usage
metrics = JobMetrics()

for image in images:
    submit_time = time.time()
    job_id = submit_job(image)
    
    result = poll_job(job_id)  # Returns queue_time, process_time, status
    
    metrics.record_job(
        job_id=job_id,
        submit_time=submit_time,
        queue_time=result["queue_time"],
        process_time=result["process_time"],
        status=result["status"]
    )

# Print summary
stats = metrics.get_stats()
print(f"Success Rate: {stats['success_rate']:.1f}%")
print(f"Avg Queue Time: {stats['avg_queue_time']:.1f}s")
print(f"Avg Process Time: {stats['avg_process_time']:.1f}s")

# Save detailed report
metrics.save_report()
```

---

## 🚨 Alerts & Notifications

### Set up alerts for anomalies:

```python
def check_and_alert(queue_time, process_time):
    # Alert if queue time exceeds threshold
    if queue_time > 60:
        send_alert(f"⚠️  High queue time: {queue_time}s")
    
    # Alert if process time is unusually slow
    if process_time > 120:
        send_alert(f"⚠️  Slow processing: {process_time}s")

def send_alert(message):
    # Implement your notification system
    # - Email
    # - Slack webhook
    # - Discord webhook
    # - PagerDuty
    print(f"ALERT: {message}")
```

---

## 💡 Production Recommendations

### For Stable Production:

1. **Keep 1+ workers warm** during business hours
2. **Set idle timeout to 300s** (5 minutes)
3. **Implement retry logic** with exponential backoff
4. **Monitor queue times** and alert on anomalies
5. **Use health checks** before job submission
6. **Implement rate limiting** to avoid overload
7. **Log all metrics** for analysis
8. **Have a backup endpoint** for failover

### For Cost Optimization:

1. **Scale to 0** during off-hours
2. **Accept cold start delays** (30-60s)
3. **Batch requests** when possible
4. **Use longer timeouts** (3-5 minutes)
5. **Implement smart retries** (don't retry immediately)

---

## 🔍 Debugging Checklist

When jobs get stuck:

- [ ] Check RunPod console for endpoint status
- [ ] Verify workers are running
- [ ] Check worker logs for errors
- [ ] Test with a single request
- [ ] Verify API key is valid
- [ ] Check network connectivity
- [ ] Review recent code changes
- [ ] Monitor resource usage (CPU/RAM)
- [ ] Check if model files are present
- [ ] Verify workflow JSON is valid

---

## 📈 Expected Performance

### BiRefNet CPU Endpoint

| Scenario | Queue Time | Process Time | Total Time |
|----------|------------|--------------|------------|
| **Warm worker** | 0-2s | 20-40s | 20-42s |
| **Cold start** | 30-60s | 20-40s | 50-100s |
| **High load** | 60-120s | 20-40s | 80-160s |

**Target SLA**:
- 95% of requests: < 60s (warm workers)
- 99% of requests: < 120s (including cold starts)

---

This guide covers the main strategies for handling queue issues effectively!
