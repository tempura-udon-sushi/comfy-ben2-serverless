# Recommended architecture at a glance

* **Anonymous & free users**: ephemeral storage + short TTL, or fully client-side if possible.
* **Logged-in free users**: ephemeral storage + short TTL, optional opt-in save.
* **Paid users**: persistent storage with versions and restore, credit tracking, CDN.

---

# 1) Buckets & retention (Supabase Storage)

Create **three** buckets with clear lifecycles:

1. `uploads-ephemeral` (private)

   * Purpose: temporary originals from anonymous/free users.
   * **TTL**: auto-delete after 24–72 hours via scheduled job.
   * Access: signed URLs only, short (≤15 min) for workers.

2. `outputs-ephemeral` (private)

   * Purpose: temporary results for anonymous/free users.
   * **TTL**: 24–72 hours.
   * Access: signed URLs only (deliver via CDN).

3. `user-library` (private)

   * Purpose: paid users’ originals + outputs (persistent).
   * **Retention**: keep until user deletes; offer “archive after N days” toggle.
   * Access: RLS + signed URLs / service role.
   * Structure: `user_id/{image_id}/original.*`, `user_id/{image_id}/output/{version_id}.png`, `thumb.webp`.

> Toggle public access **off** for all three; deliver with short-lived signed URLs to control abuse.

---

# 2) DB tables (minimal & future-proof)

* `images`

  * `id (uuid)`, `user_id (nullable)`, `sha256`, `width`, `height`, `mime`, `bucket`, `path_original`, `created_at`.
* `image_outputs`

  * `id`, `image_id`, `op_key` (e.g., `bgremove-v3:white-100%`), `path_output`, `thumbnail_path`, `metadata (jsonb)`, `created_at`.
* `jobs`

  * `id`, `user_id (nullable)`, `status` (`queued|running|done|error|expired`), `input_sha256`, `op_key`, `priority`, `worker_notes`, `created_at`, `updated_at`.
* `credits`

  * `user_id`, `balance`, `updated_at`. (Also log each spend in `credit_ledger`.)

> **op_key** = exact operation signature (model/version + params). It enables **compute caching**: same `sha256 + op_key` → reuse existing output.

**RLS policies (gist):**

* `images`: `user_id = auth.uid()` OR `user_id IS NULL` but only readable by service role.
* `image_outputs`: same.
* Free/anon users never list buckets; they only get **signed download URLs** for their own job.

---

# 3) Upload path (frontend-first, bandwidth-light)

**Client steps (works for anon + logged-in):**

1. Read file → **pre-hash (SHA-256)** in browser (streaming if large).
2. **Local safety precheck** (lightweight): file type, magic bytes, max dimensions (e.g., 12 MP), file size (e.g., ≤20 MB), and quick content heuristic (e.g., blocked extensions, SVG sanitization; EXIF strip optional on client).
3. Ask API: “I want to process `sha256` with `op_key`—do we already have it?”

   * If **hit**, return cached output URLs immediately.
   * If **miss**, API returns a **presigned upload URL** to `uploads-ephemeral` (or `user-library` if paid + “keep original” enabled).
4. Client uploads directly to Supabase via presigned URL (bypasses your server).

**Server (edge/API) after upload:**

* Optionally run a **server-side safety check** (moderation/virus scan) for defense-in-depth.
* Create a `jobs` record, enqueue work, return `job_id`.

---

# 4) Processing pipeline (GPU worker friendly)

* **Queue**: Upstash Redis, Supabase Queues, or your lightweight broker.

* **Workers**: Runpod serverless GPU. Worker pulls next job:

  1. Download input from Supabase via short signed URL.
  2. Process (background removal / compositing / upscaling).
  3. Strip EXIF, normalize color, and **deterministic file naming**:

     * `outputs-ephemeral/{job_id}.png` (free/anon)
     * `user-library/{user_id}/{image_id}/output/{version_id}.png` (paid)
     * Also generate `thumb.webp` for fast UI.
  4. Update `image_outputs` and `jobs.status`.
  5. (Paid) decrement `credits` atomically.

* **Webhook/polling**:

  * If user is online → use WebSocket or SSE to notify done.
  * Else, the client polls `GET /jobs/{id}`.

---

# 5) Free vs Paid behavior (clean & predictable)

**Anonymous user (no login):**

* Upload to `uploads-ephemeral`.
* Result saved in `outputs-ephemeral`.
* **TTL**: delete both in 24–72 hours.
* Provide **Download** button + “Sign up to save” CTA.

**Logged-in free user:**

* Same as anonymous by default.
* Optional toggle “Keep this result for 7 days” (still ephemeral bucket).
* Compute caching still applies.

