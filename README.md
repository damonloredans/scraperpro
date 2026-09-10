# scraperpro

Scrapes a brand's public catalogue and writes a **Shopify product import sheet**
in the Matrixify-style layout from `vertx_product_submission_sample.csv`
(one row per variant, product fields on the first row, gallery rows after).

Job: **Broad Arrow Tactical** (broadarrowtactical.com.au) — scrape the Oakley SI,
Princeton Tec and Crispi catalogues into Shopify import sheets. **Scrape-only**:
we deliver the CSVs + re-hosted images; the client's team runs the import (no
access to their Shopify). See `docs/quote.md` for scope, pricing and risks.

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

**Interactive:** double-click **`run.bat`** — it prompts for site, format, a
product limit (blank = all), and for Oakley whether to download + re-host images.

**CLI:**

```bash
python run.py princetontec                 # full catalogue -> output/princetontec_shopify.csv
python run.py crispi --limit 3             # first 3 products only (smoke test)
python run.py princetontec crispi          # both in one go
python run.py crispi --format shopify      # native Shopify CSV instead of Matrixify
python run.py oakleysi --limit 10 --images # scrape + download images (Akamai caps ~40-50 requests/IP)
python run.py oakleysi --limit 50 --fast   # 1 request/product -> ~3x more products before the block
```

`--fast` skips the per-colour page fetches: every colour still gets its barcode
(it's on the main page) but colours 2+ have a generic label and no per-colour
SKU. Testing lever only — the deliverable run uses full mode + proxies.

Re-runs **overwrite** that brand's CSV; a run that scrapes 0 products (e.g. an
Akamai block) is **not** written, so the last good file survives. `--images`
skips files already downloaded.

Every run prints elapsed time + s/product as it goes, a per-brand total on
completion, and for Oakley an extrapolated `~N min for 1,400` so you can size the
full job.

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

**What works:**
- **Discovery via `/en-us/sitemap.xml`** — all **1,541 product URLs in one
  request**, with `<lastmod>` for incremental runs. Falls back to the category
  crawl if the sitemap is unavailable.
- **PDP parser** — title, breadcrumb -> Type, cleaned description + measurements,
  SEO description, image gallery, per-colour Sku/UPC. Ran end to end on real
  products.
- **Circuit breaker** — after 3 Akamai-blocked requests in a row it aborts in
  ~30 s and keeps what it scraped (was: 20+ min of exponential backoff).

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

Getting past it for a full run — set **one** of these in `.env` (the fetcher
picks it up automatically, no code change):

| `.env` line | What | Cost |
|-------------|------|------|
| `SCRAPERAPI_KEY=...` | Unblocker API — ScraperAPI solves Akamai and returns the HTML. `make_fetcher()` routes every request through it. | **free tier = 5,000 credits**, covers all 1,541 |
| `SCRAPER_PROXY=http://USER:PASS@gate.smartproxy.com:7000` | Rotating residential proxy — new exit IP per request; `curl_cffi` sends through it, throttle drops, block-abort threshold rises. | ~USD $5–15 bandwidth |
| *(neither)* | Bare `curl_cffi` — works for ~40 requests from a rested IP, then blocks. Fine for testing with `--limit`. | free |

Sign-ups: **scraperapi.com** (free tier, instant key) · **smartproxy.com** /
**iproyal.com** / **brightdata.com** (residential, pay-as-you-go).

A 4th option, no third party: open the site once in a real browser, copy the
Akamai cookies (`_abck`, `bm_sv`), and `CurlCffiFetcher.seed_cookies()` them —
good for ~30–60 min per capture.

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

## QA a delivered sheet

```bash
python tools/validate.py output/oakleysi_shopify.csv            # structural + smell checks
python tools/validate.py output/oakleysi_shopify.csv --images 40 # + HEAD-check 40 random image URLs
python tools/validate.py output/oakleysi_shopify.csv --sitemap   # + flag sitemap products not in the sheet
```

