# Shopify Submission Format — Column Map

Source of truth: `vertx_product_submission_sample.csv` (Vertx sample supplied by Howard).

## What kind of file is this?

It is **not** a native Shopify product CSV. Column names like
`Variant Inventory Qty`, `Included / Australia`, `Included / International`, the
free column ordering (option values sitting after `Variant Compare At Price`),
the blank unnamed column, and the duplicated `Variant Inventory Tracker` are all
signatures of a **Matrixify (Excelify)** export/import sheet.

Practical consequences:
- Column **order does not matter** to Matrixify; column **names** do.
- You can omit columns you have no data for.
- The multi-row pattern (extra rows that carry only `Handle` + image columns) is
  a Matrixify convention for attaching extra images / extra variants.
- `Included / <Market>` columns map to Shopify Markets catalog inclusion.

We will reproduce the exact header row from the sample verbatim.

## Row model

```
Product "vertx-10-inch-md-weight-vaporcore-crew-sock"
├─ Row 1  → product-level fields + variant 1 + image 1
├─ Row 2  → Handle + variant 2 fields + image 2
├─ Row 3  → Handle + variant 3 fields + image 3
├─ ...    (one row per variant)
└─ Row N  → Handle + Image Src + Image Position only   (gallery overflow images)
```

- **Product-level fields** (Title, Body, Vendor, SEO, Options names, Status,
  Weight Unit, Markets…) appear **only on the first row** of each product.
- **Variant-level fields** repeat on every variant row.
- Extra image rows carry **only** `Handle`, `Image Src`, `Image Position`
  (and optionally `Variant Image`).

## Column-by-column

