#!/usr/bin/env python3
"""scraperpro CLI.

    python run.py princetontec                    # full run -> output/princetontec_shopify.csv
    python run.py crispi --limit 3                 # first 3 products only (smoke test)
    python run.py princetontec crispi              # multiple brands
    python run.py crispi --format shopify          # native Shopify CSV instead of the Matrixify layout
    python run.py oakleysi --limit 5               # Akamai blocks ~40-50 requests from one IP; small runs only
    python run.py oakleysi --limit 5 --images      # also download images -> output/oakleysi_images/<handle>/NN.png

--format matrixify (default) matches Howard's sample sheet and imports via the
Matrixify app. --format shopify emits Shopify's native import layout.

After --images, re-host to R2 and rewrite the CSV:
    python tools/rehost_images.py output/oakleysi_shopify.csv --images output/oakleysi_images --prefix oakley
"""
from __future__ import annotations

import argparse
import os
import sys
import time

try:  # readable brand names in the Windows console
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

from scraperpro.sites import REGISTRY
from scraperpro import shopify_columns, shopify_native

OUT_DIR = os.path.join(os.path.dirname(__file__), "output")
WRITERS = {"matrixify": shopify_columns.write_csv, "shopify": shopify_native.write_csv}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Scrape a brand catalogue to a Shopify import CSV.")
    ap.add_argument("brands", nargs="+", choices=sorted(REGISTRY), help="which brand(s) to scrape")
    ap.add_argument("--limit", type=int, default=None, help="cap products per brand (smoke test)")
    ap.add_argument("--format", choices=sorted(WRITERS), default="matrixify",
                    help="matrixify (default, matches the sample) or shopify (native importer)")
    ap.add_argument("--images", action="store_true",
                    help="also download each product's images to output/<brand>_images/<handle>/NN.png")
    ap.add_argument("--fast", action="store_true",
                    help="Oakley only: 1 request per product (skip per-colour pages). "
                         "~3x more products before Akamai blocks; other colours get barcode only, no SKU/name.")
    ap.add_argument("--only", choices=("eyewear", "softgoods"), default=None,
                    help="Oakley only: scrape just one category group (for phased delivery). "
                         "Default = whole catalogue via the sitemap.")
    ap.add_argument("--out-dir", default=OUT_DIR)
    args = ap.parse_args(argv)

    write_csv = WRITERS[args.format]
    suffix = "shopify" if args.format == "matrixify" else "shopify-native"
    os.makedirs(args.out_dir, exist_ok=True)
    rc = 0
    run_start = time.perf_counter()
    for brand in args.brands:
        print(f"\n=== {brand} ({args.format}) ===")
        t0 = time.perf_counter()
        kw = {}
        if brand == "oakleysi":
            if args.fast:
                kw["fast"] = True
            if args.only:
                kw["group"] = args.only
        scraper = REGISTRY[brand](**kw)
        try:
            products = scraper.run(limit=args.limit)
        except NotImplementedError as e:
            print(f"  SKIPPED — {e}")
            rc = 1
            continue
        if not products:
            print("  0 products — not writing (last good file kept)")
            rc = 1
            continue

        if brand == "oakleysi" and args.limit is None and not args.only and len(products) < 1400:
            print(f"  NOTE: partial run — {len(products)} of ~1,541 products "
                  "(Akamai block or interrupt). The CSV is still written; re-run later for the rest.")
            rc = 1
        flagged = [(p.handle, probs) for p in products if (probs := p.problems())]
        if flagged:
            print(f"  ! {len(flagged)} product(s) with import problems:")
            for handle, probs in flagged[:10]:
                print(f"      {handle}: {'; '.join(probs)}")

        tag = f"_{args.only}" if (brand == "oakleysi" and args.only) else ""
        path = os.path.join(args.out_dir, f"{brand}{tag}_{suffix}.csv")
        n = write_csv(path, products)
        print(f"  wrote {len(products)} products / {n} rows -> {path}")

        if args.images:
            if not hasattr(scraper, "download_images"):
                print(f"  --images not supported for {brand} (image URLs import directly)")
            else:
                img_dir = os.path.join(args.out_dir, f"{brand}_images")
                scraper.download_images(products, img_dir)

        el = time.perf_counter() - t0
        per = el / len(products) if products else 0
        m, s = divmod(int(el), 60)
        print(f"  --- {brand} complete in {m}m{s:02d}s  "
              f"({len(products)} products, {per:.1f}s/product"
              + (f"  ->  ~{per * 1400 / 60:.0f} min for 1,400" if brand == "oakleysi" else "")
              + ") ---")

    tm, ts = divmod(int(time.perf_counter() - run_start), 60)
    print(f"\n=== ALL DONE in {tm}m{ts:02d}s ===")
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