Reports **BLOCKERS** (things Shopify's importer silently rejects — no Title,
duplicate variant options, Option2-without-Option1) and **SMELLS** (no images,
bad prices, promo-collection Type values). Exits non-zero on any blocker.

## Field mapping

Full column-by-column spec: **`docs/format-mapping.md`**.
Scope / pricing / risks: **`docs/quote.md`**.

## Import gotchas (found in live Shopify testing, 2026-09-10)

- **Princeton Tec** — imports clean (Matrixify format), with USD prices.
- **Crispi imported "0 products added"** — cause: size-only products had
  `Option2 Name` set with `Option1 Name` empty, which Shopify silently rejects.
  **Fixed** — options now pack into Option1 first (`_resolve_options`), so a
  size-only boot is `Option1 Name = Size`. Also dropped the sample's stray
  trailing space in `"Size "`.
- **Oakley images: "Media processing failed"** — `assets*.oakley.com` does
  Accept-header negotiation and serves **AVIF**, which Shopify rejects. Any
  query param forces the origin PNG, but that doesn't survive Shopify's CSV
  importer (it drops the query, and/or Akamai blocks Shopify's fetcher IPs).
  Downloading Oakley images through a browser also gives AVIF-with-a-`.png`-name,
  which Shopify Files rejects too. **Oakley images must be re-hosted** — see the
  next section. Verified working: origin PNG -> flatten to white JPEG -> serve
  from our own bucket -> Shopify imports fine. Woo image URLs import as-is.
- **Oakley description had duplicate measurements** — the `.singleContent` block
  already contains the frame/lens measurements; **fixed** — we no longer append
  the separate `.sizeText` block when they're already present.

## Oakley image re-hosting (Option A — our bucket)

This is a **scrape-only** engagement: we deliver CSVs + images; the client's team
runs the Shopify import. So we can't put images in *their* Shopify Files. Instead
the `Image Src` URLs in the delivered CSV point at a bucket **we** host for the
import window, then tear down.

Pipeline (the ~6 hr Oakley "image rehosting" line in the quote):

1. `OakleySIScraper.download_images(products, out_dir)` — pulls every image as
   origin PNG (sends a plain `Accept` header so the CDN doesn't return AVIF).
2. Convert PNG -> JPEG, flatten transparency onto white, cap at ~1600 px,
   q≈85 (drops ~1 MB PNGs to ~80 KB).
3. Upload to **Cloudflare R2** (S3-compatible, `boto3`) with key
   `oakleysi/<handle>/<NN>.jpg`.
4. Rewrite the CSV `Image Src` / `Variant Image` to the public bucket URLs
   (`https://pub-<hash>.r2.dev/oakleysi/<handle>/<NN>.jpg`).

What we need to set this up (all self-serve, nothing from the client):

- A Cloudflare account, R2 enabled (free tier: 10 GB storage, 1 M writes/mo —
  the whole catalogue is ~1–2 GB / ~14 k files, so **$0**).
- An R2 API token (Object Read & Write) -> Account ID + Access Key + Secret.
- The bucket set to **public** (r2.dev public URL, or a custom domain).
- One date from the client: **when the import is done**, so we can delete the
  bucket. Assume the URLs must stay live ~2–4 weeks.

Equivalents if not Cloudflare: Backblaze B2 (10 GB free), AWS S3 (pennies),
DigitalOcean Spaces ($5/mo). Same `boto3` code.

## Other known limitations

- **Oakley SI** — Akamai blocks sustained crawling from one IP (see "The Akamai
  wall"). Needs cookie-seeding / proxies / an unblocker for the full ~1,400.
  Apparel/footwear size explosion is stubbed (eyewear is one-size).
- WooCommerce variation SKUs incomplete (Store API under-reports — see gap).
- Gallery images attached to variant rows positionally; colour-accurate pinning
  uses `Variant Image`.
- `Tags` / `Product Category` blank (as in the sample). `Variant Price` filled
  for Princeton Tec (USD); blank for Crispi + Oakley.
