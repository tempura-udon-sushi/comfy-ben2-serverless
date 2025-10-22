# 🧠 SimplyPNG — Runpod Serverless Batch Processing Guideline

### Version

v1.0 — for Windsurf project setup
Author: Leen Labs / SimplyPNG
Date: 2025-10-20

---

## 🎯 Objective

Design and implement a **scalable, serverless batch-processing system** using **Runpod Serverless** to process image jobs (e.g., background removal, object cutout, upscaling) for SimplyPNG.
The system should handle multiple concurrent requests safely, maintain cost efficiency, and ensure reliability with minimal infrastructure.

---

## 🏗️ System Architecture Overview

```
[ Client (Browser) ]
        │
        ▼
[ Next.js API Layer (BFF) ]
   ├─ job creation (POST /jobs)
   ├─ webhook receiver (/webhooks/runpod)
   ├─ credit management
   └─ dispatcher (cron/worker)
        │
        ▼
[ Runpod Serverless Container ]
   ├─ downloads input image(s)
   ├─ runs image model (ComfyUI / custom workflow)
   ├─ uploads output to storage
   └─ calls back via webhook
        │
        ▼
[ Supabase / Wasabi / S3 ]
   └─ stores input/output images
```

---

## ⚙️ Core Components

| Component             | Purpose                                 | Example Tech                   |
| --------------------- | --------------------------------------- | ------------------------------ |
| **Frontend**          | Upload input files via presigned URLs   | Next.js / React                |
| **API / BFF**         | Handle job creation, dispatch, webhooks | Next.js API routes             |
| **Database**          | Track job lifecycle + user credits      | Supabase (Postgres)            |
| **Queue**             | Manage job order + retries              | Simple DB queue or Redis/SQS   |
| **Storage**           | Host input/output images                | Supabase Storage / Wasabi / S3 |
| **Runpod Serverless** | GPU-based image processing              | Python container               |
| **Webhook**           | Receive job results                     | `/api/webhooks/runpod`         |

---

## 🗂️ Database Schema (Postgres / Supabase)

```sql
CREATE TABLE jobs (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  type TEXT NOT NULL,          -- e.g. 'bg_remove'
  params JSONB NOT NULL,
  input_urls JSONB NOT NULL,
  output_urls JSONB,
  status TEXT NOT NULL,        -- QUEUED | RUNNING | SUCCEEDED | FAILED
  error TEXT,
  attempts INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE credit_ledger (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  job_id UUID,
  delta INT NOT NULL,          -- -n for consumption
  note TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 🧩 API Endpoints

| Endpoint               | Method      | Description                                |
| ---------------------- | ----------- | ------------------------------------------ |
| `/api/jobs`            | POST        | Create a new job, enqueue for processing   |
| `/api/jobs/:id`        | GET         | Fetch job status and results               |
| `/api/webhooks/runpod` | POST        | Receive Runpod callback (signed)           |
| `/api/dispatcher`      | CRON/Worker | Poll queue and send job to Runpod endpoint |

---

## 🚀 Processing Flow

1. **User uploads image(s)** → presigned PUT to Supabase/S3
2. **`POST /jobs`** → create job record in DB (status = QUEUED)
3. **Dispatcher** picks QUEUED jobs → sends payload to **Runpod endpoint**
4. **Runpod container** processes input → saves output → sends **webhook callback**
5. **Webhook receiver** updates job status → deducts credits
6. **Client polls `GET /jobs/:id`** → gets output URLs

---

## 🧠 Runpod Payload Example

```json
{
  "job_id": "6a9b-...-1234",
  "type": "bg_remove",
  "params": { "halo": 2, "shadow": "soft", "output_format": "png" },
  "inputs": [
    { "url": "https://storage/input/abc.png" }
  ],
  "output_prefix": "https://storage/output/user123/6a9b/",
  "webhook_url": "https://api.simplypng.com/webhooks/runpod",
  "auth": { "callback_hmac": "base64-signature" },
  "timeout_s": 180
}
```

---

## 🐍 Runpod Serverless Example (`handler.py`)

```python
import os, json, io, requests, hmac, hashlib, base64
from PIL import Image

