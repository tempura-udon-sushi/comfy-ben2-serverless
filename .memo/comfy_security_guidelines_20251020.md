# 🧱 SimplyPNG — Secure ComfyUI Configuration Guidelines

## 1. Overview

In SimplyPNG, all prompts are pre-defined and controlled by the system.  
Users do **not** directly enter prompts, so the risk of **direct prompt injection** is minimal.  
However, indirect attacks (via filenames, metadata, or embedded image text) can still occur.

The goal of this document is to clarify which countermeasures should be implemented **inside ComfyUI** and which should remain **outside (backend layer)**.

---

## 2. Security Layer Breakdown

| Layer | Purpose | Implementation Location |
|-------|----------|--------------------------|
| **Frontend (Next.js)** | Validate uploads, enforce input limits | ✅ Frontend |
| **Backend (API / Edge Function)** | Prompt sealing, sanitization, metadata stripping, rate limit | ✅ Main defense layer |
| **ComfyUI Runtime** | Fixed workflows, disable external nodes, restrict output | ⚙️ Secondary (supportive) layer |
| **Model Level (Qwen, Flux, etc.)** | Locked system prompt, no external I/O | ⚙️ Within Comfy node or model settings |

---

## 3. 🧱 Primary Defense — *Outside ComfyUI*

Most security logic should live **outside** Comfy.

| Measure | Description |
|----------|--------------|
| **Prompt Sealing** | Build and lock final prompt templates on the server. Pass the completed string to Comfy. |
| **Variable Whitelisting & Sanitization** | Only allow pre-approved variables (e.g., color codes, style options). |
| **Metadata Stripping (EXIF/IPTC/XMP)** | Strip metadata before the image reaches Comfy using Sharp or Pillow. |
| **Filename Re-issue / MIME Enforcement** | Rename uploaded files to UUIDs, verify MIME headers before passing to Comfy. |
| **Secure Comfy Invocation** | Use a secure API proxy between the frontend and Comfy backend; never expose Comfy’s raw port. |
| **Key Management** | Do not embed API keys in Comfy nodes. All keys handled by backend. |
| **Logging & Rate Control** | Implement at backend level. Comfy’s internal logs are not sufficient. |

> ✅ Comfy should receive only *already-sanitized* requests and act as a deterministic, isolated image processor.

---

## 4. ⚙️ Secondary Defense — *Inside ComfyUI*

Inside ComfyUI, the focus is on **reducing flexibility and removing attack surfaces**.

| Measure | Description |
|----------|-------------|
| **Fixed Workflows** | Each workflow corresponds to a single, locked task (e.g., background removal, relighting). |
| **Disable Dangerous Nodes** | Remove or block nodes like: `Web Request`, `PythonExec`, `RunPythonCode`, `LLM Party`, etc. |
| **Avoid Editable Prompt Nodes** | No editable text nodes in the public interface; system templates are fixed. |
| **Restrict Outputs** | Allow only image outputs; remove text or console output nodes. |
| **Custom Node Policy** | Avoid AGPL-3.0-licensed or unverified nodes that may perform external calls. |
| **Sandboxed Execution** | Run Comfy inside a Docker container with no host FS mount or internet access. |
| **Node Configuration Lock** | Hardcode sensitive parameters (e.g., guidance scale, lighting mode). |

> 🔒 Within Comfy: **Reduce freedom, block external access, and freeze workflow parameters.**

---

## 5. 🧩 Recommended Architecture for SimplyPNG

```

Frontend (Next.js)
│  ──> Validate upload & size
▼
Backend (Node API / Edge Function)
│  ──> Prompt sealing
│  ──> Allowlist & sanitization
│  ──> Strip metadata (Sharp)
│  ──> UUID rename
▼
ComfyUI (RunPod / Local worker)
│  ──> Fixed workflow only
│  ──> No external or PythonExec nodes
│  ──> Only image outputs
▼
Supabase Storage (paid users)
│  ──> Store final processed image
▼
Client display

```

---

## 6. ✅ Summary

- **Main security logic = Comfy external (backend side)**  
- **Comfy internal defense = Restrict flexibility**  
- Comfy should act as a **deterministic, sandboxed engine** that receives sanitized, fixed prompts.  
- Always combine:
  - Prompt sealing  
  - Metadata stripping  
  - Variable allowlisting  
  - Workflow locking  
  - External access blocking  

---

## 7. 🔍 Optional: Security Audit Checklist for Comfy

| Category | Checklist | Status |
|-----------|------------|--------|
| Nodes | No “PythonExec”, “LLM Party”, or “Web Request” nodes | ☐ |
| Workflow | Each workflow performs one fixed task | ☐ |
| Parameters | All numeric / enum params locked | ☐ |
| Output | Only image type outputs | ☐ |
| Environment | Run in Docker with no host FS mount | ☐ |
| Network | Comfy runs without internet access | ☐ |
| Logs | Backend captures request + result metadata | ☐ |

---

**File:** `simplypng_comfyui_security_guideline.md`  
**Maintained by:** Leen Labs / SimplyPNG Dev Team  
**Last Updated:** 2025-10-20

---
```
