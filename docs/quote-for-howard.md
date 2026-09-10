# Product Catalogue -> Shopify Import — Quote

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
**two formats** — the Matrixify layout your sample uses, and a native Shopify CSV
for the built-in importer — so your team can use whichever suits.

Product images are **re-hosted** so they import cleanly (the brand CDNs serve a
format Shopify rejects). Images sit on hosting I run for the import window, then
come down.

I've already test-imported into a scratch store and fixed three issues that would
otherwise have surfaced on your side: variant option handling, image format, and
description formatting.

---

## Progress so far

A working codebase is already in place, not starting from zero:

- **Framework + Princeton Tec + Crispi** — scrapers working, products import cleanly
- **Oakley SI** — product discovery, bot-protection handling, the page parser, and
  the image-hosting pipeline are all **built and proven against a live Shopify
  import**
- Confirmed the Oakley catalogue is **1,541 products**

Remaining: Oakley apparel/footwear size variants, category and colour-name
cleanup, per-variant SKUs for Princeton Tec / Crispi, the full catalogue run,
and QA across all 1,541 products.

---

## Timeline — ~3 weeks

| Week | Deliverable |
|------|-------------|
| 1 | Princeton Tec + Crispi files delivered · Oakley sample (~50 products) for your review |
| 2 | Oakley full catalogue run · first complete file |
| 3 | QA across the catalogue, fixes, final consolidated delivery + handover |

---

## Price (AUD)

**Fixed: $2,000** for all three brands as scoped.

Plus **~$75** for a scraping-proxy subscription needed for the Oakley crawl —
billed at cost with the receipt, cancelled once the job is delivered.

### Phased alternative

| Phase | Scope | AUD |
|-------|-------|-----|
| 1 | Princeton Tec + Crispi | $350 |
| 2 | Oakley SI — eyewear (~960 products) | $900 |
| 3 | Oakley SI — apparel, accessories, footwear, goggles (~580) | $750 |
| | **All phases** | **$2,000** |

Phase 1 lands first so you can see the import working before committing to 2–3.

### Payment

| | AUD |
|--|-----|
| On start | $500 |
| Princeton Tec + Crispi delivered | $400 |
| Oakley SI + final delivery | $1,100 + ~$75 infra |

One revision round per brand is included.

---

## To confirm before I start

1. **Sample sheet** — is the Vertx format final? And do you import via the
   Matrixify app or Shopify's built-in importer? (I deliver both, just want to
   know which to prioritise.)
2. **Crispi** — crispiaustralia.com.au lists 13 products; that's the whole site.
   Crispi globally makes 40+ models. Is the AU site the target, or the full
   range (a different website)?
3. **Descriptions** — cleaned (tidied HTML, keeping headings/lists/copy) or the
   raw source markup as your sample has it?
4. **Oakley colours** — Oakley lists each colour of a model as its own product
   page. Keep that (one Shopify product per colour), or group them into one
   product with a colour dropdown?
5. **Pricing** — the `Variant Price` column is blank in your sample. Options:
   leave it blank and price in Shopify; or I apply a margin formula to Princeton
   Tec's listed prices (Oakley and Crispi don't publish prices, so those stay
   blank regardless).
6. **Authorisation** — confirmation that Broad Arrow is an authorised
   stockist/reseller of these three brands and may list their catalogues and
   product images.