CALLBACK_SECRET = os.getenv("CALLBACK_SECRET", "change-me")

def sign(body: bytes) -> str:
    mac = hmac.new(CALLBACK_SECRET.encode(), body, hashlib.sha256).digest()
    return base64.b64encode(mac).decode()

def handler(event, _context):
    try:
        payload = event if isinstance(event, dict) else json.loads(event)
        job_id = payload["job_id"]
        input_url = payload["inputs"][0]["url"]
        out_prefix = payload["output_prefix"]
        webhook = payload["webhook_url"]

        # Download image
        r = requests.get(input_url)
        img = Image.open(io.BytesIO(r.content)).convert("RGBA")

        # Process (replace with actual model)
        result = img  # placeholder

        # Upload
        out_url = f"{out_prefix}output.png"
        buf = io.BytesIO()
        result.save(buf, "PNG")
        requests.put(out_url, data=buf.getvalue(), headers={"Content-Type": "image/png"})

        # Callback
        body = json.dumps({"job_id": job_id, "status": "SUCCEEDED", "outputs": [{"url": out_url}]})
        sig = sign(body.encode())
        requests.post(webhook, data=body, headers={"X-Signature": sig, "Content-Type": "application/json"})
        return {"ok": True}
    except Exception as e:
        err = json.dumps({"job_id": payload.get("job_id"), "status": "FAILED", "error": str(e)})
        sig = sign(err.encode())
        requests.post(payload["webhook_url"], data=err, headers={"X-Signature": sig})
        return {"error": str(e)}
```

---

## 🔁 Dispatcher Example (Node.js / TypeScript)

```ts
import fetch from "node-fetch";
import { sql } from "./db";

const RUNPOD_ENDPOINT = process.env.RUNPOD_ENDPOINT!;
const CALLBACK_SECRET = process.env.CALLBACK_SECRET!;

export async function dispatchOnce() {
  const job = await sql`
    UPDATE jobs SET status='DISPATCHED'
    WHERE id = (
      SELECT id FROM jobs WHERE status='QUEUED'
      ORDER BY created_at ASC
      LIMIT 1
      FOR UPDATE SKIP LOCKED
    )
    RETURNING *;
  `;

  if (!job) return;

  const payload = {
    job_id: job.id,
    type: job.type,
    params: job.params,
    inputs: job.input_urls,
    output_prefix: await createSignedOutputPrefix(job),
    webhook_url: process.env.WEBHOOK_URL,
    auth: { callback_hmac: "placeholder" },
    timeout_s: 180
  };

  const res = await fetch(RUNPOD_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ input: payload })
  });

  if (!res.ok) {
    await sql`UPDATE jobs SET status='QUEUED', attempts=attempts+1 WHERE id=${job.id}`;
  } else {
    await sql`UPDATE jobs SET status='RUNNING' WHERE id=${job.id}`;
  }
}
```

---

## 🪝 Webhook Receiver Example (Next.js API Route)

```ts
import { NextRequest, NextResponse } from "next/server";
import crypto from "crypto";
import { sql } from "@/lib/db";

const SECRET = process.env.CALLBACK_SECRET!;

function verifySig(raw: Buffer, sigB64: string) {
  const mac = crypto.createHmac("sha256", SECRET).update(raw).digest();
  const given = Buffer.from(sigB64, "base64");
  return crypto.timingSafeEqual(mac, given);
}

