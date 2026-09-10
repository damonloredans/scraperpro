# Quote — Brand Scrape to Shopify Submission Format

**Prepared for:** Howard (Broad Arrow Tactical — broadarrowtactical.com.au)
**Re:** Product data capture for Oakley SI, Princeton Tec, Crispi (AU) → Shopify import sheet
**Date:** 2026-09-10
**Status:** Estimate. Firms into a fixed quote after the ~1-day discovery + sample sign-off.

---

## 1. Scope

Capture the public catalogue of three brands, deliver each as a Shopify product
import file matching `vertx_product_submission_sample.csv` (a **Matrixify**-style
sheet — see `docs/format-mapping.md`):

| # | Brand | Site | Platform | What we pull |
|---|-------|------|----------|--------------|
| 1 | Oakley SI | oakleysi.com/en-us | SAP Commerce Cloud | Eyewear, apparel, accessories, footwear, goggles, helmets |
| 2 | Princeton Tec | princetontec.com | WooCommerce | Headlamps, handhelds, helmet/marker lights, accessories |
| 3 | Crispi | **crispiaustralia.com.au** | WooCommerce | Full boot range |

> The brief said "Cirspi / cirspiaustralia.com.au" — that spelling does **not**
> resolve (NXDOMAIN). Live site is **crispiaustralia.com.au** (brand *Crispi*).

Per product: handle, title, vendor, description (HTML), SEO title/description,
options (colour / size), one row per variant, SKU, barcode (where public),
weight in grams, image URLs (main + gallery). Output as **draft** products with
**blank price**.

**Pricing is out of scope.** The sample sheet ships with `Variant Price` blank —
you set retail pricing in Shopify. It's also the only option for Oakley SI, whose
prices are the one thing hidden behind the members' login (see §5, Risk 1). If a
price list or a logged-in session is provided later, prices are a small follow-up
pass.

---

## 2. Catalogue size (measured 2026-09-10)

| Brand | Products (approx) | Est. variant rows |
|-------|-------------------|-------------------|
| Oakley SI — Eyewear (sunglasses, eyeglasses, goggles, Rx, accessories) | 957 | |
| Oakley SI — Apparel | 310 | colour × size |
| Oakley SI — Accessories | 139 | |
| Oakley SI — Footwear | 35 | colour × size |
| Oakley SI — Helmets | ~10 | |
| **Oakley SI total** | **~1,300–1,500** | **~6,000–12,000** |
| Princeton Tec | 72 (measured) | ~240 |
| Crispi (AU) | 13 (measured) | ~150 |

---

## 3. Oakley SI — recon findings (2026-09-10)

Loaded several live pages. What we confirmed:

| Question | Finding |
|----------|---------|
| Are product pages visible logged-out? | **Yes.** Title, description, features, technologies, breadcrumb, frame/lens colour, all measurements (lens H/W, bridge, arm, frame width), style code, image gallery — all render without an account. |
| Per-variant barcodes? | **Yes, logged-out.** Each PDP embeds `window.productObj.variants` keyed by UPC, plus a rich `__utagProducts` object (Sku, FrameColor, LensColor, LensTechnology, LensType, Size, ModelCode, LensUPC, image, warranty…). |
| Price? | **No.** Rendered as an empty Hybris `<format:price/>` placeholder for logged-out users. Confirmed login-only. |
| Is there a REST/JSON API (SAP OCC)? | **No.** `/occ/v2/…` falls through to the site search page. HTML scraping only. |
| JS rendering needed? | **Minimal.** Pages are server-side rendered — the HTML already contains the product data. `__utagProducts` is the only piece that needs the page's JS to have run. |
| Bot protection? | **Yes — Akamai.** Plain HTTP clients get HTTP 403 / a "security has been notified" page. Needs a browser-like client (see §6). |

**Net:** everything needed is obtainable except price. The work is a large,
careful HTML crawl behind Akamai — not a blocked site, but a slow one.

---

## 4. Effort estimate (hours)

