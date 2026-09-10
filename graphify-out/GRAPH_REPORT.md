# Graph Report - scraperpro  (2026-09-11)

## Corpus Check
- 23 files · ~65,879 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 233 nodes · 385 edges · 13 communities (9 shown, 4 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 43 edges (avg confidence: 0.87)
- Token cost: 95,000 input · 4,200 output

## Community Hubs (Navigation)
- WooCommerce Scraper & Variants
- Project Docs & Design Rationale
- Oakley Product Parsing
- Shared HTTP & Parsing Utilities
- Shopify CSV Output
- R2 Image Re-hosting
- Fetcher Backends & Akamai Bypass
- Oakley Crawl Orchestration & QA
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12

## God Nodes (most connected - your core abstractions)
1. `WooScraper` - 24 edges
2. `Internal working quote (rev 2)` - 15 edges
3. `OakleySIScraper` - 12 edges
4. `Product` - 11 edges
5. `R2` - 8 edges
6. `_product_type()` - 8 edges
7. `Oakley PDP parser` - 8 edges
8. `Variant` - 7 edges
9. `Progress` - 6 edges
10. `_utag_products()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `Oakley SI sunglasses category page fixture` --conceptually_related_to--> `Oakley /en-us/sitemap.xml product discovery`  [INFERRED]
  tests/fixtures/oakleysi_category_sunglasses.html → README.md
- `SI Light Patrol Boot PDP fixture (style 11190, Blackout)` --shares_data_with--> `Oakley PDP parser`  [INFERRED]
  tests/fixtures/oakleysi_pdp_boot_11190.html → README.md
- `Per-size EAN barcode present in data-variant, per-size SKU empty` --references--> `size-button PDP markup (softgoods size axis source)`  [INFERRED]
  tests/fixtures/oakleysi_pdp_boot_11190.html → README.md
- `utag_data.Products object (colour-level Sku 11190-02E, empty Price)` --conceptually_related_to--> `Risk 1 - Oakley price login-gated (ID.me)`  [INFERRED]
  tests/fixtures/oakleysi_pdp_boot_11190.html → docs/quote.md
- `Oakley PDP parser` --shares_data_with--> `Shopify Submission Format column map`  [INFERRED]
  README.md → docs/format-mapping.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Matrixify import-sheet generation** — docs_format_mapping_row_model, docs_format_mapping_column_map, docs_format_mapping_option_resolution [INFERRED 0.80]
- **No size-level SKU at source across Crispi and Oakley softgoods** — readme_per_variant_sku_gap, docs_quote_risk_9_per_variant_skus, docs_quote_for_howard_sku_question, tests_fixtures_oakleysi_pdp_boot_11190_size_button_element [INFERRED 0.85]
- **Oakley softgoods size-variant explosion from SSR size-button markup** — readme_size_button_markup, docs_quote_risk_5_size_variants, tests_fixtures_oakleysi_pdp_boot_11190_size_button_element, readme_pdp_parser [INFERRED 0.85]
- **Oakley Shopify Type resolved from taxonomy code, not promo breadcrumb** — readme_product_type_function, readme_product_category_code, readme_promo_breadcrumb_unreliability, tests_fixtures_oakleysi_pdp_boot_11190_promo_breadcrumb_path [INFERRED 0.85]

## Communities (13 total, 4 thin omitted)

### Community 0 - "WooCommerce Scraper & Variants"
Cohesion: 0.08
Nodes (40): Fixed price AUD $2,000 + ~$75 infrastructure, Reseller authorisation / indemnity confirmation, Client-facing quote for Howard, Oakley image hosting options A/B/C, SKU column fill question (a/b/c), docs/format-mapping.md column-by-column spec, Howard (Broad Arrow Tactical), Internal working quote (rev 2) (+32 more)

### Community 1 - "Project Docs & Design Rationale"
Cohesion: 0.10
Nodes (16): Variant, CrispiScraper, Crispi — crispiaustralia.com.au — WooCommerce, public Store API. Catalogue:…, EU 42" / "42.0" -> "42" so Size option values are consistent., PrincetonTecScraper, Princeton Tec — princetontec.com — WooCommerce, public Store API. Catalogue:…, _dedupe_variants(), WooCommerce Store API scraper base. Both Princeton Tec and Crispi AU expose the… (+8 more)

### Community 2 - "Oakley Product Parsing"
Cohesion: 0.11
Nodes (29): BeautifulSoup, scraperpro — brand catalogue scrapers that emit a Shopify (Matrixify) import…, _brace_match(), _clean_soup(), _colour_labels(), _description(), _first_image_for(), _images() (+21 more)

### Community 3 - "Shared HTTP & Parsing Utilities"
Cohesion: 0.09
Nodes (20): clean_description(), get_html(), get_json(), grams(), gtin_from_jsonld(), HandlePool, jsonld_blocks(), make_session() (+12 more)

### Community 4 - "Shopify CSV Output"
Cohesion: 0.14
Nodes (13): RuntimeError, BlockedError, CurlCffiFetcher, _dotenv_get(), FixtureFetcher, make_fetcher(), Fetchers — pluggable HTTP backends (same `.get(url, expect=None) -> str`).…, SCRAPERAPI_KEY -> UnblockerFetcher; else CurlCffiFetcher (which auto-uses… (+5 more)

### Community 5 - "R2 Image Re-hosting"
Cohesion: 0.13
Nodes (20): clean_description() HTML cleaning, Shopify Submission Format column map, Option1/2 value resolution, Matrixify multi-row product model, QA across 1,541 products (biggest single item), clean_description() page-builder stripping, Colour swatch title attribute as colour name, Oakley PDP parser (+12 more)

### Community 6 - "Fetcher Backends & Akamai Bypass"
Cohesion: 0.18
Nodes (11): scraperpro CLI. python run.py princetontec # full run ->…, _dedupe(), Product, The exact Shopify submission sheet layout from…, Structural issues Shopify's importer rejects silently., Expand to Matrixify rows: product+variant+image on row 1, then one row per…, Write products to a Shopify submission CSV. Returns the row count., write_csv() (+3 more)

### Community 7 - "Oakley Crawl Orchestration & QA"
Cohesion: 0.18
Nodes (10): load_env(), png_to_jpeg(), R2, Cloudflare R2 upload (S3-compatible) for re-hosting Oakley images. Config comes…, Upload bytes as image/jpeg at `key`; return the public URL., Delete every object under `prefix` (teardown after the client's import)., Flatten transparency onto white, downscale, encode JPEG., main() (+2 more)

### Community 8 - "Community 8"
Cohesion: 0.19
Nodes (9): Product, OakleySIScraper, Download every product image to <out_dir>/<handle>/NN.png, in parallel. Oakley…, All product URLs in ONE request. `since` = ISO date; only URLs with a newer…, test_pdp_parses_to_product(), load(), main(), QA a delivered import sheet before it goes to the client. python… (+1 more)

## Ambiguous Edges - Review These
- `Risk 1 - Oakley price login-gated (ID.me)` → `Reseller authorisation / indemnity confirmation`  [AMBIGUOUS]
  docs/quote-for-howard.md · relation: conceptually_related_to

## Knowledge Gaps
- **14 isolated node(s):** `beautifulsoup4 dependency`, `boto3 dependency`, `curl_cffi dependency`, `Pillow dependency`, `clean_description() HTML cleaning` (+9 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 73 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Risk 1 - Oakley price login-gated (ID.me)` and `Reseller authorisation / indemnity confirmation`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `WooScraper` connect `Project Docs & Design Rationale` to `Fetcher Backends & Akamai Bypass`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Why does `OakleySIScraper` connect `Community 8` to `Project Docs & Design Rationale`, `Oakley Product Parsing`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `WooScraper` (e.g. with `Product` and `Variant`) actually correct?**
  _`WooScraper` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `Product` (e.g. with `_rows()` and `write_csv()`) actually correct?**
  _`Product` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `BeautifulSoup` (e.g. with `clean_description()` and `jsonld_blocks()`) actually correct?**
  _`BeautifulSoup` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `beautifulsoup4 dependency`, `boto3 dependency`, `curl_cffi dependency` to the rest of the system?**
  _14 weakly-connected nodes found - possible documentation gaps or missing edges._