**Paid user:**

* Originals & outputs go to `user-library`.
* Keep **version history** (last N versions; user setting).
* CDN-backed thumbnails for dashboard speed.
* Enable **collections/folders** and **re-run from original**.

---

# 6) Client-only processing (when it makes sense)

You *can* offer a **client-side path** for small tasks to delight free users and reduce cost:

* Examples: PNG→WEBP, color profile fix, EXIF strip, simple resize/crop, maybe a **tiny on-device matting** (if you ship a WASM model).
* For heavier ops (Qwen/SDXL/IC-Light/upscalers), keep it **server-side** to be consistent and support quality.

Rule of thumb:

* If final image ≤ 2048 px and operation is ~instant in WASM → do it client-side, **no storage** by default.
* Otherwise follow the standard server pipeline above.

---

# 7) Cost controls & performance

* **Ingress guardrails**: hard cap dimensions (e.g., 6000×6000), auto-downscale originals for processing unless “Keep full-res” (paid).
* **Compute cache** (sha256 + op_key) = biggest savings.
* **Cold storage toggle** for paid libraries (“archive outputs older than 90 days to cheaper class” if/when Supabase tier supports).
* **WebP thumbnails** only; load originals lazily via signed URL with short expiry (e.g., 60–120s).
* **Chunked uploads** for big files; show progress.
* **EXIF strip** everywhere; product users rarely need EXIF.

---

# 8) Security & compliance

* **Strip EXIF** (privacy), sanitize SVGs, disallow active content.
* **Virus scan** on server (ClamAV or provider add-on) for uploads that are kept.
* **RLS** everywhere; never expose bucket listing.
* **Short-lived signed URLs** (download) and **one-time presigned PUT** (upload).
* **Audit ledger** for credit spends and destructive ops.
* Consider **PDPA (Singapore)** + **GDPR-style** deletion: “Delete my data” wipes `user-library` and related rows.

---

# 9) Minimal APIs (clean contracts)

* `POST /intake` → body: `{ sha256, filename, size, width, height, op_key, wants_persist }`

  * returns `{ cached:true, output_urls }` **or** `{ upload_url, job_id }`
* `GET /jobs/{id}` → `{ status, output_urls? }`
* `POST /outputs/promote` (free → paid save)

  * copies from `outputs-ephemeral` to `user-library`, creates `images/image_outputs` rows, updates credits if needed.

---

# 10) Naming & keys (idempotent + human-tolerant)

* **Content address** for originals: `sha256` of raw bytes.
* **Operation key**: `bgremove-v3:white-100%-softshadow:studio-A` (include every parameter that affects pixels).
* **Paths** deterministic from (`user_id?`, `image_id`, `version_id`), e.g.:

  * `user-library/{uid}/{img}/output/{ver}.png`
  * `outputs-ephemeral/{job_id}.png`

---

# 11) What you asked, directly answered

> “safety and size are OK, we store to supabase? (or just process on frontend for free?)”

* For **heavier ops**: yes, store to **ephemeral** bucket, process on server, keep results ephemeral for free users.
* For **light ops**: do it client-side and **skip storage** unless they explicitly save.

> “Save the processed image for paid user in supabase?”

* Yes—store in `user-library` with versions, thumbnails, and metadata. Give them controls (keep original? archive policy?).

---

# 12) Quick RLS examples (sketch)

```sql
-- images: only owner can select
create policy "images owner can select"
on public.images for select
using (user_id = auth.uid());

-- outputs: only owner can select
create policy "outputs owner can select"
on public.image_outputs for select
using (
  exists (
    select 1 from public.images i
    where i.id = image_outputs.image_id
      and i.user_id = auth.uid()
  )
);
```

(Use service role for workers and ephemeral buckets.)

---

# 13) Nice-to-haves (later)

* **Share link** for paid users (creates a **read-only** short link with expiring signed URLs).
* **Re-run** with different op_key from the same original (one-click A/B).
* **Team seats** (shared library subpaths).
* **Watermarked previews** for unpaid results if you want to push conversion.

---

## TL;DR recommended default

* Free/anon: ephemeral upload → GPU process → ephemeral output (24–72h TTL), no persistent save unless they upgrade.
* Paid: persistent originals + versioned outputs in `user-library`, thumbnails via CDN, credit ledger, compute cache by `(sha256, op_key)`.
* Always: client pre-hash, presigned direct uploads, server-side safety check, short-lived signed URLs, strict RLS, EXIF strip, and auto cleanup jobs.

If you want, I can sketch the exact bucket paths, table DDL, and a tiny Next.js API route sample for `POST /intake` and the Runpod worker loop in one go.