### Princeton Tec — WooCommerce, public Store API ✅
| Task | Hrs |
|------|-----|
| Recon + field mapping | 1.5 |
| Scraper (`wc/store/v1` products + variations + images) — **done** | 3.0 |
| Per-variant SKU/barcode via product-page variation form (API under-reports) | 2.0 |
| Transform + description cleanup — **done** | 2.0 |
| QA + revision | 3.0 |
| **Subtotal** | **~11** |

### Crispi AU — WooCommerce, public Store API ✅
| Task | Hrs |
|------|-----|
| Recon + field mapping — **done** | 1.0 |
| Scraper + Avada/Fusion-Builder description cleanup — **done** | 3.0 |
| Per-size SKU/barcode via product-page variation form (API returns 0–1 of ~12) | 3.0 |
| EU-size normalisation, width axis — **done** | 1.0 |
| QA + revision | 2.5 |
| **Subtotal** | **~10.5** |

### Oakley SI — SAP Commerce, Akamai, ~1,400 products ⚠️
| Task | Hrs — light path¹ | Hrs — browser path² |
|------|------|------|
| Recon — **done** | 2 | 2 |
| Fetcher: Chrome-impersonation client **or** Playwright + proxy rotation + throttle | 4 | 10 |
| Category crawler (all categories, pagination, colourway URLs) | 5 | 6 |
| PDP parser (name, desc, features, measurements, colours, sizes, UPCs, images from `productObj`/`__utagProducts`) | 9 | 10 |
| Variant explosion (colour × size) + colourway grouping decision | 4 | 4 |
| Transform to Shopify template | 4 | 4 |
| Spec/description cleanup + SEO fields | 3 | 3 |
| QA at scale (validation script + sampling ~1,400 products) | 8 | 8 |
| Revision round | 5 | 6 |
| Buffer: Akamai blocks, re-runs, catalogue changes mid-crawl | 4 | 7 |
| **Subtotal** | **~48** | **~60** |

¹ *Light path*: a Chrome-TLS-impersonating HTTP client (`curl_cffi` / `hrequests`)
gets past Akamai for GET-only page fetches. ~1–2 s/page. **Try first** — discovery
proves whether it works.
² *Browser path*: headless Chromium (Playwright) or driving a real Chrome over the
debug port. ~3–8 s/page, heavier, but the reliable fallback.

### Project overhead
| Task | Hrs |
|------|-----|
| Kickoff, template sign-off, sample delivery | 2 |
| Final consolidation, import dry-run, handover doc | 2 |
| Contingency | 6 |
| **Subtotal** | **~10** |

### Total

| Bucket | Hours |
|--------|-------|
| Princeton Tec | 11 |
| Crispi AU | 10.5 |
| Oakley SI | 48–60 |
| Overhead + contingency | 10 |
| **TOTAL** | **~80–92 hrs** |
| — **already complete** (discovery for all 3, format spec, working prototype for Princeton Tec + Crispi, Oakley recon) | **~10 hrs** |
| **Remaining** | **~70–82 hrs** |

---

## 5. Price (AUD)

Rate basis: **AUD $22 / hr** — skilled scraping/dev work, PH-based, existing
relationship. (For reference, a Western scraping agency would quote this job at
AUD $7,000–10,000.)

### Option A — all three brands

| Line | Hrs | AUD |
|------|-----|-----|
| Discovery + working prototype (2 of 3 brands + Oakley recon) — **done** | 10 | $220 |
| Princeton Tec — finish | 6 | $130 |
| Crispi AU — finish | 7 | $155 |
| Oakley SI — full build | 54 | $1,190 |
| Overhead + contingency | 10 | $220 |
| **Total** | **~87** | **≈ $1,900** |

**Client-facing offer:** *fixed at* **AUD $2,000** for all three brands as
scoped. Out-of-scope work at $22/hr.

### Option B — phased (recommended)

| Phase | Scope | AUD |
|-------|-------|-----|
| 1 | Princeton Tec + Crispi (near done) | **$350** |
| 2 | Oakley SI — **eyewear only** (~957 products) | **$850** |
| 3 | Oakley SI — apparel + accessories + footwear (~450 products) | **$650** |
| | **All phases** | **$1,850** |

Phase 1 delivers in week 1. Client sees the import work before committing to
phases 2–3. Lowest risk for both sides.

