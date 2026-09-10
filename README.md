# scraperpro

Scrapes a brand's public catalogue and writes a **Shopify product import sheet**
in the Matrixify-style layout from `vertx_product_submission_sample.csv`
(one row per variant, product fields on the first row, gallery rows after).

Job: **Broad Arrow Tactical** (broadarrowtactical.com.au) — migrate Oakley SI,
Princeton Tec and Crispi catalogues into Shopify. See `docs/quote.md` for scope,
pricing and risks.

## Brands

| Brand | Site | Platform | Status |
|-------|------|----------|--------|
| Princeton Tec | princetontec.com | WooCommerce (public Store API) | ✅ working |
| Crispi (AU) | **crispiaustralia.com.au** | WooCommerce (public Store API) | ✅ working |
| Oakley SI | oakleysi.com/en-us | SAP Commerce Cloud + Akamai | 🚧 scaffold — see `scraperpro/sites/oakleysi.py` |

> The brief wrote "Cirspi / cirspiaustralia.com.au" — that domain does not
> resolve. The real site is **crispiaustralia.com.au** (brand *Crispi*).

## Setup

```bash
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

## Usage

```bash
python run.py princetontec                 # full catalogue -> output/princetontec_shopify.csv
python run.py crispi --limit 3             # first 3 products only (smoke test)
python run.py princetontec crispi          # both in one go
python run.py oakleysi                     # not implemented yet (exits 1)
```

Measured run times: **Princeton Tec 72 products ≈ 3 min**, **Crispi 13 products
≈ 40 s** (both network-bound, deliberately throttled). Oakley SI projected at
~10–15 s/product → ~20–35 hrs of machine crawl for the full ~1,400-product
catalogue, spread over several days in batches.

Output CSVs land in `output/` (git-ignored). Import with **Matrixify** (not the
native Shopify importer — the column layout is Matrixify's). Everything imports
as **draft** with a **blank price** — you set pricing in Shopify.

## How it works

```
run.py
 └─ scraperpro/sites/<brand>.py     thin per-brand config
     └─ scraperpro/woo.py           WooCommerce Store API crawler + transform
         ├─ scraperpro/common.py    http session, slugify, HTML cleaning, JSON-LD gtin
         └─ scraperpro/shopify_columns.py   the exact sheet layout + row expansion
```

### WooCommerce path (Princeton Tec, Crispi) — implemented

1. `GET /wp-json/wc/store/v1/products?per_page=100&page=N` — parent products.
2. `GET /wp-json/wc/store/v1/products?type=variation&parent=<id>` — variation
   objects (sku, price, weight, images). Their `attributes` array is empty, so
   option values are joined in from the parent's `attributes` (slug → display
   name) and `variations` (id → slugs); falls back to parsing the variation
   label string, then to synthesising the grid from parent attribute terms.
3. Barcodes aren't in the Store API — fetch each product page, read `gtin` from
   its JSON-LD (blank when absent).
4. `clean_description()` strips page-builder scaffolding (Magento PageBuilder,
   Avada/Fusion Builder), keeps headings/lists/paragraphs.

**Known gap:** both sites' Store API under-reports variations (Crispi returns
0–1 of ~12 sizes). Synthesised rows have the right options but **no SKU**. Fix =
parse each product page's variation form (`data-product_variations` /
`?wc-ajax=get_variation`). Costed in the "finish" hours in `docs/quote.md`.

### Oakley SI path — designed, not built

Recon (2026-09-10, see `docs/quote.md` §3) found:

- Product pages are **server-side rendered** — the HTML already holds name,
  description, features, measurements, breadcrumb, colours, style code, images.
- Each PDP embeds `window.productObj.variants` (keyed by UPC) and a rich
  `window.__utagProducts` object (Sku, FrameColor, LensColor, LensTechnology,
  Size, ModelCode, LensUPC, image, …) — **barcodes and attributes without login**.
- **Price** is an empty `<format:price/>` placeholder logged-out → login-only,
  treated as out of scope.
- **No** SAP OCC/REST API (`/occ/v2/…` 404s to search).
- **Akamai** blocks plain HTTP clients (403). Needs a browser-like fetcher.

Planned design — a pluggable **fetcher** behind the parser so it can swap without
touching parsing logic:

| Fetcher | Speed | Use when |
|---------|-------|----------|
| `curl_cffi` / `hrequests` (Chrome-TLS impersonation, plain GET) | ~1–2 s/page | **try first** — pages are SSR, no JS needed except `__utagProducts` |
| Playwright headless Chromium | ~3–6 s/page | curl_cffi gets challenged |
| Playwright/Selenium over CDP to a real Chrome (`--remote-debugging-port=9222`) | ~4–8 s/page | Akamai flags headless too — reuses your real profile/fingerprint |

`__utagProducts` needs the page's JS to have run, so if the light fetcher is used
we either (a) re-derive those fields from the SSR HTML + `productObj`, or (b) use
the browser fetcher for PDPs and the light one for listings.

### New / removed products mid-crawl

The crawl is a multi-day snapshot. The crawler is **idempotent** (keyed on style
code) and re-runnable. The final QA pass re-pulls every category listing, diffs
the style-code set against what was scraped, and re-scrapes any adds; removals
are dropped. Keeping the sheet current after handover = a scheduled weekly delta
run (separate quote).

## Field mapping

Full column-by-column spec: **`docs/format-mapping.md`**.
Scope / pricing / risks: **`docs/quote.md`**.

## Known limitations

- **Oakley SI not implemented** — scaffold + design only.
- WooCommerce variation SKUs incomplete (see gap note above).
- Gallery images attached to variant rows positionally; colour-accurate pinning
  uses `Variant Image`.
- `Tags`, `Product Category`, `Type`, `Variant Price`, `Compare At Price` left
  blank (as in the sample).
