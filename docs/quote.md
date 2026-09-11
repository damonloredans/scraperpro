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
| **Crispi** scraper | ✅ 13 products, imports clean. Per-size SKUs don't exist at source (Risk 9) — model-level SKU only, a client decision not a build task |
| **Oakley — discovery** | ✅ sitemap, all 1,541 URLs in **one request** (was a ~160-request crawl) |
| **Oakley — anti-bot** | ✅ ScraperAPI, tested end to end — **1 credit / request**, full catalogue ≈ 1,542 credits = **within the free trial**. Circuit breaker + partial-write for any hiccup. |
| **Oakley — PDP parser** | ✅ title, category/Type (from the stable taxonomy code, not the promo breadcrumb), cleaned description + measurements, SEO text, images, per-colour SKU + barcode. **Proven in a live Shopify import.** |
| **Oakley — image re-hosting** | ✅ download (parallel) -> JPEG -> our Cloudflare R2 bucket -> rewrite `Image Src`. Proven in a live Shopify import. **$0** (R2 free tier). |

**The three things that could have blown the timeline — Akamai, image hosting,
and product discovery — are done.** What remains is catalogue-scale build and QA.

---

## 3. What's left

| Task | Hrs |
|------|-----|
| **Oakley: size variants** — parser currently handles eyewear (one-size). Apparel (310), footwear (35) and goggles need the size axis parsed from the PDP + colour×size explosion | 8–10 |
| ~~**Oakley: category / type**~~ — **done 2026-09-10.** `_product_type()` maps the `utag_data.product_category` code to a Shopify Type (breadcrumb was promo junk for ~half of softgoods). `validate.py` promo-Type smells 13/20 → 0 on live samples. Segment map extends during QA. | ~~3~~ → 0.5 (QA top-ups) |
| **Oakley: colour names** — swatch links carry the real name in `title="Blackout"` on the main page; `utag` FrameColor is empty for softgoods. Swap the label source | 3 |
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

**Client-facing offer:** *fixed at* **AUD $2,000 total** for all three brands as
scoped — infra (~$75) folded into that number, not billed as an add-on, and
collected as part of the Oakley milestone. Out-of-scope work at $22/hr.
Pitched to Howard as negotiable (up or down) — audition, hold the relationship
over the exact figure.

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

No on-sign-off deposit — the ~32 hrs of work to date (framework, PT + Crispi,
Oakley recon) is unbilled and absorbed into the two delivery milestones below,
not charged separately. Lower cash-flow cushion for us, but no upfront ask of
the client while this is still an audition.

| Milestone | AUD |
|-----------|-----|
| Princeton Tec + Crispi files (week 1) | $900 |
| Oakley SI + final consolidated delivery | $1,100 (incl. ~$75 ScraperAPI, receipt on request) |
| **Total** | **$2,000** |

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
   PDP and exploded colour×size. **Recon 2026-09-10 confirms the data is in the
   SSR HTML** — `<label class="size-button" data-size data-variant data-hasstock>`,
   one per size with a per-size barcode — so this is straight parser work, no
   extra requests, no blocked data. Costed in section 3 (~8–10 hrs).
6. **Colourway grouping (Oakley).** Oakley lists colours of one model as
   separate product pages. Default = mirror the source (one Shopify product per
   colourway). Grouping into one product with a Colour option adds ~4 hrs.
   Confirm preference.
7. **Descriptions.** Source sites use heavy page-builder HTML. We default to
   *cleaned* (strip wrapper divs/styles, keep headings/lists/copy). Confirm
   cleaned vs. raw.
8. **Barcodes / weights.** Oakley exposes per-variant UPCs in the page — eyewear
   via `utag_data.Products`, softgoods via the size buttons' `data-variant`
   (verified 2026-09-10), so barcodes are covered across the catalogue. Weights
   are **not on the PDP anywhere** (confirmed) -> blank unless the client
   provides a source. Same for Crispi/PT weights where the Store API omits them.
9. **Per-variant SKUs — verified 2026-09-10, and the brands differ.**
   - **Princeton Tec:** real per-size SKUs exist; the Store API exposes most
     (≈3/4), the rest come from the product page. Finish as costed.
   - **Crispi:** *no per-size SKUs exist to scrape.* Store API `variations[]` is
     empty for most products; the one product exposing all 11 variation objects
     returns the same model code (`CR75T`) on every size; no
     `data-product_variations` on the PDP; JSON-LD has only the parent SKU; the
     `?wc-ajax=get_variation` endpoint is bot-walled; the sitemap has no SKU
     data. Finest SKU available = the **model-level code** (`CR65V-1`, `CR92H`…),
     present for 11/13, blank for both Futuras. **Client decision** (put to
     Howard): (a) model-level SKU on every variant row — default; (b) synthesise
     `CR75T-38`… by convention; (c) leave blank, Broad Arrow assigns. This
     removes the "parse the variation form" line from Crispi's finish hours —
     there's nothing to parse.
   - **Oakley softgoods:** same — the size buttons carry `data-sku=""`; only the
     colour-level SKU (`FOA409350-02E`) exists. Per-size **barcode** is present
     (`data-variant`), per-size SKU is not.
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
13. **Image hosting — client decision (BLOCKER).** The ~12k Oakley images must
    be served from somewhere Shopify can fetch *during* the import (not straight
    from oakleysi.com — AVIF). Shopify copies each image to its own CDN on a
    successful import, so hosting is only needed for the import window itself.
    Options to put to the client (see quote-for-howard.md Q7):
    - **A (default):** our Cloudflare R2, deleted once they confirm the import is
      done. $0. Risk: a re-import after teardown needs images re-hosted (~2 hrs).
    - **B:** we keep R2 live 3–6 months as a re-import safety net. ~AUD $0–5/mo
      (still likely free tier), passed through.
    - **C:** client's own bucket or a Shopify upload token — images live on their
      side permanently. If a Shopify token: we can upload straight to their
      Shopify Files and skip our bucket entirely (+~2 hrs, but removes our
      hosting dependency). Conflicts slightly with "scrape-only, no store
      access" — needs a scoped token.
    Confirm which before the full run. Default A unless they say otherwise.
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
- **Oakley image hosting** — A (our temp bucket, default) / B (we keep it live
  3–6 mo) / C (their bucket or a Shopify token). Risk 13.
- **Pricing** — pick one:
  1. Leave `Variant Price` blank, price in Shopify after import.
  2. Give us a **margin formula** for Princeton Tec's USD RRP (e.g.
     `retail = RRP × 1.4`), and an AUD FX rate.
  3. Supply a cost / price list (CSV keyed by SKU/UPC) to merge.
- Confirm Broad Arrow is authorised to sell + list all three brands, in writing
  (Risk 3 / 12).
- Go-ahead + first invoice.
