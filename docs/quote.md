# Quote — Brand Catalogue Scrape to Shopify Import Sheets

**Prepared for:** Howard (Broad Arrow Tactical — broadarrowtactical.com.au)
**Re:** Oakley SI, Princeton Tec, Crispi (AU) -> Shopify import files
**Status:** internal working estimate (rev 2 — reflects work completed + de-risked).
Client-facing version: `docs/quote-for-howard.md`.

---

## 1. Scope

Capture the public catalogue of three brands, deliver each as a Shopify product
import file matching `vertx_product_submission_sample.csv` (a **Matrixify** sheet
— see `docs/format-mapping.md`), plus a **native Shopify CSV** for the built-in
importer:

| # | Brand | Site | Platform | Catalogue |
|---|-------|------|----------|-----------|
| 1 | Oakley SI | oakleysi.com/en-us | SAP Commerce + Akamai | **1,541 products** (eyewear, apparel, accessories, footwear, goggles) |
| 2 | Princeton Tec | princetontec.com | WooCommerce | **72 products** |
| 3 | Crispi | **crispiaustralia.com.au** | WooCommerce | **13 products** |

> The brief said "Cirspi / cirspiaustralia.com.au" — that spelling does not
> resolve. Live site is **crispiaustralia.com.au** (brand *Crispi*).

Per product: handle, title, vendor, description (HTML), SEO title/description,
options (colour / size), one row per variant, SKU, barcode, weight in grams,
images (main + gallery). Output as **draft** products.

**Scrape-only engagement.** We deliver the import files + the re-hosted images.
The client's team runs the Shopify import — we have no access to their store.
Our own-store import testing already caught and fixed three issues
that would otherwise have hit their team: Crispi importing 0 products (option
ordering), Oakley images failing (AVIF format), and duplicated measurement text.

**Pricing (`Variant Price`).** We capture what each source *shows*:

| Brand | Source price | In the sheet |
|-------|--------------|--------------|
| Princeton Tec | yes — public API | source RRP **in USD** |
| Crispi | no — API returns `0` for variable products | blank |
| Oakley SI | no — login-gated | blank |

So Oakley + Crispi land **blank**, Princeton Tec lands as **USD RRP**. The client
decides how retail price is set — see section 8.

---

## 2. What's already built and proven

Roughly **32 hours in**. A working codebase (~1,800 lines) — not slideware:

| Piece | Status |
|-------|--------|
| Reusable framework — fetcher / discovery / transform / image pipeline / two output formats / interactive `run.bat` | ✅ |
| **Princeton Tec** scraper | ✅ 72 products, USD prices, imports clean |
| **Crispi** scraper | ✅ 13 products, imports clean (per-size SKUs pending — see Risk 9) |
| **Oakley — discovery** | ✅ sitemap, all 1,541 URLs in **one request** (was a ~160-request crawl) |
| **Oakley — anti-bot** | ✅ ScraperAPI, tested end to end — **1 credit / request**, full catalogue ≈ 1,542 credits = **within the free trial**. Circuit breaker + partial-write for any hiccup. |
| **Oakley — PDP parser** | ✅ title, breadcrumb, cleaned description + measurements, SEO text, images, per-colour SKU + barcode. **Proven in a live Shopify import.** |
| **Oakley — image re-hosting** | ✅ download (parallel) -> JPEG -> our Cloudflare R2 bucket -> rewrite `Image Src`. Proven in a live Shopify import. **$0** (R2 free tier). |

**The three things that could have blown the timeline — Akamai, image hosting,
and product discovery — are done.** What remains is catalogue-scale build and QA.

---

## 3. What's left

