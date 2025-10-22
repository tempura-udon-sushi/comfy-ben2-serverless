# Product Roadmap & Risk Analysis
## Minne Background Removal Service

**Target Users:** Japanese handcraft sellers on Minne marketplace  
**Core Value:** Simple, affordable product photo background removal  
**Competition:** Canva ($20/month), Photoshop (complex), remove.bg (expensive per image)

---

## ⚠️ RISKS & MITIGATION

### 1. Output Safety (CRITICAL - Priority 1)

**Risk:**  
Input filter blocks NSFW content, but AI model could still generate inappropriate output:
- Qwen could hallucinate inappropriate content during image editing
- Model might add unwanted objects
- Background removal might expose inappropriate areas in clothing/fashion items

**Impact:** Brand damage, legal liability, user trust loss

**Mitigation Strategies:**
- **Output Safety Checker**: Run Florence2 caption on final output, check for unsafe keywords
- **Dual-pass filtering**: Both input AND output must pass safety checks
- **Confidence threshold**: Flag images with low confidence for manual review
- **Watermark system**: Add watermark during processing, remove only after safety approval
- **Audit log**: Store safety check results for compliance

**Implementation:**
```
Input Image → Input Safety Check → Process → Output Safety Check → User Download
                    ↓ BLOCK                           ↓ BLOCK
              [Reject with message]            [Manual review queue]
```

---

### 2. Adversarial Attacks (HIGH - Priority 2)

**Risk:**  
Users might try to bypass input filters:
- Obscured NSFW content (partially covered, artistic interpretations)
- Batch upload spam/abuse to overwhelm system
- Prompt injection via image metadata/EXIF data
- Watermarked/copyrighted images from competitors

**Impact:** System abuse, increased costs, legal issues

**Mitigation Strategies:**
- **Rate Limiting:**
  - Free users: 10 images/day, 1 request per 30 seconds
  - Paid users: 100 images/day, 3 requests per 10 seconds
  - IP-based throttling
- **CAPTCHA**: Required after 3 consecutive requests
- **Multiple Detection Layers:**
  - Florence2 caption analysis (current)
  - CLIP-based NSFW detector (add as secondary check)
  - Reverse image search for professional/copyrighted photos
- **Suspicious Pattern Detection:**
  - Block IPs with >5 flagged images in 24 hours
  - Flag accounts with unusual upload patterns
- **EXIF Analysis:**
  - Detect professional camera metadata
  - Flag stock photo characteristics

---

### 3. Quality Control Issues (HIGH - Priority 2)

**Risk:**  
Bad outputs damage user trust and reputation:
- Wrong product isolated (background items instead of main product)
- Over-aggressive cropping cuts off product parts
- Color distortion or artifacts
- Shadows removed when they should be preserved
- Hair/fur/fine details lost on plush toys

**Impact:** User dissatisfaction, high refund rate, negative reviews

**Mitigation Strategies:**
- **Before/After Preview**: Mandatory approval step before download
- **Quality Score System:**
  ```python
  quality_metrics = {
      'florence_confidence': 0.8,  # Caption confidence
      'edge_smoothness': 0.7,      # No jagged edges
      'color_preservation': 0.9,   # Original colors maintained
      'product_completeness': 1.0  # No cropping of main product
  }
  ```
- **"Redo" Button**: With feedback options:
  - "Wrong product isolated"
  - "Product cut off"
  - "Poor quality"
  - "Colors look wrong"
- **A/B Testing**: Test different prompt variations for quality
- **Success Metrics Tracking:**
  - % of users who download without redo
  - Average processing time
  - User satisfaction rating (optional post-download survey)

**Implementation Priority:**
1. Preview with approval (Phase 1)
2. Redo button (Phase 1)
3. Quality metrics (Phase 2)
4. A/B testing (Phase 3)

---

### 4. Copyright & Legal (MEDIUM - Priority 3)