export async function POST(req: NextRequest) {
  const raw = Buffer.from(await req.arrayBuffer());
  const sig = req.headers.get("x-signature") || "";
  if (!verifySig(raw, sig)) return NextResponse.json({ error: "Invalid signature" }, { status: 401 });

  const { job_id, status, outputs, error } = JSON.parse(raw.toString());

  if (status === "SUCCEEDED") {
    await sql`UPDATE jobs SET status='SUCCEEDED', output_urls=${JSON.stringify(outputs)} WHERE id=${job_id}`;
    await consumeCreditsFor(job_id);
  } else {
    await sql`UPDATE jobs SET status='FAILED', error=${error} WHERE id=${job_id}`;
  }

  return NextResponse.json({ ok: true });
}
```

---

## 🔒 Security Guidelines

* Use **HMAC-SHA256** signature for webhook verification
* Store **CALLBACK_SECRET** and **Runpod API key** in environment variables
* Validate **file MIME types and sizes** on frontend before upload
* Generate **short-lived presigned URLs** (5–10 min)
* Use HTTPS for all webhook and storage URLs
* Ensure **job IDs are UUIDv4** to prevent enumeration
* Implement **rate limiting** and **credit pre-check** before enqueuing jobs

---

## ⚡ Reliability / Scaling Tips

| Area        | Practice                                                  |
| ----------- | --------------------------------------------------------- |
| Job Control | Use DB queue for MVP, Redis or SQS for scaling            |
| Concurrency | Token bucket pattern (`MAX_INFLIGHT`)                     |
| Retry       | Exponential backoff (`attempts` < 3)                      |
| Idempotency | Webhook handles duplicates gracefully                     |
| Timeout     | `timeout_s` in Runpod payload, enforce at container level |
| Metrics     | Log `job_id`, GPU runtime, model version                  |
| Cold Start  | Embed model weights inside image or cached layer          |
| Cost        | Batch small jobs if GPU warmup cost dominates             |

---

## 📦 Processing Types (SimplyPNG)

| Type             | Description                                   |
| ---------------- | --------------------------------------------- |
| `bg_remove`      | Background removal with shadow / halo options |
| `cutout_subject` | Clean subject cutout for product shots        |
| `object_remove`  | Remove unwanted items (region-based)          |
| `white_bg_ecomm` | Add clean white studio background             |
| `upscale_2k`     | 512→2K upscale (for product photos)           |
| `jpeg_to_png`    | Convert with transparent alpha                |

Each job stores its parameter version in `params: {"v":1,...}` for reproducibility.

---

## ✅ Minimum Checklist

* [ ] Database schema deployed
* [ ] `POST /jobs` endpoint implemented
* [ ] Dispatcher (cron or worker) running
* [ ] Runpod container deployed
* [ ] Webhook receiver verified with HMAC
* [ ] Credit deduction logic connected
* [ ] Logging & monitoring enabled
* [ ] Load test with 10–50 concurrent jobs

---

## 📊 Monitoring Metrics

| Metric            | Description                   |
| ----------------- | ----------------------------- |
| Job success rate  | SUCCEEDED / total             |
| Avg GPU time      | total GPU seconds / job count |
| Queue latency     | time(QUEUED → RUNNING)        |
| Failure reason    | timeout, network, model error |
| Credit efficiency | credits consumed / job        |
| Storage cost      | per GB/month per user         |

---

## 🧩 Optional Enhancements

* Add **job chaining** (e.g., remove → upscale)
* Enable **batch submission API** (`POST /jobs/batch`)
* Integrate **notifications** (email / webhook to client)
* Add **admin dashboard** for job monitoring
* Implement **web-based visual diff** viewer for output comparison

---

## 🧾 License / Compliance

* Verify all models (e.g., SD1.5, Florence-2, IC-Light) are under **commercial-safe license**
* Track model versions used per job for auditability
* Remove all **image metadata** before storage (privacy)

---

## 💡 Summary

This setup provides:

* Fully **serverless**, **event-driven**, and **scalable** batch processing
* End-to-end security with webhook HMAC verification
* Clear separation of **job management**, **execution**, and **billing**
* Low maintenance cost suitable for lean SaaS (SimplyPNG, Leen Labs ecosystem)

---
