#!/usr/bin/env python3
"""Re-host a scraped CSV's images to Cloudflare R2 and rewrite Image Src.

    # 1. scrape + download the images  (needs .env with R2_* set)
    python run.py oakleysi --images

    # 2. convert -> upload to R2 -> rewrite the CSV
    python tools/rehost_images.py output/oakleysi_shopify.csv --prefix oakley

Produces <csv>.r2.csv with Image Src / Variant Image pointing at
https://pub-<hash>.r2.dev/<prefix>/<handle>/NN.jpg

Teardown after the client confirms their import:
    python tools/rehost_images.py --delete-prefix oakley
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scraperpro.r2 import R2, png_to_jpeg


def rehost(csv_path: str, images_dir: str, prefix: str) -> str:
    r2 = R2()
    rows = list(csv.reader(open(csv_path, encoding="utf-8")))
    h = rows[0]
    i_handle, i_src, i_pos = h.index("Handle"), h.index("Image Src"), h.index("Image Position")
    i_var = h.index("Variant Image")

    url_map: dict[tuple[str, int], str] = {}          # (handle, position) -> r2 url
    uploaded = skipped = 0

    for r in rows[1:]:
        if len(r) <= i_pos or not r[i_pos].strip().isdigit():
            continue
        handle, pos = r[i_handle], int(r[i_pos])
        local = os.path.join(images_dir, handle, f"{pos:02d}.png")
        if not os.path.exists(local):
            print(f"  ! missing {local}")
            continue
        key = f"{prefix}/{handle}/{pos:02d}.jpg"
        if r2.exists(key):
            skipped += 1
        else:
            with open(local, "rb") as fh:
                r2.put_jpeg(key, png_to_jpeg(fh.read()))
            uploaded += 1
        url_map[(handle, pos)] = f"{r2.public_base}/{key}"
        r[i_src] = url_map[(handle, pos)]

    # pin each product's Variant Image to its position-1 image
    for r in rows[1:]:
        if len(r) > i_var and r[i_var].strip():
            r[i_var] = url_map.get((r[i_handle], 1), r[i_var])

    out = csv_path.rsplit(".", 1)[0] + ".r2.csv"
    csv.writer(open(out, "w", newline="", encoding="utf-8")).writerows(rows)
    print(f"  uploaded {uploaded}, already-there {skipped}  ->  {out}")
    return out


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="?", help="scraped CSV to rewrite")
    ap.add_argument("--images", default="output/oakleysi_images")
    ap.add_argument("--prefix", default="oakley", help="R2 key prefix (folder)")
    ap.add_argument("--delete-prefix", metavar="PREFIX", help="teardown: delete all objects under PREFIX")
    a = ap.parse_args(argv)

    if a.delete_prefix:
        n = R2().delete_prefix(a.delete_prefix.rstrip("/") + "/")
        print(f"deleted {n} objects under {a.delete_prefix}/")
        return 0
    if not a.csv:
        ap.error("csv is required unless --delete-prefix")
    rehost(a.csv, a.images, a.prefix)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
