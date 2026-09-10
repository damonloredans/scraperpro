# scraperpro

Scrapes a brand's public catalogue and writes a **Shopify product import sheet**
in the Matrixify-style layout from `vertx_product_submission_sample.csv`
(one row per variant, product fields on the first row, gallery rows after).

Job: **Broad Arrow Tactical** (broadarrowtactical.com.au) — migrate Oakley SI,
Princeton Tec and Crispi catalogues into Shopify. See `docs/quote.md` for scope,
pricing and risks.

## Brands

| Brand | Site | Platform | Products | Status |
|-------|------|----------|----------|--------|
| Princeton Tec | princetontec.com | WooCommerce (public Store API) | 72 | working — SKUs partial (see gap) |
| Crispi (AU) | **crispiaustralia.com.au** | WooCommerce (public Store API) | **13** | working — per-size SKUs missing (see gap) |
| Oakley SI | oakleysi.com/en-us | SAP Commerce Cloud + Akamai | ~1,400 | partial - discovery + PDP parser done; Akamai blocks volume |

> The brief wrote "Cirspi / cirspiaustralia.com.au" — that domain does not
> resolve. The real site is **crispiaustralia.com.au** (brand *Crispi*).
>
> **Crispi AU has only 13 products.** That is the complete `crispiaustralia.com.au`
> catalogue (verified via the store API + category counts). Crispi *globally*
> makes 40+ models — if Broad Arrow wants the full range, that's a different site
> (crispi.com / crispioutdoor.com), not the AU distributor. Confirm with Howard.

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
~10-15 s/product -> ~20-35 hrs of machine crawl for the full ~1,400-product
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
   option values are joined in from the parent's `attributes` (slug -> display
   name) and `variations` (id -> slugs); falls back to parsing the variation
   label string, then to synthesising the grid from parent attribute terms.
3. Barcodes aren't in the Store API — fetch each product page, read `gtin` from
   its JSON-LD (blank when absent).
4. `clean_description()` strips page-builder scaffolding (Magento PageBuilder,
   Avada/Fusion Builder), keeps headings/lists/paragraphs.

**Known gap:** both sites' Store API under-reports variations (Crispi returns
0–1 of ~12 sizes). Synthesised rows have the right options but **no SKU**. Fix =
parse each product page's variation form (`data-product_variations` /
`?wc-ajax=get_variation`). Costed in the "finish" hours in `docs/quote.md`.

### Oakley SI path — partially built (`scraperpro/sites/oakleysi.py` + `scraperpro/fetch.py`)

Recon 2026-09-10 (see `docs/quote.md` §3):

- Product pages are **server-side rendered** — the HTML holds name, description,
  features, measurements, breadcrumb, colours, style code, images.
- Each PDP embeds `utag_data.Products = {<UPC>: {Sku, FrameColor, LensColor,
  LensTechnology, LensType, Category, ModelName, …}}` — **per-variant barcodes +
  attributes, no login**. Parsed with a brace-matcher (it's a JS object literal
  with unquoted numeric keys, not JSON).
- **Price** is an empty `<format:price/>` placeholder logged-out -> out of scope.
- **No** SAP OCC/REST API (`/occ/v2/...` -> search page).

**What works:** category discovery (48 links/page, paginates `?q=…&page=N`) and
the PDP parser. Pulled real products end to end — title, breadcrumb -> Type, cleaned
description + measurements, SEO description, image gallery, per-colour Sku/UPC.

**What's stubbed:** apparel/footwear/goggle *size* explosion (eyewear is
one-size); colourway grouping (currently one Shopify product per style code).

#### The Akamai wall

Oakley SI sits behind **Akamai Bot Manager**. Observed behaviour:

| Client | Result |
|--------|--------|
| `requests` / WebFetch | HTTP 403 immediately |
| `curl_cffi` (Chrome TLS/JA3 impersonation) | HTTP 200 for the first ~40–50 requests, then a 2.7 KB JS-challenge stub (still 200, no product data) |
| Real / headless browser | runs the JS sensor -> gets the `_abck` / `bm_sv` cookies -> sustained access, but ~3–8 s/page and needs stealth patches (plain Selenium/Playwright is fingerprinted too) |

`fetch.py`'s `CurlCffiFetcher` throttles (3 s + jitter), and `expect=` detects
the challenge stub (page missing `/en-us/product/` or `pdp-hero-name`) and backs
off exponentially. That's enough for small batches; **not** enough for 1,400
products from one IP in one sitting.

Production options (in order of cost):
1. **Cookie-seed**: open the site once in a real browser, copy the Akamai
   cookies into the `curl_cffi` session, refresh when they expire (~30–60 min).
   Fast bulk crawl (~1–2 s/page) between refreshes. Cheapest.
2. **Residential proxy rotation** — each IP gets ~50 requests before cooldown, so
   rotate. ~USD $5–15 for the whole catalogue in bandwidth.
3. **Unblocker API** (ScraperAPI / Zyte / BrightData Web Unlocker) — hands back
   solved HTML. ~USD $50–150 for the full catalogue, zero block-management.

#### Why not "just Selenium / BeautifulSoup"?

- **BeautifulSoup is already the parser here.** It has no network layer — it
  can't fetch anything, so it can't be blocked *or* get past a block. Something
  else (requests / curl_cffi / a browser) fetches the HTML and hands it to BS4.
- **Selenium (a real browser) does help** — it runs Akamai's JS sensor, so it
  gets the cookies a plain HTTP client can't. But it's 3–8 s/page vs ~1 s, it's
  heavy for ~1,400 pages, and vanilla Selenium/Playwright is itself fingerprinted
  (`navigator.webdriver`, headless quirks, canvas) — you still need
  `undetected-chromedriver` / stealth / a real profile. So the strategy is: fast
  path (curl_cffi, or curl_cffi + browser-seeded cookies) for the bulk, browser
  only where it gets challenged. `fetch.py` is the swap point.

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

- **Oakley SI** — parser works, but Akamai blocks sustained crawling from one IP
  (see "The Akamai wall" above). Needs cookie-seeding / proxies / an unblocker
  for the full ~1,400 products. Size explosion for apparel/footwear is stubbed.
- WooCommerce variation SKUs incomplete (see gap note above).
- Gallery images attached to variant rows positionally; colour-accurate pinning
  uses `Variant Image`.
- `Tags`, `Product Category`, `Type`, `Variant Price`, `Compare At Price` left
  blank (as in the sample).