| Task | Hrs |
|------|-----|
| **Oakley: size variants** — parser currently handles eyewear (one-size). Apparel (310), footwear (35) and goggles need the size axis parsed from the PDP + colour×size explosion | 8–10 |
| **Oakley: category / type** — breadcrumb currently grabs promo-collection names; map to real categories | 3 |
| **Oakley: colour names** — replace fallback labels (`Matte Black (E655)`) with real swatch names from the page | 3 |
| **Oakley: colourway grouping** — decide + implement (mirror source vs. group into one product with a Colour option — Risk 6) | 0–4 |
| **Woo (PT + Crispi): per-variant SKUs** — parse each product page's variation form (Store API under-reports — Risk 9) | 4 |
| **Full Oakley run + image re-host at scale** — ~3.5 hrs unattended machine time, then verify ~12k images landed | 4 |
| **QA across 1,541 products** — validation script + sampling + fixing bad rows. *The biggest single item.* | 12 |
| Transform / SEO polish at scale | 3 |
| Weights (blank now — Risk 10) | 2 |
| Revision round (one per brand, included) | 5 |
| Buffer — site changes, re-runs, edge cases | 4 |
| Consolidation, import dry-run notes, handover doc | 3 |
| **Remaining** | **~55–60 hrs** |

**Total project: ~32 done + ~57 left ≈ ~90 hrs** — unchanged from the original
estimate. The *risk* dropped a lot; the *work* didn't, because scope grew (two
output formats, the R2 infrastructure, `run.bat`, parallel pipeline, `--fast`
mode) and the apparel size-variant work was under-costed first time round.

---

## 4. Price (AUD)

Rate: **AUD $22 / hr** — skilled scraping/dev work, PH-based, existing
relationship. A Western scraping agency quotes this kind of job at
**AUD $7,000–10,000**.

| Line | Hrs | AUD |
|------|-----|-----|
| Built + proven to date (framework, 3 parsers, anti-bot, image pipeline, live testing) | 32 | $700 |
| Princeton Tec — finish (SKUs, QA) | 4 | $90 |
| Crispi — finish (SKUs, QA) | 5 | $110 |
| Oakley SI — remaining (size variants, category/colour, full run, scale QA, revision) | 40 | $880 |
| Overhead + contingency | 8 | $175 |
| **Labour total** | **~89** | **≈ $2,000** |
| Data infrastructure | — | **~AUD $75** — one month of ScraperAPI's Hobby plan (USD $49 / 100k credits) covers the full crawl **plus dev re-runs** with huge headroom; cancelled on delivery. R2 image hosting is free tier ($0). Billed at cost with the receipt. |

**Client-facing offer:** *fixed at* **AUD $2,000** labour + **~$75 infrastructure
at cost** for all three brands as scoped. Out-of-scope work at $22/hr.

### Phased option (lower risk for both sides)

| Phase | Scope | AUD |
|-------|-------|-----|
| 1 | Princeton Tec + Crispi — delivered in week 1 | **$350** |
| 2 | Oakley SI — **eyewear** (~957 products) | **$900** |
| 3 | Oakley SI — apparel + accessories + footwear + goggles (~580) | **$750** |
| | **All phases** | **$2,000** |

Phase 1 lands first so the client sees the import working before committing to
2–3.

### Invoice schedule

| Milestone | AUD |
|-----------|-----|
| On sign-off (work to date) | $500 |
| Princeton Tec + Crispi files (week 1) | $400 |
| Oakley SI + final consolidated delivery | $1,100 |
| Infrastructure (ScraperAPI receipt) | ~$75 at cost |
| **Total** | **$2,000 + ~$75** |

---

## 5. Timeline

~32 hrs done, ~57 left at ~20 hrs/week -> **~3 weeks**.

| Week | Deliverable |
|------|-------------|
| 1 | Sign-off · **Princeton Tec + Crispi files delivered** · Oakley eyewear sample (~50 products) for review |
| 2 | Oakley size variants + category/colour · **full 1,541-product run** · first complete file |
| 3 | QA across the catalogue, fixes, final consolidated delivery + handover |

The full Oakley crawl is **~3.5 hrs of unattended machine time in one sitting**
(scrape ~2.3 hrs via ScraperAPI + parallel image download ~40 min + R2 upload
~30 min) — not a multi-day batch job. It slots into week 2 and needs no
babysitting.

---

## 6. Risks / assumptions to confirm

