# Quote — Brand Scrape to Shopify Submission Format

**Prepared for:** Howard (Broad Arrow Tactical — broadarrowtactical.com.au)
**Re:** Product data capture for Oakley SI, Princeton Tec, Crispi (AU) -> Shopify import sheet
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
weight in grams, image URLs (main + gallery). Output as **draft** products.

**Pricing.** The sample sheet ships with `Variant Price` blank. We now capture
what each source site *shows*:

| Brand | Price available? | What we put in `Variant Price` |
|-------|------------------|-------------------------------|
| Princeton Tec | Yes — public API | source RRP **in USD** (Broad Arrow is AU -> needs FX + margin, or overwrite) |
| Crispi AU | No — the store API returns `0` for variable products (real prices are on the product page, same gap as SKUs) | blank until product-page parsing is added |
| Oakley SI | No — login-gated (`<format:price/>` placeholder logged-out) | blank |

So realistically Oakley + Crispi land **blank** and Princeton Tec lands as **USD
RRP**. The client needs to decide how retail price is set — see §8. Options:
leave blank and price in Shopify; give us a **margin formula** (e.g.
`retail = RRP × 1.4`, or `cost ÷ (1 − 0.35)`) to apply; or supply a cost/price
list to merge.

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
| Per-variant barcodes? | **Yes, logged-out.** Each PDP embeds `utag_data.Products = {<UPC>: {Sku, FrameColor, LensColor, LensTechnology, LensType, Category, ModelName, …}}` — parsed with a brace-matcher (JS object literal, unquoted numeric keys). |
| Price? | **No.** Empty Hybris `<format:price/>` placeholder for logged-out users. Confirmed login-only. |
| Is there a REST/JSON API (SAP OCC)? | **No.** `/occ/v2/…` falls through to the site search page. HTML scraping only. |
| JS rendering needed? | **No** for the core data — pages are server-side rendered. |
| Bot protection? | **Yes — Akamai.** `requests` -> 403. `curl_cffi` (Chrome TLS impersonation) -> clean 200s + full data for ~40–50 requests, then a JS-challenge stub. Sustained crawling needs cookie-seeding / proxies / an unblocker — see Risk 2. |
| Does the parser actually work? | **Yes.** Built and ran end to end during recon — pulled real products (Standard Issue Holbrook USA Flag Collection, Meta Vanguard) with title, breadcrumb -> Type, cleaned description + measurements, SEO text, 10–15 images, per-colour Sku/UPC — before hitting the volume block. |

**Net:** the parser is done and everything except price is obtainable. The open
problem is **crawl volume vs. Akamai**, not "can we read the site" — see Risk 2
for the fix and its pass-through cost.

---

## 4. Effort estimate (hours)

### Princeton Tec - WooCommerce, public Store API
| Task | Hrs |
|------|-----|
| Recon + field mapping | 1.5 |
| Scraper (`wc/store/v1` products + variations + images) — **done** | 3.0 |
| Per-variant SKU/barcode via product-page variation form (API under-reports) | 2.0 |
| Transform + description cleanup — **done** | 2.0 |
| QA + revision | 3.0 |
| **Subtotal** | **~11** |

### Crispi AU - WooCommerce, public Store API
| Task | Hrs |
|------|-----|
| Recon + field mapping — **done** | 1.0 |
| Scraper + Avada/Fusion-Builder description cleanup — **done** | 3.0 |
| Per-size SKU/barcode via product-page variation form (API returns 0–1 of ~12) | 3.0 |
| EU-size normalisation, width axis — **done** | 1.0 |
| QA + revision | 2.5 |
| **Subtotal** | **~10.5** |

### Oakley SI - SAP Commerce, Akamai, ~1,400 products
| Task | Hrs — light path¹ | Hrs — browser path² |
|------|------|------|
| Recon — **done** | 2 | 2 |
| Fetcher: Chrome-impersonation client **or** Playwright + proxy rotation + throttle | 4 | 10 |
| Category crawler (all categories, pagination, colourway URLs) | 5 | 6 |
| PDP parser (name, desc, features, measurements, colours, sizes, UPCs) — **built + tested** | 9 | 10 |
| Variant explosion (colour × size) + colourway grouping decision | 4 | 4 |
| **Image rehosting** — download ~14k images, bulk-upload to Shopify Files or attach via Admin API, rewrite `Image Src` (Oakley's CDN serves AVIF; Shopify rejects it and won't take the query-string workaround — see Risk 15) | 6 | 6 |
| Transform to Shopify template | 4 | 4 |
| Spec/description cleanup + SEO fields | 3 | 3 |
| QA at scale (validation script + sampling ~1,400 products) | 8 | 8 |
| Revision round | 5 | 6 |
| Buffer: Akamai blocks, re-runs, catalogue changes mid-crawl | 4 | 7 |
| **Subtotal** | **~54** | **~66** |

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
| Oakley SI | 54–66 |
| Overhead + contingency | 10 |
| **TOTAL** | **~85–97 hrs** |
| — **already complete** (discovery for all 3, format spec, working Princeton Tec + Crispi + Oakley parser, live import testing) | **~13 hrs** |
| **Remaining** | **~72–84 hrs** |

