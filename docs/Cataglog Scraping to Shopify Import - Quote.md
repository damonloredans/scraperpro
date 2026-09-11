# Product Catalogue -> Shopify Import - Quote

**For:** Broad Arrow Tactical
**Brands:** Oakley SI · Princeton Tec · Crispi

---

## Scope

Capture the public catalogue of three brands and deliver each as a Shopify
product import file matching your Vertx sample sheet:

| Brand | Site | Products |
|-------|------|----------|
| Oakley SI | oakleysi.com/en-us | ~1,541 (eyewear, apparel, accessories, footwear, goggles) |
| Princeton Tec | princetontec.com | 72 |
| Crispi | crispiaustralia.com.au | 13 |

Per product: title, description, SEO fields, options (colour / size), one row per
variant, SKU, barcode, weight, and images. Delivered as **draft** products in
**two formats** - the Matrixify layout your sample uses, and a native Shopify CSV
for the built-in importer - so your team can use whichever suits.

Product images are **re-hosted** so they import cleanly - Oakley's media host serves a 
format Shopify rejects, so the images can't be imported straight from oakleysi.com.
See question 6 for how you'd like them hosted.

I've already test-imported into a scratch store and fixed three issues that would
otherwise have surfaced on your side: variant option handling, image format, and
description formatting.

---

## Progress so far

A working codebase is already in place, not starting from zero:

- **Framework + Princeton Tec + Crispi** - dev scrapers working, products import cleanly
- **Oakley SI** - product discovery, bot-protection handling, the page parser, and
  the image-hosting pipeline are all **built and proven against a live Shopify
  import**
- Confirmed the Oakley catalogue is **1,541 products**

Remaining: Oakley apparel/footwear size variants, colour-name cleanup,
finishing Princeton Tec's per-size product codes, the full catalogue run, and
QA across all 1,541 products. (Crispi and Oakley clothing/footwear don't
publish a separate code per size - see question 7.)

---

## Timeline - ~3 weeks

| Week | Deliverable |
|------|-------------|
| 1 | Princeton Tec + Crispi files delivered · Oakley sample (~50 products) for your review |
| 2 | Oakley full catalogue run · first complete file |
| 3 | QA across the catalogue, fixes, final consolidated delivery + handover |

---

## Why Oakley is most of the cost

The three brands are not the same amount of work:

| | Princeton Tec + Crispi | Oakley SI |
|---|---|---|
| Platform | WooCommerce - has a built-in public product feed | Enterprise platform (SAP), **no feed** - every product read from its own web page |
| Products | 85 combined | **1,541** |
| Access | open | **commercial bot protection (Akamai)** - the site actively blocks automated access; needs a paid unblocking service (~$75, folded into the Oakley payment below) |
| Images | import straight from the source | Oakley's image servers send a format Shopify rejects - all **~12,000 images** must be downloaded, converted and re-hosted |
| Effort share | ~15% | ~85% |

Princeton Tec and Crispi are a few days' work. Oakley is a catalogue-scale build:
1,541 pages to read and parse, bot protection to get through, 12,000 images to
re-host, and QA across the whole catalogue - which is the single biggest task,
because at that volume you can't just eyeball it.

## Price (AUD)

**Fixed: $2,000** for all three brands as scoped - includes the ~$75 scraping
service needed for the Oakley crawl (collected as part of the Oakley payment
below, cancelled once the job is delivered).

Open to negotiating this, lower or higher, depending on how you see the
scope of the project.

### Phased alternative

| Phase | Scope | AUD |
|-------|-------|-----|
| 1 | Princeton Tec + Crispi | $350 |
| 2 | Oakley SI - eyewear (~960 products) | $900 |
| 3 | Oakley SI - apparel, accessories, footwear, goggles (~580) | $750 |
| | **All phases** | **$2,000** |

Phase 1 lands first so you can see the import working before committing to 2–3.

### Payment

Work is already underway, the framework, Princeton Tec, and Crispi are built,
and Oakley's been recon'd end to end. Nothing due upfront; payment follows
delivered work:

| | AUD |
|--|-----|
| Princeton Tec + Crispi delivered | $900 |
| Oakley SI + final delivery | $1,100 (includes the ~$75 infra cost) |

One revision round per brand is included.

---

## To confirm before I start

1. **Sample sheet** - is the Vertx format final? And do you import via the
   Matrixify app or Shopify's built-in importer? (I deliver both, just want to
   know which to prioritise.)
2. **Crispi** - crispiaustralia.com.au lists 13 products; that's the whole site.
   Crispi globally makes 40+ models. Is the AU site the target, or the full
   range (a different website)?
3. **Descriptions** - cleaned (tidied HTML, keeping headings/lists/copy) or the
   raw source markup as your sample has it?
4. **Oakley colours** - Oakley lists each colour of a model as its own product
   page. Keep that (one Shopify product per colour), or group them into one
   product with a colour dropdown?
5. **Pricing** - the `Variant Price` column is blank in your sample. Options:
   leave it blank and price in Shopify; or I apply a margin formula to Princeton
   Tec's listed prices (Oakley and Crispi don't publish prices, so those stay
   blank regardless).
6. **Oakley image hosting** - the ~12,000 Oakley images have to be served from
   somewhere Shopify can fetch during import (they can't come straight from
   oakleysi.com). Once a product imports, Shopify copies the image onto its own
   CDN, so it's permanent from then on. The question is where they live *during*
   the import:
   - **A - I host them temporarily** (default): on a bucket I run, deleted after
     your import is confirmed done. $0 cost. Only downside: if you re-import
     later, after teardown, those URLs are gone and the images would need
     re-hosting (small job).
   - **B - I keep the bucket live longer** (e.g. 3–6 months) as a safety net for
     re-imports. Still cheap; I'd pass through the hosting cost (a few AUD/month).
   - **C - your infrastructure**: you give me a storage bucket or a Shopify
     upload token and the images live on your side permanently, under your
     control.
   A is fine for most cases; pick B or C if you expect to re-run the import or
   want the images on your own infra.

7. **Product codes / SKUs.** These vary by brand:
   - **Princeton Tec** publishes a real SKU for each size - those come through.
   - **Crispi** only publishes one code per boot *model* (e.g. `CR92H` for the
     Hunter GTX, all sizes), and two models have no code at all. There is no
     per-size code to capture - it doesn't exist on their site.
   - **Oakley** publishes a code per *colour* (not per size) for clothing and
     footwear; sunglasses have a code per colour as well. Every size does have a
     barcode, which we capture.

   So for Crispi and Oakley clothing/footwear, how do you want the SKU column
   filled? **(a)** repeat the model/colour code on every size row (default);
   **(b)** we generate a size code by pattern, e.g. `CR92H-42`, `CR92H-43`…;
   **(c)** leave it blank and your team assigns SKUs on your side. Most Shopify
   setups do (c) or (a).
