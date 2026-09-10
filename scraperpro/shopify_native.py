"""Native Shopify product CSV writer (the layout Shopify's built-in
"Import products by CSV" expects).

The default output (`shopify_columns.py`) matches Howard's sample sheet, which is
a **Matrixify** file and only imports through the Matrixify app. If you want to
import with Shopify's own importer instead, use this: `run.py --format shopify`.

Shopify's importer is tolerant of missing optional columns; these are the ones it
recognises. One row per variant; product-level fields on the first row; extra
image rows carry Handle + Image Src + Image Position.
"""
from __future__ import annotations

import csv

from .shopify_columns import Product, _dedupe

HEADER = [
    "Handle", "Title", "Body (HTML)", "Vendor", "Type", "Tags", "Published",
    "Option1 Name", "Option1 Value", "Option2 Name", "Option2 Value",
    "Option3 Name", "Option3 Value",
    "Variant SKU", "Variant Grams", "Variant Inventory Tracker",
    "Variant Inventory Qty", "Variant Inventory Policy",
    "Variant Fulfillment Service", "Variant Price", "Variant Compare At Price",
    "Variant Requires Shipping", "Variant Taxable", "Variant Barcode",
    "Image Src", "Image Position", "Image Alt Text", "Variant Image",
    "Variant Weight Unit", "SEO Title", "SEO Description", "Status",
]


def _rows(p: Product) -> list[dict]:
    out: list[dict] = []
    images = _dedupe(p.images)
    for i, v in enumerate(p.variants):
        row = {k: "" for k in HEADER}
        row.update({
            "Handle": p.handle,
            "Option1 Value": v.option1,
            "Option2 Value": v.option2,
            "Option3 Value": v.option3,
            "Variant SKU": v.sku,
            "Variant Grams": str(v.grams) if v.grams else "",
            "Variant Inventory Tracker": "shopify",
            "Variant Inventory Qty": "0",
            "Variant Inventory Policy": "deny",
            "Variant Fulfillment Service": "manual",
            "Variant Price": v.price,
            "Variant Compare At Price": v.compare_at,
            "Variant Requires Shipping": "TRUE",
            "Variant Taxable": "TRUE",
            "Variant Barcode": v.barcode,
            "Variant Image": v.image,
            "Variant Weight Unit": "g",
        })
        if i == 0:
            row.update({
                "Title": p.title,
                "Body (HTML)": p.body_html,
                "Vendor": p.vendor,
                "Type": p.product_type,
                "Tags": p.tags,
                "Published": "FALSE",                 # Status=draft -> keep unpublished
                "Option1 Name": p.option1_name or ("Title" if not p.option2_name else ""),
                "Option2 Name": p.option2_name,
                "Option3 Name": p.option3_name,
                "SEO Title": p.seo_title or f"{p.title} {p.vendor}".strip(),
                "SEO Description": p.seo_description,
                "Status": "draft",
            })
            if not row["Option1 Name"]:
                row["Option1 Name"] = "Title"
                row["Option1 Value"] = row["Option1 Value"] or "Default Title"
            if images:
                row["Image Src"] = images[0]
                row["Image Position"] = "1"
        elif i < len(images):
            row["Image Src"] = images[i]
            row["Image Position"] = str(i + 1)
        out.append(row)

    for pos in range(min(len(p.variants), len(images)), len(images)):
        row = {k: "" for k in HEADER}
        row["Handle"] = p.handle
        row["Image Src"] = images[pos]
        row["Image Position"] = str(pos + 1)
        out.append(row)
    return out


def write_csv(path: str, products: list[Product]) -> int:
    n = 0
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=HEADER, extrasaction="ignore")
        w.writeheader()
        for p in products:
            for row in _rows(p):
                w.writerow(row)
                n += 1
    return n