---

## 5. Price (AUD)

Rate basis: **AUD $22 / hr** — skilled scraping/dev work, PH-based, existing
relationship. (For reference, a Western scraping agency would quote this job at
AUD $7,000–10,000.)

### Option A — all three brands

| Line | Hrs | AUD |
|------|-----|-----|
| Discovery + working prototype (all 3 parsers + live import testing) — **done** | 13 | $285 |
| Princeton Tec — finish | 6 | $130 |
| Crispi AU — finish | 7 | $155 |
| Oakley SI — full build (incl. image rehosting) | 55 | $1,210 |
| Overhead + contingency | 10 | $220 |
| **Labour total** | **~91** | **≈ $2,000** |
| Data infrastructure (unblocker API / residential proxies for Oakley) — **billed at cost** | — | **$0–150** |

The infrastructure line is a **pass-through**: Oakley SI's Akamai protection needs
an unblocker service (Zyte / ScraperAPI / Bright Data) or residential proxies to
crawl ~1,400 products. One-time, ~USD $15–100 depending on provider; free-tier
credits may cover it entirely. Cancelled after the scrape. Not needed for
Princeton Tec or Crispi.

**Client-facing offer:** *fixed at* **AUD $2,000** for all three brands as scoped
(labour), **plus infrastructure at cost (capped at AUD $150)**. Out-of-scope work
at $22/hr.

### Option B — phased (recommended)

| Phase | Scope | AUD |
|-------|-------|-----|
| 1 | Princeton Tec + Crispi (near done) | **$350** |
| 2 | Oakley SI — **eyewear only** (~957 products) | **$850** + infra at cost |
| 3 | Oakley SI — apparel + accessories + footwear (~450 products) | **$650** |
| | **All phases** | **$1,850** + infra (≤ $150) |

Phase 1 delivers in week 1. Client sees the import work before committing to
phases 2–3. Lowest risk for both sides.

### Invoice schedule (Option A)

| Milestone | AUD |
|-----------|-----|
| Discovery + prototype (delivered) | $220 |
| Princeton Tec + Crispi files (week 1) | $290 |
| Oakley SI + final delivery (weeks 2–4) | $1,490 |
| Data infrastructure (receipts attached) | at cost, ≤ $150 |
| **Total** | **$2,000 + infra** |

---

## 6. Timeline

~10 hrs already done. Remaining ~70-82 hrs at ~20 hrs/week -> **~4 weeks**.

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
2. **Oakley SI Akamai bot protection — tested 2026-09-10.** A Chrome-TLS
   impersonating client (`curl_cffi`) gets clean 200s and full page data for the
   **first ~40–50 requests**, then Akamai switches to a JS-challenge stub (still
   HTTP 200, no product data). The parser is built and pulled real products end
   to end before the block; it is a *volume* problem, not a "can't read the site"
   problem. To crawl all ~1,400 products one of these is needed (cheapest first):
   (a) seed the session with Akamai cookies from one real-browser visit, refresh
   every ~30–60 min (~1–2 s/page between refreshes); (b) residential proxy
   rotation (~USD $5–15 bandwidth for the catalogue); (c) an unblocker API
   (ScraperAPI / Zyte / BrightData, ~USD $50–150). Costed as the "browser path"
   spread in §4; the proxy/unblocker fee is a pass-through, not in the hours.
3. **Detection / legal exposure** *(not legal advice — see a lawyer if unsure).*
   - **Detection:** Akamai flags *traffic patterns and IPs*, automatically. The
     "security has been notified" text is boilerplate, not an incident report.
     Realistic worst case = a temporary IP block. Not a personal-threat situation.
   - **Scraping itself:** we fetch only public, non-logged-in pages — no login
     bypass, no checkout, no clickwrap ToS accepted — at a polite rate, once.
     Public-data scraping is generally not a criminal matter (US: *hiQ*,
     *Van Buren*; AU has no anti-scraping statute). A browsewrap ToS breach is a
     *contract* issue whose usual remedy is "stop," not damages.
   - **The real exposure is copyright** — Oakley/Luxottica, Princeton Tec and
     Crispi own their product photos and marketing copy. Publishing them in Broad
     Arrow's store is a reproduction. This is fine *if Broad Arrow is an
     authorised reseller/stockist* of each brand (which is the whole premise of
     the store); it is the client's problem if not.
   - **Protect yourself:** get Howard's written confirmation that Broad Arrow is
     authorised to sell and list all three brands, and put a clause in the
     engagement that the client warrants this and indemnifies you for
     third-party IP claims arising from the data. The contractor doing the
     technical work is far less exposed than the party publishing commercially.
