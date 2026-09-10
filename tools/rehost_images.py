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
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scraperpro.r2 import R2, png_to_jpeg


def rehost(csv_path: str, images_dir: str, prefix: str, workers: int = 12,
           clean: bool = False) -> str:
    r2 = R2()
    rows = list(csv.reader(open(csv_path, encoding="utf-8")))
    h = rows[0]
    i_handle, i_src, i_pos = h.index("Handle"), h.index("Image Src"), h.index("Image Position")
    i_var = h.index("Variant Image")

    jobs = []                                        # (handle, pos, local, key)
    for r in rows[1:]:
        if len(r) <= i_pos or not r[i_pos].strip().isdigit():
            continue
        handle, pos = r[i_handle], int(r[i_pos])
        local = os.path.join(images_dir, handle, f"{pos:02d}.png")
        if not os.path.exists(local):
            print(f"  ! missing {local}")
            continue
        jobs.append((handle, pos, local, f"{prefix}/{handle}/{pos:02d}.jpg"))

    print(f"  [r2] {len(jobs)} images, {workers} workers")
    url_map: dict[tuple[str, int], str] = {}
    uploaded = skipped = 0

    def push(job):
        handle, pos, local, key = job
        if r2.exists(key):
            return handle, pos, key, "skip"
        with open(local, "rb") as fh:
            r2.put_jpeg(key, png_to_jpeg(fh.read()))
        return handle, pos, key, "up"

    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for fut in as_completed(ex.submit(push, j) for j in jobs):
            handle, pos, key, what = fut.result()
            url_map[(handle, pos)] = f"{r2.public_base}/{key}"
            uploaded += what == "up"
            skipped += what == "skip"
            done += 1
            if done % 200 == 0 or done == len(jobs):
                print(f"  [r2] {done}/{len(jobs)}")

    for r in rows[1:]:
        if len(r) <= i_pos or not r[i_pos].strip().isdigit():
            continue
        u = url_map.get((r[i_handle], int(r[i_pos])))
        if u:
            r[i_src] = u
    for r in rows[1:]:                                # pin Variant Image to position 1
        if len(r) > i_var and r[i_var].strip():
            r[i_var] = url_map.get((r[i_handle], 1), r[i_var])

    out = csv_path.rsplit(".", 1)[0] + ".r2.csv"
    csv.writer(open(out, "w", newline="", encoding="utf-8")).writerows(rows)
    print(f"  uploaded {uploaded}, already-there {skipped}  ->  {out}")

    if clean and uploaded + skipped == len(jobs) and jobs:
        shutil.rmtree(images_dir, ignore_errors=True)
        print(f"  [clean] removed local {images_dir} ({len(jobs)} images now only on R2)")
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