**Risk:**  
Users upload images they don't own:
- Professional product photos stolen from competitors
- Brand logos that shouldn't be edited
- Stock photography with watermarks removed
- Celebrity/influencer images

**Impact:** DMCA takedowns, legal liability, platform ban risk

**Mitigation Strategies:**
- **Terms of Service:**
  - Users affirm they own or have rights to images
  - Clear statement that service is for personal product photos only
  - Liability disclaimer
- **Reverse Image Search:**
  - Check against Google Images for exact matches
  - Flag if image appears on major e-commerce sites
- **Logo Detection:**
  - Detect major brand logos (Nike, Apple, etc.)
  - Block or warn if detected
- **Watermark Detection:**
  - Detect common stock photo watermarks (Shutterstock, Getty, etc.)
  - Block if found
- **DMCA Compliance:**
  - Clear takedown process
  - User identity verification for high-volume users

---

### 5. Cost Management (MEDIUM - Priority 3)

**Risk:**  
GPU costs spiral out of control:
- Abuse: users uploading excessively
- Large batch uploads
- High-resolution images requiring more processing
- Peak hour congestion

**Impact:** Financial losses, slow service, need to raise prices

**Mitigation Strategies:**
- **Tiered Pricing:**
  ```
  Free:  10 images/month,  standard quality, watermarked
  Basic: 100 images/month, $5/mo, no watermark, email support
  Pro:   Unlimited,        $15/mo, premium quality, batch processing, API
  ```
- **File Size Limits:**
  - Free: 4MB max, 2048x2048px max
  - Paid: 10MB max, 4096x4096px max
- **Processing Queue:**
  - Paid users: Priority queue
  - Free users: Standard queue (may wait during peak hours)
  - Display estimated wait time
- **Auto-scaling:**
  - Scale GPU instances based on queue length
  - Auto-shutdown during low traffic hours (2-6 AM JST)
- **Cost Monitoring:**
  - Alert if daily GPU cost exceeds budget
  - Monthly cost reports per user tier

---

### 6. Model Failures (MEDIUM - Priority 2)

**Risk:**  
Florence2/Qwen produces errors or crashes:
- Florence misidentifies product (e.g., "table" instead of "phone on table")
- Qwen fails to remove background properly
- Model hangs or times out
- Out of memory errors on large images

**Impact:** Poor user experience, wasted resources, support tickets

**Mitigation Strategies:**
- **Timeout Limits:**
  - Florence2: 10s max
  - Qwen processing: 30s max
  - Total workflow: 45s max
- **Fallback Models:**
  ```
  Primary: Florence2 + Qwen + Dynamic Prompt
  Fallback 1: U2Net (simpler background removal)
  Fallback 2: SAM (Segment Anything Model)
  Emergency: Simple color-based removal
  ```
- **Error Handling:**
  - User-friendly error messages (not technical details)
  - Automatic retry logic (max 2 retries)
  - Suggest alternative: "Try a different photo angle"
- **Health Monitoring:**
  - Track model success rates
  - Alert if success rate drops below 90%
  - Automatic model restart if needed

---

### 7. Data Privacy (HIGH - Priority 2)

**Risk:**  
User images contain sensitive information:
- Personal photos accidentally uploaded
- Private information visible in background (addresses, documents, etc.)
- GDPR compliance for EU users
- Data breach exposing user images

**Impact:** Legal violations, user trust loss, fines

**Mitigation Strategies:**
- **Minimal Data Storage:**
  - Process images in memory only
  - Auto-delete after 24 hours maximum
  - No permanent storage of originals
- **Privacy Policy:**
  - Clear explanation of data handling
  - State explicitly: "We don't store your images"
  - GDPR-compliant privacy notice
- **User Control:**
  - "Delete Immediately" button after download
  - No account/login required (anonymous processing)
  - Option to process without saving preview
- **Encryption:**
  - HTTPS for all transfers
  - Encrypted temporary storage (if any)
- **Access Logs:**
  - Minimal logging (timestamp, IP, file size only)
  - No image content logging
  - Auto-delete logs after 30 days