| # | Column | Level | Fill rule | From sample |
|---|--------|-------|-----------|-------------|
| 1 | `Handle` | product (every row) | `slug(vendor + " " + title)`, lowercase, `[a-z0-9-]`, dedupe with `-2` | `vertx-10-inch-md-weight-vaporcore-crew-sock` |
| 2 | `Title` | product (row 1) | Title Case; sample prefixes brand → `Vertx …` | `Vertx 10 Inch Md Weight Vaporcore Crew Sock` |
| 3 | `Body (HTML)` | product (row 1) | Source description HTML. Sample keeps raw page-builder markup; our default is **cleaned** (strip `<style>`, wrapper `<div>`, keep `<h2>/<h3>/<ul>/<li>/<p>`). | large HTML blob |
| 4 | `Vendor` | product (row 1) | Brand name | `Vertx` |
| 5 | `Tags` | product (row 1) | Comma-separated. **Blank in sample** → leave blank unless client wants breadcrumb/category tags | *(empty)* |
| 6 | `SEO Title` | product (row 1) | Pattern `"{Title} {Vendor}"` (sometimes `+ " Official Site"`) | `Vertx 10 Inch Md Weight Vaporcore Crew Sock Vertx` |
| 7 | `SEO Description` | product (row 1) | ~150–320 char plain-text lede pulled from the description | `Designed for Vertx® by the masters of merino …` |
| 8 | `Published` | product (row 1) | `TRUE` in sample (note: `Status` is still `draft` — Matrixify lets both coexist; product stays unpublished until activated) | `TRUE` |
| 9 | `Variant Inventory Qty` | variant | `0` on row 1; blank on later rows in sample | `0` |
| 10 | `Variant Inventory Policy` | variant (every variant row) | `deny` | `deny` |
| 11 | `Variant Inventory Tracker` | variant (every variant row) | `shopify` | `shopify` |
| 12 | `Variant Fulfillment Service` | variant (every variant row) | `manual` | `manual` |
| 13 | *(unnamed blank column)* | – | always empty; keep for header parity | *(empty)* |
| 14 | `Gift Card` | product (row 1) | `FALSE` | `FALSE` |
| 15 | `Status` | product (row 1) | `draft` — everything imports as draft for review | `draft` |
| 16 | `Variant Weight Unit` | product (row 1) | `g` | `g` |
| 17 | `Included / Australia` | product (row 1) | `TRUE` | `TRUE` |
| 18 | `Included / International` | product (row 1) | `TRUE` | `TRUE` |
| 19 | `Product Category` | product (row 1) | Shopify standard taxonomy. **Blank in sample** → leave blank (or map later) | *(empty)* |
| 20 | `Type` | product (row 1) | Custom type. **Blank in sample** | *(empty)* |
| 21 | `Option1 Name` | product (row 1) | `Colour` for multi-colour products; `Title` for single-variant | `Colour` |
| 22 | `Option1 Linked To` | product (row 1) | blank (only used for combined/linked listings) | *(empty)* |
| 23 | `Option2 Name` | product (row 1) | `Size ` (trailing space preserved from sample) when sized | `Size ` |
| 24 | `Option2 Linked To` | product (row 1) | blank | *(empty)* |
| 25 | `Option3 Name` | product (row 1) | blank unless a 3rd axis (e.g. width) exists | *(empty)* |
| 26 | `Option3 Linked To` | product (row 1) | blank | *(empty)* |
| 27 | `Variant Compare At Price` | variant | **Blank in sample** (client sets pricing) | *(empty)* |
| 28 | `Image Alt Text` | image row | Alt text for the image in this row. Blank in sample rows; populate with `"{Title} - {Colour}"` where useful | *(empty)* |
| 29 | `Option1 Value` | variant | Colour value (sample shows source colour name, e.g. `IT'S BLACK` / `SMOKE GREY` / `RANGER GREEN` / `DARK EARTH`) | `IT'S BLACK` |
| 30 | `Option2 Value` | variant | Size value (`MEDIUM`, `LARGE`, `XLARGE` …) | `MEDIUM` |
| 31 | `Option3 Value` | variant | blank unless option 3 in use | *(empty)* |
| 32 | `Variant SKU` | variant | Source SKU verbatim (spaces kept): `F1 VTX9111 IBK MEDIUM` = `F1 {style} {colourcode} {size}` | `F1 VTX9111 IBK MEDIUM` |
| 33 | `Variant Grams` | variant | Integer grams | `1000` |
| 34 | `Variant Barcode` | variant | UPC/EAN/GTIN. Oakley SI: in product URL. Woo: JSON-LD `gtin` on PDP if present, else blank | `190449699597` |
| 35 | `Variant Inventory Tracker` | variant | **Duplicate header** — same value as col 11 (`shopify`). Matrixify tolerates dup; fill identically | `shopify` |
| 36 | `Variant Price` | variant | **Blank** — client sets retail price | *(empty)* |
| 37 | `Variant Requires Shipping` | variant | `TRUE` | `TRUE` |
| 38 | `Variant Taxable` | variant | `TRUE` | `TRUE` |
| 39 | `Image Src` | image row | Absolute image URL. Shopify fetches on import. First row = main image | `https://cdn.shopify.com/…/VTX9111_10inMDSock_IBK_3qtr_…jpg` |
| 40 | `Image Position` | image row | 1-based integer, unique per product | `1` |
| 41 | `Variant Image` | variant | URL of the image to pin to this specific variant (usually the colour's hero shot) | `https://cdn.shopify.com/…/VTX9111_10inMDSock_IBK_3qtr_…jpg` |

## Single-variant products

Rows 96 / 109 in the sample (mesh pouches): no options.
- `Option1 Name` = *(empty)*, `Option1 Value` = `Default Title`
- `Variant SKU` = source SKU (`F1 VTX5195 AGY`)
- Still one product row + extra image rows.

## Images

- Sample uses `cdn.shopify.com` URLs because those products were already
  uploaded once. For a fresh import we pass **source CDN URLs** (Woo:
  `wp-content/uploads/…`; Oakley SI: `/medias/…`). Shopify ingests them.
- Dedupe identical URLs. Assign `Image Position` sequentially.
- `Variant Image` should point at the colour's main shot so the storefront
  swaps the hero image when a shopper picks a colour.

## De-dupe / grouping rules

- Woo "variable product" = one Shopify product; its `variations` = variant rows.
- Oakley SI lists many **colourways as separate product pages**. Decision needed
  with client: keep as separate products (matches source) **or** group by model
  into one product with a `Colour` option. Default = **mirror the source**
  (separate products) unless told otherwise — grouping adds ~6–10 hrs on Oakley.

## Per-source field origins

### WooCommerce (Princeton Tec, Crispi)

| Sheet column | Source |
|--------------|--------|
| Title | `products[].name` (brand-prefixed) |
| Body (HTML) | `products[].description` → `clean_description()` |
| Option1/2 Value | parent `attributes[].terms` (slug→name) joined to `variations` by id; fallback = variation label string; fallback = synth grid |
| Variant SKU | `type=variation` object `.sku` (partial — API under-reports) |
| Variant Grams | variation `.weight` (kg) × 1000 |
| Variant Barcode | JSON-LD `gtin*` on the product page (often absent) |
| Image Src / Variant Image | `products[].images[].src`, variation `.images[0].src` |

### Oakley SI (recon 2026-09-10 — see quote §3)

| Sheet column | Source (all visible logged-out) |
|--------------|--------------------------------|
| Title | PDP `<h1>` |
| Body (HTML) | overview + "Features & Technologies" + measurements blocks → cleaned |
| Vendor | `Oakley SI` |
| Type / Product Category | PDP breadcrumb (`Eyewear > Sunglasses > On-Duty…`) |
| Option1 Value (Colour) | `window.__utagProducts[upc].FrameColor` / `productObj`; card colour for apparel |
| Option2 Value (Size) | size `<select>` (apparel/footwear/goggles); eyewear usually one-size |
| Variant SKU | `__utagProducts[upc].Sku` (e.g. `OO9102-B9`) or style code |
| Variant Barcode | UPC — `productObj.variants` keys / `?variant=<UPC>` links / `__utagProducts` key |
| Variant Grams | not on PDP → blank unless found |
| Variant Price | **blank** — `<format:price/>` placeholder logged-out |
| Image Src | gallery `/medias/…` or `assets.oakley.com/…` per colour |

## Open questions for client

1. Cleaned vs. raw description HTML?
2. Populate `Tags` / `Product Category` / `Type`, or leave blank as in sample?
3. Oakley SI: mirror source (colourway = product) or group by model?
4. Confirm prices are excluded.
