#!/usr/bin/env python3
"""QA a delivered import sheet before it goes to the client.

    python tools/validate.py output/oakleysi_shopify.csv
    python tools/validate.py output/oakleysi_shopify.csv --images 40   # also HEAD-check 40 random image URLs
    python tools/validate.py output/oakleysi_shopify.csv --sitemap     # Oakley: check nothing from the sitemap is missing

Reports structural problems Shopify's importer rejects silently, plus data
smells. Exit code is non-zero if any BLOCKER is found.

Works on both the Matrixify layout and the native layout (auto-detects columns).
"""
from __future__ import annotations

import argparse
import csv
import random
import re
import sys
from collections import Counter, defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

BLOCKERS: list[str] = []   # things that make Shopify skip a product
SMELLS: list[str] = []     # things worth a human look

PROMO_TYPE_TERMS = ("gift", "holiday", "guide", "collection", "new arrival", "best seller",
                    "sale", "featured", "shop ")


def load(path: str):
    rows = list(csv.reader(open(path, encoding="utf-8")))
    header = rows[0]
    idx = {name: i for i, name in enumerate(header) if name}
    need = ["Handle", "Title", "Option1 Name", "Option1 Value", "Variant SKU",
            "Image Src", "Image Position"]
    missing = [c for c in need if c not in idx]
    if missing:
        sys.exit(f"CSV missing expected columns: {missing}")
    return header, rows[1:], idx


def val(row, idx, name):
    i = idx.get(name)
    return row[i].strip() if i is not None and i < len(row) else ""


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("--images", type=int, default=0, metavar="N", help="HEAD-check N random image URLs")
    ap.add_argument("--sitemap", action="store_true", help="Oakley: flag sitemap products not in the sheet")
    a = ap.parse_args(argv)

    header, rows, idx = load(a.csv)

    # group rows by product (Handle), first row of each = the product row
    products: dict[str, list] = defaultdict(list)
    order: list[str] = []
    for r in rows:
        h = val(r, idx, "Handle")
        if not h:
            SMELLS.append(f"row with no Handle: {r[:3]}")
            continue
        if h not in products:
            order.append(h)
        products[h].append(r)

    n_prod = len(order)
    print(f"\n{a.csv}")
    print(f"  {len(rows)} rows, {n_prod} products\n")

    # --- per-product structural checks -------------------------------------
    handle_titles = Counter()
    variant_rows_total = 0
    no_image = no_title = no_variant = 0
    dupe_opts = opt2_no_opt1 = blank_opt1 = 0
    price_bad = 0
    barcode_missing = 0
    promo_type = 0

    for h in order:
        prs = products[h]
        p0 = prs[0]
        title = val(p0, idx, "Title")
        handle_titles[h] += 1
        if not title:
            no_title += 1
            BLOCKERS.append(f"{h}: first row has no Title (Shopify won't create it)")

        variants = [r for r in prs if val(r, idx, "Variant SKU") or val(r, idx, "Option1 Value")]
        variant_rows_total += len(variants)
        if not variants:
            no_variant += 1
            BLOCKERS.append(f"{h}: no variant rows")

        if not any(val(r, idx, "Image Src") for r in prs):
            no_image += 1
            SMELLS.append(f"{h}: no images")

        o1name = val(p0, idx, "Option1 Name")
        o2name = val(p0, idx, "Option2 Name")
        if o2name and not o1name:
            opt2_no_opt1 += 1
            BLOCKERS.append(f"{h}: Option2 Name set, Option1 Name empty")
        if o1name and any(not val(v, idx, "Option1 Value") for v in variants):
            blank_opt1 += 1
            BLOCKERS.append(f"{h}: Option1 Name set but a variant has blank Option1 Value")

        keys = [(val(v, idx, "Option1 Value"), val(v, idx, "Option2 Value"),
                 val(v, idx, "Option3 Value")) for v in variants]
        if len(keys) > 1 and len(set(keys)) != len(keys):
            dupe_opts += 1
            BLOCKERS.append(f"{h}: {len(keys) - len(set(keys))} duplicate variant option value(s)")

        for v in variants:
            pr = val(v, idx, "Variant Price")
            if pr and (not re.fullmatch(r"\d+(\.\d{1,2})?", pr) or float(pr) == 0):
                price_bad += 1
                SMELLS.append(f"{h}: bad price {pr!r}")
                break
            if not val(v, idx, "Variant Barcode"):
                barcode_missing += 1

        t = val(p0, idx, "Type").lower()
        if t and any(term in t for term in PROMO_TYPE_TERMS):
            promo_type += 1
            SMELLS.append(f"{h}: Type looks like a promo collection: {val(p0, idx, 'Type')!r}")

    dupe_handles = [h for h, c in handle_titles.items() if c > 1]

    # --- image URL sample check ------------------------------------------------
    img_fail = 0
    if a.images:
        import requests
        urls = list({val(r, idx, "Image Src") for r in rows if val(r, idx, "Image Src")})
        sample = random.sample(urls, min(a.images, len(urls)))
        print(f"  checking {len(sample)} random image URLs...")
        for u in sample:
            try:
                rr = requests.head(u, timeout=20, allow_redirects=True)
                ct = rr.headers.get("content-type", "")
                if rr.status_code != 200 or not ct.startswith("image/"):
                    img_fail += 1
                    SMELLS.append(f"image {rr.status_code} {ct}: {u}")
            except requests.RequestException as e:
                img_fail += 1
                SMELLS.append(f"image ERR {e}: {u}")

    # --- sitemap coverage (Oakley) -------------------------------------------
    if a.sitemap:
        from scraperpro.sites.oakleysi import OakleySIScraper
        sm = OakleySIScraper().discover_from_sitemap()
        sm_codes = {u.rstrip("/").split("/")[-1] for u in sm}
        got = {h.split("-", 1)[0] for h in order}
        missing = sm_codes - got
        if missing:
            SMELLS.append(f"{len(missing)} sitemap products not in the sheet "
                          f"(e.g. {sorted(missing)[:8]})")

    # --- report -------------------------------------------------------------
    print("  structural:")
    print(f"    products with no Title on row 1 : {no_title}")
    print(f"    products with no variant rows   : {no_variant}")
    print(f"    duplicate variant option values : {dupe_opts}")
    print(f"    Option2 without Option1          : {opt2_no_opt1}")
    print(f"    blank Option1 Value              : {blank_opt1}")
    print(f"    duplicate handles               : {len(dupe_handles)}")
    print("  data smells:")
    print(f"    products with no images          : {no_image}")
    print(f"    bad / zero prices                : {price_bad}")
    print(f"    variant rows missing a barcode   : {barcode_missing}")
    print(f"    Type = promo-collection name     : {promo_type}")
    if a.images:
        print(f"    image URLs that failed the check : {img_fail} / {len(sample)}")

    def dump(label, items, n=25):
        if items:
            print(f"\n  {label} ({len(items)}):")
            for s in items[:n]:
                print(f"    - {s}")
            if len(items) > n:
                print(f"    ... and {len(items) - n} more")

    dump("BLOCKERS — Shopify will skip these", BLOCKERS)
    dump("SMELLS — worth a look", SMELLS)

    print()
    if BLOCKERS:
        print(f"  FAIL: {len(BLOCKERS)} blocker(s). Fix before delivery.")
        return 1
    print("  OK: no blockers. Sample the smells above by hand.")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, __file__.rsplit("tools", 1)[0])
    raise SystemExit(main(sys.argv[1:]))
