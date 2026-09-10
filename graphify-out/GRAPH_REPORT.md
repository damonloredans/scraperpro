# Graph Report - scraperpro  (2026-09-10)

## Corpus Check
- 22 files · ~53,404 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 193 nodes · 334 edges · 8 communities
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 30 edges (avg confidence: 0.83)
- Token cost: 108,000 input · 3,500 output

## Community Hubs (Navigation)
- WooCommerce Scraper & Variants
- Project Docs & Design Rationale
- Oakley Product Parsing
- Shared HTTP & Parsing Utilities
- Shopify CSV Output
- R2 Image Re-hosting
- Fetcher Backends & Akamai Bypass
- Oakley Crawl Orchestration & QA

## God Nodes (most connected - your core abstractions)
1. `WooScraper` - 24 edges
2. `Product` - 16 edges
3. `OakleySIScraper` - 15 edges
4. `Variant` - 10 edges
5. `Shopify Submission Format column map` - 10 edges
6. `Oakley PDP parser` - 9 edges
7. `R2` - 8 edges
8. `BlockedError` - 7 edges
9. `make_fetcher()` - 7 edges
10. `FixtureFetcher` - 7 edges

## Surprising Connections (you probably didn't know these)
- `WooCommerce variation SKU gap` --semantically_similar_to--> `Oakley size-variant explosion`  [INFERRED] [semantically similar]
  README.md → docs/quote.md
- `beautifulsoup4 dependency` --conceptually_related_to--> `Oakley PDP parser`  [INFERRED]
  requirements.txt → README.md
- `Oakley image re-hosting pipeline (Option A)` --shares_data_with--> `boto3 dependency`  [INFERRED]
  README.md → requirements.txt
- `Oakley image re-hosting pipeline (Option A)` --references--> `Pillow dependency`  [INFERRED]
  README.md → requirements.txt
- `Crispi Option1-first packing fix (_resolve_options)` --rationale_for--> `Shopify Submission Format column map`  [INFERRED]
  README.md → docs/format-mapping.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Oakley SI scrape-to-sheet pipeline** — readme_sitemap_discovery, readme_curl_cffi_fetcher, readme_pdp_parser, readme_oakley_image_rehosting, readme_circuit_breaker [INFERRED 0.85]
- **Akamai bot-wall bypass strategy** — readme_akamai_wall, readme_curl_cffi_fetcher, docs_quote_scraperapi, readme_circuit_breaker, readme_fast_mode [INFERRED 0.80]
- **Matrixify import-sheet generation** — readme_matrixify_format, docs_format_mapping_row_model, docs_format_mapping_column_map, docs_format_mapping_option_resolution, readme_crispi_option_ordering_fix [INFERRED 0.80]

## Communities (8 total, 0 thin omitted)

### Community 0 - "WooCommerce Scraper & Variants"
Cohesion: 0.10
Nodes (16): Variant, CrispiScraper, Crispi — crispiaustralia.com.au — WooCommerce, public Store API. Catalogue:…, EU 42" / "42.0" -> "42" so Size option values are consistent., PrincetonTecScraper, Princeton Tec — princetontec.com — WooCommerce, public Store API. Catalogue:…, _dedupe_variants(), WooCommerce Store API scraper base. Both Princeton Tec and Crispi AU expose the… (+8 more)

### Community 1 - "Project Docs & Design Rationale"
Cohesion: 0.10
Nodes (32): clean_description() HTML cleaning, Shopify Submission Format column map, Option1/2 value resolution, Matrixify multi-row product model, Oakley colourway grouping decision, Crispi AU = 13 products scope, Client-facing quote (for Howard), Internal working quote (rev 2) (+24 more)

### Community 2 - "Oakley Product Parsing"
Cohesion: 0.10
Nodes (25): BlockedError, FixtureFetcher, Fetchers — pluggable HTTP backends (same `.get(url, expect=None) -> str`).…, Serves saved HTML by matching a substring of the URL to a fixture filename.…, Raised when the fetcher is persistently blocked — abort the whole run., scraperpro — brand catalogue scrapers that emit a Shopify (Matrixify) import…, _brace_match(), _clean_soup() (+17 more)

### Community 3 - "Shared HTTP & Parsing Utilities"
Cohesion: 0.09
Nodes (24): BeautifulSoup, clean_description(), get_html(), get_json(), grams(), gtin_from_jsonld(), HandlePool, html_unescape() (+16 more)

### Community 4 - "Shopify CSV Output"
Cohesion: 0.18
Nodes (11): scraperpro CLI. python run.py princetontec # full run ->…, _dedupe(), Product, The exact Shopify submission sheet layout from…, Structural issues Shopify's importer rejects silently., Expand to Matrixify rows: product+variant+image on row 1, then one row per…, Write products to a Shopify submission CSV. Returns the row count., write_csv() (+3 more)

### Community 5 - "R2 Image Re-hosting"
Cohesion: 0.18
Nodes (10): load_env(), png_to_jpeg(), R2, Cloudflare R2 upload (S3-compatible) for re-hosting Oakley images. Config comes…, Upload bytes as image/jpeg at `key`; return the public URL., Delete every object under `prefix` (teardown after the client's import)., Flatten transparency onto white, downscale, encode JPEG., main() (+2 more)

### Community 6 - "Fetcher Backends & Akamai Bypass"
Cohesion: 0.17
Nodes (8): RuntimeError, CurlCffiFetcher, _dotenv_get(), make_fetcher(), SCRAPERAPI_KEY -> UnblockerFetcher; else CurlCffiFetcher (which auto-uses…, Prime the session with Akamai cookies (_abck / bm_sv / ak_bmsc …) captured from…, Routes every request through ScraperAPI, which solves Akamai and returns the…, UnblockerFetcher

### Community 7 - "Oakley Crawl Orchestration & QA"
Cohesion: 0.24
Nodes (7): OakleySIScraper, Download every product image to <out_dir>/<handle>/NN.png, in parallel. Oakley…, All product URLs in ONE request. `since` = ISO date; only URLs with a newer…, load(), main(), QA a delivered import sheet before it goes to the client. python…, val()

## Knowledge Gaps
- **7 isolated node(s):** `Matrixify-style Shopify import sheet`, `Cloudflare R2 image bucket`, `Matrixify multi-row product model`, `curl_cffi dependency`, `Pillow dependency` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 61 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Product` connect `Shopify CSV Output` to `WooCommerce Scraper & Variants`, `Oakley Product Parsing`, `Oakley Crawl Orchestration & QA`?**
  _High betweenness centrality (0.134) - this node is a cross-community bridge._
- **Why does `WooScraper` connect `WooCommerce Scraper & Variants` to `Shopify CSV Output`?**
  _High betweenness centrality (0.125) - this node is a cross-community bridge._
- **Why does `OakleySIScraper` connect `Oakley Crawl Orchestration & QA` to `WooCommerce Scraper & Variants`, `Oakley Product Parsing`, `Shopify CSV Output`, `Fetcher Backends & Akamai Bypass`?**
  _High betweenness centrality (0.120) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `WooScraper` (e.g. with `Product` and `Variant`) actually correct?**
  _`WooScraper` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `Product` (e.g. with `_rows()` and `write_csv()`) actually correct?**
  _`Product` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `OakleySIScraper` (e.g. with `BlockedError` and `Product`) actually correct?**
  _`OakleySIScraper` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `Variant` (e.g. with `OakleySIScraper` and `_dedupe_variants()`) actually correct?**
  _`Variant` has 3 INFERRED edges - model-reasoned connections that need verification._