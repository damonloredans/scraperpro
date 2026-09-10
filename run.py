#!/usr/bin/env python3
"""scraperpro CLI.

    python run.py princetontec                    # full run -> output/princetontec_shopify.csv
    python run.py crispi --limit 3                 # first 3 products only (smoke test)
    python run.py princetontec crispi              # multiple brands
    python run.py crispi --format shopify          # native Shopify CSV instead of the Matrixify layout
    python run.py oakleysi                         # partial (Akamai-limited) — see docs

--format matrixify (default) matches Howard's sample sheet and imports via the
Matrixify app. --format shopify emits Shopify's native import layout.
"""
from __future__ import annotations

import argparse
import os
import sys

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
    ap.add_argument("--out-dir", default=OUT_DIR)
    args = ap.parse_args(argv)

    write_csv = WRITERS[args.format]
    suffix = "shopify" if args.format == "matrixify" else "shopify-native"
    os.makedirs(args.out_dir, exist_ok=True)
    rc = 0
    for brand in args.brands:
        print(f"\n=== {brand} ({args.format}) ===")
        scraper = REGISTRY[brand]()
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
        path = os.path.join(args.out_dir, f"{brand}_{suffix}.csv")
        n = write_csv(path, products)
        print(f"  wrote {len(products)} products / {n} rows -> {path}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