---

## 🎯 USER DEMANDS & FEATURES

### 1. Background Customization (HIGH - Phase 1)

**Current:** Pure white background only  
**User Need:** Different background options for various marketplace requirements

**Features:**
- **Color Presets:**
  - Pure White (#FFFFFF) - Default
  - Light Gray (#F5F5F5) - Minne common
  - Cream (#FFFDD0) - Warm tone
  - Soft Blue (#F0F8FF) - Baby products
  - Custom hex color input
- **Transparent PNG:**
  - For users who add backgrounds later
  - Essential for designers
- **Gradient Backgrounds:**
  - Subtle gradients (light to lighter)
  - Professional look
- **Pattern Backgrounds:**
  - Subtle textures (linen, paper, wood grain)
  - Low opacity to not distract from product

**Implementation:**
```python
class BackgroundCustomizer:
    backgrounds = {
        'pure_white': '#FFFFFF',
        'light_gray': '#F5F5F5',
        'cream': '#FFFDD0',
        'soft_blue': '#F0F8FF',
        'transparent': 'alpha',
        'custom': 'user_input'
    }
```

**UI Design:**
- Color swatches with preview
- Hex color picker
- "Transparent" checkbox

---

### 2. Image Size Control (HIGH - Phase 1)

**Current:** Variable output size based on model  
**User Need:** Standard sizes for different platforms

**Standard Sizes:**
```python
size_presets = {
    'minne_standard': (640, 640),
    'minne_large': (1200, 1200),
    'instagram_square': (1080, 1080),
    'instagram_portrait': (1080, 1350),
    'custom': (user_width, user_height)
}
```

**Features:**
- **Maintain Aspect Ratio:**
  - Add padding to fit dimensions
  - Center product automatically
- **Fill Frame:**
  - Scale product to edges
  - Option to maintain proportions
- **Smart Crop:**
  - Auto-detect product bounds
  - Center with optimal padding
- **Upscaling:**
  - Use RealESRGAN for larger sizes
  - Separate upscaling workflow for premium users

**UI Design:**
- Dropdown with popular sizes
- Custom width/height inputs
- Preview with grid overlay

---

### 3. Shadow Control (MEDIUM - Phase 2)

**Current:** Generic "preserve shadows" in prompt  
**User Need:** Fine control over shadow appearance

**Options:**
- **Natural Shadow:**
  - Keep original shadows (current default)
  - Good for realistic product photos
- **No Shadows:**
  - Remove all shadows completely
  - Clean, minimal look
- **Artificial Drop Shadow:**
  - Add consistent drop shadow
  - Adjustable opacity (10-50%)
  - Adjustable offset (5-20px)
- **Enhanced Shadow:**
  - Strengthen existing shadows
  - Make product "pop" more

**Implementation:**
```python
shadow_prompts = {
    'natural': 'preserve realistic shadows',
    'none': 'remove all shadows completely, flat lighting',
    'drop_shadow': 'add subtle drop shadow underneath',
    'enhanced': 'enhance and strengthen natural shadows'
}
```

---

### 4. Edge Refinement (MEDIUM - Phase 2)

**Current:** Model-dependent edge quality  
**User Need:** Control over edge appearance

**Options:**
- **Soft Edge (Feathering):**
  - 2-5px feather radius
  - Natural blend
  - Good for organic products
- **Hard Edge (Sharp):**
  - Crisp cutout
  - Good for geometric products
  - Professional catalog look
- **Edge Smoothing:**
  - Remove jagged artifacts
  - Clean up rough edges
- **Detail Preservation:**
  - Keep fine details (hair, fur, lace)
  - Important for textile/plush products

**Technical Approach:**
- Post-process alpha channel
- Morphological operations
- Guided filter for edge refinement

---

### 5. Batch Processing (HIGH - Phase 2)

**Current:** One image at a time  
**User Need:** Process multiple product photos efficiently

**Features:**
- **Upload Multiple:**
  - Free: up to 5 images
  - Paid: up to 20 images
- **Shared Settings:**
  - Apply same background/size to all
  - Individual adjustments optional
- **Progress Tracking:**
  - Show current image (3/10)
  - Estimated time remaining
  - Thumbnail previews
- **Bulk Download:**
  - ZIP file with all processed images
  - Original filenames preserved
  - Option to rename (product_1.png, product_2.png, etc.)

**UI Design:**
- Drag-and-drop multiple files
- Grid view with status indicators
- "Process All" button

---

### 6. Product Positioning (MEDIUM - Phase 2)

**Current:** Product position depends on original image  
**User Need:** Consistent product placement across photos

**Features:**
- **Auto-Center:**
  - Detect product bounds
  - Center in frame
- **Padding Control:**
  - Small (10% margin) - Product fills frame
  - Medium (20% margin) - Standard
  - Large (30% margin) - Spacious
- **Alignment:**
  - Center (default)
  - Top-aligned (for tall products)
  - Bottom-aligned (for short products)
- **Rotation:**
  - Auto-straighten
  - Manual rotation adjustment

**Implementation:**
- Bounding box detection
- Centroid calculation
- Affine transformations

---

### 7. Quality Presets (LOW - Phase 3)

**User Need:** Speed vs. quality trade-off

**Presets:**
```python
quality_presets = {
    'fast': {
        'resolution': (512, 512),
        'steps': 10,
        'time': '~5 seconds',
        'use_case': 'Quick preview'
    },
    'standard': {
        'resolution': (1024, 1024),
        'steps': 20,
        'time': '~15 seconds',
        'use_case': 'Most users (default)'
    },
    'premium': {
        'resolution': (2048, 2048),
        'steps': 30,
        'upscale': True,
        'time': '~45 seconds',
        'use_case': 'Print quality, large displays'
    }
}
```

---

### 8. Preview & Edit (HIGH - Phase 1)

**Current:** Direct output, no preview  
**User Need:** See results before committing

**Features:**
- **Side-by-Side Comparison:**
  - Original | Processed
  - Swipe to compare
  - Zoom in/out
- **Download Options:**
  - "Looks Good" → Download
  - "Redo" → Try again with feedback
  - "Edit" → Manual touch-up (Phase 2)
- **Manual Touch-up (Phase 2):**
  - Brush tool to restore areas
  - Eraser to remove more background
  - Undo/redo up to 10 steps
- **History:**
  - Save last 3 processed images
  - Quick access to recent work

---

### 9. Format Options (MEDIUM - Phase 2)

**Current:** PNG only  
**User Need:** Different formats for different uses

**Formats:**
- **PNG:**
  - Transparent background support
  - Lossless quality
  - Larger file size
  - Best for: Further editing, design work
- **JPEG:**
  - White background only
  - Smaller file size (70% compression)
  - Best for: Web uploads, Minne listings
- **WebP:**
  - Modern format
  - Better compression than JPEG
  - Transparency support
  - Best for: Modern websites, speed
- **Multi-Export:**
  - Download all 3 formats at once (ZIP)
  - Paid feature

---

### 10. Mobile Support (CRITICAL - Phase 1)

**Current:** Desktop browser only  
**User Need:** Most Minne sellers use smartphones

**Features:**
- **Camera Integration:**
  - "Take Photo" button
  - Direct camera access
  - No need to save to gallery first
- **Gallery Upload:**
  - Select from photo library
  - Multi-select for batch
- **Mobile-Optimized UI:**
  - Touch-friendly buttons
  - Swipe gestures
  - Vertical layout
  - Large preview area
- **Progressive Web App (PWA):**
  - Install to home screen
  - Works offline (for UI, not processing)
  - Push notifications when processing complete
- **Network Optimization:**
  - Compress uploads on mobile
  - Progressive image loading
  - Offline queue (process when back online)

---

## 🔧 TECHNICAL OPTIMIZATIONS

### Model Processing Strategy

**Current Setup:**
- Florence2: Caption generation
- Qwen: Image editing (1024x1024 optimal)
- Dynamic Prompt Builder: Text processing

**Optimizations:**

1. **Quantization:**
   ```python
   # Reduce model size and increase speed
   model_precision = {
       'florence2': 'FP16',  # 2x faster, minimal quality loss
       'qwen': 'FP16',       # Keep quality for main processing
       'upscaler': 'INT8'    # 4x faster, acceptable for upscaling
   }
   ```

2. **Model Caching:**
   ```python
   # Keep models in VRAM between requests
   keep_models_loaded = True
   unload_after_idle = 300  # 5 minutes
   ```

3. **Batch Inference:**
   ```python
   # Process multiple images in one batch
   batch_size = 4  # Adjust based on VRAM
   ```

### Output Size Strategy

**Recommended Workflow:**
```
Input (variable size)
  ↓
Resize to 1024x1024 (Qwen optimal)
  ↓
Process with Qwen
  ↓
Resize to user's target size
  ↓
[Optional] Upscale if > 2048x2048
  ↓
Output
```

**Upscaling:**
- Use RealESRGAN for sizes > 2048px
- Separate dedicated upscaling workflow
- Premium feature only (higher GPU cost)

### Caching Strategy

```python
cache_layers = {
    'florence2_captions': {
        'ttl': 3600,  # 1 hour
        'key': image_hash,
        'storage': 'redis'
    },
    'processed_results': {
        'ttl': 3600,  # 1 hour (if user re-processes)
        'key': image_hash + settings_hash,
        'storage': 's3'
    },
    'user_quota': {
        'ttl': 86400,  # 24 hours
        'key': user_ip,
        'storage': 'redis'
    }
}
```

### Queue Management

**Architecture:**
```
User Upload → Redis Queue → Worker Pool → Post-Process → User Download
                   ↓
            Priority System:
            - Pro users: Priority 1
            - Basic users: Priority 2
            - Free users: Priority 3
```

**Features:**
- Estimated wait time calculation
- Email notification when done (optional)
- WebSocket for real-time status updates
- Automatic retry on failure (max 2 times)

---

## 📊 BUSINESS MODEL

### Freemium Pricing

| Tier | Price | Limits | Features |
|------|-------|--------|----------|
| **Free** | ¥0 | • 10 images/month<br>• Standard quality<br>• Watermarked<br>• Queue priority: Low | • Basic background removal<br>• White background only<br>• Standard sizes |
| **Basic** | ¥500/month<br>($5 USD) | • 100 images/month<br>• Standard quality<br>• No watermark<br>• Queue priority: Medium | • All Free features<br>• Custom background colors<br>• All size presets<br>• Email support |
| **Pro** | ¥1,500/month<br>($15 USD) | • Unlimited images<br>• Premium quality<br>• No watermark<br>• Queue priority: High | • All Basic features<br>• Batch processing (20 images)<br>• Shadow control<br>• Edge refinement<br>• API access<br>• Priority support |

### Usage Analytics

**Track Metrics:**
```python
analytics = {
    'success_rate': '% of images successfully processed',
    'user_satisfaction': '% who download without redo',
    'processing_time': 'average seconds per image',
    'popular_categories': 'most common product types',
    'failure_reasons': {
        'quality_issues': 'count',
        'wrong_product': 'count',
        'timeout': 'count',
        'safety_blocked': 'count'
    },
    'conversion_rate': '% free users who upgrade',
    'churn_rate': '% subscribers who cancel'
}
```

### Customer Support

**Self-Service:**
- Comprehensive FAQ
- Video tutorials (Japanese)
- Example gallery (good vs. bad photos)
- Tips for best results

**Support Channels:**
- Email: support@yourservice.jp
- Response time:
  - Free: 48 hours
  - Basic: 24 hours
  - Pro: 4 hours (business hours)
- Feedback form in app
- Community forum (future)

---

## 🚀 IMPLEMENTATION ROADMAP

### Phase 1: MVP+ (1-2 months)
**Goal:** Launch with safety and core features

**Priority Features:**
1. ✅ Input Safety Checker (COMPLETE)
2. ⚠️ Output Safety Checker
3. ⚠️ Background Color Selector (White, Gray, Transparent)
4. ⚠️ Size Presets (640x640, 1200x1200, Custom)
5. ⚠️ Before/After Preview with Approval
6. ⚠️ Mobile-Responsive UI
7. ⚠️ Rate Limiting (10/day free, 100/day paid)

**Technical:**
- Basic queue system
- Redis for session storage
- PostgreSQL for user accounts
- S3 for temporary image storage (24hr auto-delete)

**Business:**
- Landing page (Japanese)
- Pricing page
- Terms of Service
- Privacy Policy
- Stripe payment integration

---

### Phase 2: Enhanced (2-3 months)
**Goal:** Improve quality and add power features

**Features:**
1. Batch Processing (5 images free, 20 images paid)
2. Quality Presets (Fast/Standard/Premium)
3. Shadow Control
4. Edge Refinement
5. Multiple Format Export (PNG/JPEG/WebP)
6. Manual Touch-up Tools (brush restore/erase)
7. CLIP-based NSFW detector (secondary check)

**Technical:**
- Auto-scaling GPU instances
- CDN for static assets
- WebSocket for real-time updates
- Job retry logic

**Business:**
- Email marketing automation
- Usage analytics dashboard
- Customer success tracking
- Affiliate program for influencers

---

### Phase 3: Premium (3+ months)
**Goal:** Advanced features for power users

**Features:**
1. API Access
2. Product Positioning Controls
3. Advanced Shadow Generation
4. Upscaling Workflow (4K+)
5. Gradient/Pattern Backgrounds
6. Bulk Export (ZIP)
7. History Management
8. Team Accounts (Pro+)

**Technical:**
- API rate limiting
- API key management
- Webhook notifications
- Advanced caching
- Multi-region deployment

**Business:**
- Enterprise plans
- White-label options
- Partnership with Minne
- Expansion to other marketplaces (Etsy, Mercari)

---

## 🎯 SUCCESS METRICS

### Technical KPIs
- **Uptime:** > 99.5%
- **Processing Speed:** < 15s average (standard quality)
- **Success Rate:** > 95% (no errors/timeouts)
- **Safety Block Rate:** < 0.5% false positives

### Business KPIs
- **User Acquisition:** 1,000 users Month 1, 10,000 by Month 6
- **Conversion Rate:** > 5% free to paid
- **Monthly Recurring Revenue (MRR):** ¥500,000 by Month 6
- **Customer Satisfaction:** > 4.5/5 stars
- **Churn Rate:** < 10% monthly

### Quality KPIs
- **First-Time Success:** > 80% (no redo needed)
- **User Satisfaction:** > 85% "satisfied" or "very satisfied"
- **Support Ticket Rate:** < 5% of users

---

## 📝 NOTES & CONSIDERATIONS

### Localization
- All UI in Japanese
- Error messages in Japanese
- Support in Japanese
- Consider English version in Phase 3

### Compliance
- GDPR compliance (for EU users)
- Japan Personal Information Protection Act
- Payment Card Industry (PCI) compliance via Stripe
- Terms of Service review by lawyer

### Scalability
- Start with 1 GPU instance
- Auto-scale to 5 instances max
- Monitor costs carefully
- Set up billing alerts

### Competition Analysis
- **Remove.bg:** $9.99 for 40 images → Our advantage: Unlimited Pro for $15
- **Canva:** $20/month → Our advantage: Specialized for product photos, easier
- **Photoshop:** Complex → Our advantage: One-click simplicity

### Marketing Strategy
- Target Minne seller communities
- Instagram ads (Japanese handcraft hashtags)
- YouTube tutorials
- Partnership with Minne influencers
- Free tier for virality

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-09  
**Owner:** Product Team  
**Status:** Draft - Pending Review