1. **Oakley price is login-gated** (ID.me: active military / gov / first
   responder — we can't register). Everything else renders logged-out (proven).
   Prices later = a client price list, or a logged-in session we can drive
   (+6–10 hrs).
2. **Oakley Akamai — no longer a project risk.** ScraperAPI was tested end to
   end to end: clean pages, real product data, **1 credit per request**.
   One full crawl ≈ 1,542 credits; the project (with dev re-runs) needs
   ~6–10k, so we run on one month of the **Hobby plan** ($49 / 100k credits),
   cancelled on delivery — the infra line in section 4. Circuit breaker +
   partial-write mean a hiccup costs ~30 s and never loses scraped work.
3. **Detection / legal** *(not legal advice).* Akamai flags traffic/IPs
   automatically; worst realistic case was a temporary IP block, now moot with
   ScraperAPI. We fetch only public, non-logged-in pages. The real exposure is
   **copyright** — the brands own their photos and copy; publishing them is fine
   *if Broad Arrow is an authorised stockist* of each. **Protect yourself:** get
   that in writing plus an indemnity clause (Risk 12).
4. **Crispi = 13 products.** Verified — that's the entire AU site. Crispi
   globally makes 40+ models; if the client wants the full range that's a
   different site (crispi.com), re-scoped. **Confirm which catalogue.**
5. **Size variants (Oakley apparel/footwear/goggles).** The parser handles
   eyewear (one-size) today. ~580 products need the size axis parsed from the
   PDP and exploded colour×size. Costed in section 3 (~8–10 hrs).
6. **Colourway grouping (Oakley).** Oakley lists colours of one model as
   separate product pages. Default = mirror the source (one Shopify product per
   colourway). Grouping into one product with a Colour option adds ~4 hrs.
   Confirm preference.
7. **Descriptions.** Source sites use heavy page-builder HTML. We default to
   *cleaned* (strip wrapper divs/styles, keep headings/lists/copy). Confirm
   cleaned vs. raw.
8. **Barcodes / weights.** Oakley exposes per-variant UPCs in the page
   (captured). Weights aren't on the PDP -> blank unless a source is provided.
9. **WooCommerce variation coverage.** Princeton Tec / Crispi's public API
   under-reports variations (Crispi returns 0–1 of ~12 sizes). The scraper
   rebuilds the full option grid so *structure* is right, but those rows have no
   SKU until we parse each product page's variation form — in the finish hours.
10. **Product Category / Type / Tags** — blank in the sample. Leave blank, or
    auto-map from source breadcrumbs. Confirm.
11. **New / removed products mid-project.** The crawl is now ~3.5 hrs, so this
    barely applies; the final QA pass re-checks the sitemap and picks up any
    delta before delivery. Keeping the sheet current *after* handover = a
    scheduled weekly delta run, quoted separately.
12. **Legal / authorisation.** Assumes Broad Arrow has a reseller arrangement
    with all three brands and the right to list their catalogues and use their
    photos/copy. Get it in writing + an indemnity clause. Client's
    responsibility.
13. **Image bucket.** We host the ~12k Oakley images on our Cloudflare R2 for the
    import window, then delete. Free tier, $0. One date needed from the client:
    when their import is done.
14. **Import method.** Sample is a **Matrixify** sheet (needs the Matrixify app).
    We also ship a **native Shopify CSV** for the free built-in importer — the
    client's team picks.
15. **One revision round** per brand included. Further passes at $22/hr.
16. **One-time capture.** Ongoing sync quoted separately.

---

## 7. To start

- Confirm the sample sheet is final; Matrixify or native importer (we deliver
  both).
- **Crispi**: AU site = 13 products — is that the target, or the full global
  range? (Risk 4)
- Cleaned vs. raw descriptions (Risk 7).
- Oakley: mirror source vs. group colourways (Risk 6).
- **Pricing** — pick one:
  1. Leave `Variant Price` blank, price in Shopify after import.
  2. Give us a **margin formula** for Princeton Tec's USD RRP (e.g.
     `retail = RRP × 1.4`), and an AUD FX rate.
  3. Supply a cost / price list (CSV keyed by SKU/UPC) to merge.
- Confirm Broad Arrow is authorised to sell + list all three brands, in writing
  (Risk 3 / 12).
- Go-ahead + first invoice.