### Invoice schedule (Option A)

| Milestone | AUD |
|-----------|-----|
| Discovery + prototype (delivered) | $220 |
| Princeton Tec + Crispi files (week 1) | $290 |
| Oakley SI + final delivery (weeks 2–4) | $1,490 |
| **Total** | **$2,000** |

---

## 6. Timeline

~10 hrs already done. Remaining ~70–82 hrs at ~20 hrs/week → **~4 weeks**.

| Week | Deliverable |
|------|-------------|
| 1 | Discovery sign-off · **Princeton Tec + Crispi files delivered** · Oakley fetcher proven |
| 2 | Oakley category crawl + PDP parser · sample (~50 products) for review |
| 3 | Oakley full crawl + transform · first full file |
| 4 | QA, fixes, final consolidated delivery + handover |

The Oakley crawl itself runs ~20–35 hrs of machine time spread across several
days (batches, not flat-out) — that overlaps weeks 2–3 and isn't hands-on time.

---

## 7. Risks / assumptions to confirm

1. **Oakley SI price is login-gated** (ID.me: active military / gov / first
   responder — we can't register). Everything else is visible logged-out
   (confirmed in recon, §3). Prices later = client price list, or a logged-in
   session we can drive (+6–10 hrs).
2. **Oakley SI Akamai bot protection.** Discovery's first job is to prove the
   light fetcher (`curl_cffi`) works; if not, we fall to a real/headless browser
   (slower, costed as the "browser path" in §4). Real risk of intermittent
   blocks and a slower crawl either way — hence the buffer line.
3. **New / removed products during the crawl.** A crawl is a snapshot over
   several days. Handling: the crawler is re-runnable and idempotent (keyed on
   style code); the final QA pass re-pulls every category listing and diffs
   against what was scraped, so adds/removes in the window are caught and the
   deltas re-scraped before delivery. Oakley adds only a handful of products a
   week, so impact is small. Keeping the sheet current *after* handover = a
   scheduled weekly delta run, quoted separately.
4. **Colourway grouping (Oakley).** Oakley lists many colours of one model as
   separate product pages. Default = mirror the source (one Shopify product per
   colourway). Grouping them into one product with a Colour option adds ~6–10
   hrs. Confirm preference.
5. **Row counts are estimates** from category headers. True variant count (and
   Oakley QA effort) is known only after crawl 1.
6. **Descriptions**: source sites use heavy page-builder HTML. Sample keeps raw
   markup; we default to *cleaned* (strip wrapper `<div>`/`<style>`, keep
   headings/lists/copy). Confirm cleaned vs. raw.
7. **Images**: source image URLs go in `Image Src`; Shopify pulls them on import.
   Re-hosting/renaming = +5–8 hrs.
8. **Barcodes / weights**: Oakley SI exposes per-variant UPCs in the page
   (confirmed). WooCommerce Store API does **not** — we read JSON-LD `gtin` from
   each product page where present, else blank. Weights blank where the source
   omits them.
9. **WooCommerce variation coverage**: Princeton Tec / Crispi public API
   under-reports variations (Crispi returns 0–1 of ~12 sizes). The prototype
   rebuilds the full option grid from parent attributes so *structure* is right,
   but those rows have no SKU until we parse each product page's variation form —
   included in the finish hours (§4).
10. **Product Category / Type / Tags**: blank in the sample. Leave blank, or
    auto-map from source breadcrumbs — confirm.
11. **One revision round** per brand included. Further passes at $22/hr.
12. **Legal / authorisation**: assumes Broad Arrow Tactical has a
    reseller/distributor arrangement with these brands and the right to list
    their catalogues. Client's responsibility to confirm before we publish.
13. **One-time capture.** Ongoing sync quoted separately.

---

## 8. To start

- Confirm the sample sheet is final (and that it's imported via **Matrixify**,
  not the native Shopify importer).
- Cleaned vs. raw descriptions (Risk 6).
- Oakley: mirror source vs. group colourways (Risk 4).
- Prices excluded — confirmed?
- Go-ahead for the ~1-day paid discovery (credited if you proceed).