4. **Crispi AU catalogue is only 13 products.** Verified against
   crispiaustralia.com.au's store API + category counts — that is the *entire*
   site. Crispi globally makes 40+ models; if the client expects the full range,
   that means scraping crispi.com / crispioutdoor.com instead (different site,
   re-scope). **Confirm which catalogue Howard wants.**
5. **New / removed products during the crawl.** A crawl is a snapshot over
   several days. Handling: the crawler is re-runnable and idempotent (keyed on
   style code); the final QA pass re-pulls every category listing and diffs
   against what was scraped, so adds/removes in the window are caught and the
   deltas re-scraped before delivery. Oakley adds only a handful of products a
   week, so impact is small. Keeping the sheet current *after* handover = a
   scheduled weekly delta run, quoted separately.
6. **Colourway grouping (Oakley).** Oakley lists many colours of one model as
   separate product pages. Default = mirror the source (one Shopify product per
   colourway). Grouping them into one product with a Colour option adds ~6–10
   hrs. Confirm preference.
7. **Row counts are estimates** from category headers. True variant count (and
   Oakley QA effort) is known only after crawl 1.
8. **Descriptions**: source sites use heavy page-builder HTML. Sample keeps raw
   markup; we default to *cleaned* (strip wrapper `<div>`/`<style>`, keep
   headings/lists/copy). Confirm cleaned vs. raw.
9. **Images**: source image URLs go in `Image Src`; Shopify pulls them on import.
   Re-hosting/renaming = +5–8 hrs.
10. **Barcodes / weights**: Oakley SI exposes per-variant UPCs in the page
    (confirmed). WooCommerce Store API does **not** — we read JSON-LD `gtin` from
    each product page where present, else blank. Weights blank where the source
    omits them.
11. **WooCommerce variation coverage**: Princeton Tec / Crispi public API
    under-reports variations (Crispi returns 0–1 of ~12 sizes). The prototype
    rebuilds the full option grid from parent attributes so *structure* is right,
    but those rows have no SKU until we parse each product page's variation form —
    included in the finish hours (§4).
12. **Product Category / Type / Tags**: blank in the sample. Leave blank, or
    auto-map from source breadcrumbs — confirm.
13. **One revision round** per brand included. Further passes at $22/hr.
14. **Legal / authorisation**: assumes Broad Arrow Tactical has a
    reseller/distributor arrangement with these brands and the right to list
    their catalogues and use their photos/copy. Get it in writing + an indemnity
    clause (see Risk 3). Client's responsibility.
15. **Oakley images must be rehosted.** `assets*.oakley.com` serves AVIF (via
    Accept negotiation); Shopify rejects AVIF and won't honour the query-string
    workaround through the CSV importer. So Oakley images have to be downloaded
    (~14k of them) and either bulk-uploaded to Shopify Files or attached via the
    Admin API at product-create time, with the CSV pointing at Shopify URLs. The
    scraper's `download_images()` handles the download; the upload/rewrite is
    costed in §4. **Woo (Princeton Tec, Crispi) images import fine by URL.**
16. **Import method.** The sample is a **Matrixify** sheet — imports via the
    Matrixify app. `run.py --format shopify` also emits a native Shopify CSV for
    the built-in importer. Live testing: Princeton Tec imports clean; the Crispi
    "0 products" issue (options) and Oakley images (above) are handled.
17. **One-time capture.** Ongoing sync quoted separately.

---

## 8. To start

- Confirm the sample sheet is final (and that it's imported via **Matrixify**,
  not the native Shopify importer).
- **Crispi**: the AU site has only 13 products — is that the target, or the full
  global Crispi range (different site)? (Risk 4)
- Cleaned vs. raw descriptions (Risk 8).
- Oakley: mirror source vs. group colourways (Risk 6).
- **Pricing** — pick one:
  1. Leave `Variant Price` blank, set all pricing in Shopify after import.
  2. Give us a **margin formula** to apply to the source RRP we capture
     (e.g. `retail = RRP × 1.4`, or `retail = cost ÷ (1 − margin%)`), and say
     whether Princeton Tec USD should be FX-converted to AUD (and at what rate).
  3. Supply a cost or price list (CSV, keyed by SKU/UPC) to merge in.
  Note: only Princeton Tec has a source price via API; Crispi + Oakley land blank
  regardless (see §1).
- Confirm Broad Arrow is authorised to sell + list all three brands, in writing
  (Risk 3 / 14).
- Go-ahead for the ~1-day paid discovery (credited if you proceed).
