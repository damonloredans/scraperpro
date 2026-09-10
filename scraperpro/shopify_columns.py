"""The exact Shopify submission sheet layout from vertx_product_submission_sample.csv.

It is a Matrixify-style sheet, not a native Shopify CSV. We reproduce the header
verbatim, including the one blank column (index 12) and the duplicated
"Variant Inventory Tracker" (indexes 10 and 34).

See docs/format-mapping.md for the column-by-column rationale.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field

# Header row, verbatim from the sample. "" is the real unnamed column.
HEADER: list[str] = [
    "Handle",
    "Title",
    "Body (HTML)",
    "Vendor",
    "Tags",
    "SEO Title",
    "SEO Description",
    "Published",
    "Variant Inventory Qty",
    "Variant Inventory Policy",
    "Variant Inventory Tracker",
    "Variant Fulfillment Service",
    "",                                # unnamed blank column (kept for parity)
    "Gift Card",
    "Status",
    "Variant Weight Unit",
    "Included / Australia",
    "Included / International",
    "Product Category",
    "Type",
    "Option1 Name",
    "Option1 Linked To",
    "Option2 Name",
    "Option2 Linked To",
    "Option3 Name",
    "Option3 Linked To",
    "Variant Compare At Price",
    "Image Alt Text",
    "Option1 Value",
    "Option2 Value",
    "Option3 Value",
    "Variant SKU",
    "Variant Grams",
    "Variant Barcode",
    "Variant Inventory Tracker",       # duplicate header, same value as index 10
    "Variant Price",
    "Variant Requires Shipping",
    "Variant Taxable",
    "Image Src",
    "Image Position",
    "Variant Image",
]

# Fixed values that never change in the sample.
DEFAULTS = {
    "Published": "TRUE",
    "Variant Inventory Qty": "0",
    "Variant Inventory Policy": "deny",
    "Variant Inventory Tracker": "shopify",
    "Variant Fulfillment Service": "manual",
    "Gift Card": "FALSE",
    "Status": "draft",
    "Variant Weight Unit": "g",
    "Included / Australia": "TRUE",
    "Included / International": "TRUE",
    "Variant Requires Shipping": "TRUE",
    "Variant Taxable": "TRUE",
}


@dataclass
class Variant:
    option1: str = ""          # colour (or "Default Title")
    option2: str = ""          # size
    option3: str = ""
    sku: str = ""
    grams: int = 0
    barcode: str = ""
    price: str = ""            # left blank by default — client sets pricing
    compare_at: str = ""
    image: str = ""            # URL pinned to this variant


@dataclass
class Product:
    handle: str
    title: str
    body_html: str = ""
    vendor: str = ""
    tags: str = ""
    seo_title: str = ""
    seo_description: str = ""
    product_category: str = ""
    product_type: str = ""
    option1_name: str = ""     # "Colour" / ""
    option2_name: str = ""     # "Size " / ""
    option3_name: str = ""
    variants: list[Variant] = field(default_factory=list)
    images: list[str] = field(default_factory=list)   # ordered, deduped, main first

    def rows(self) -> list[dict]:
        """Expand to Matrixify rows: product+variant+image on row 1, then one row
        per extra variant, then image-only rows for gallery overflow."""
        out: list[dict] = []
        images = _dedupe(self.images)

        for i, v in enumerate(self.variants):
            row = {k: "" for k in HEADER}
            # variant-level (every variant row)
            row.update({
                "Handle": self.handle,
                "Variant Inventory Policy": DEFAULTS["Variant Inventory Policy"],
                "Variant Inventory Tracker": DEFAULTS["Variant Inventory Tracker"],
                "Variant Fulfillment Service": DEFAULTS["Variant Fulfillment Service"],
                "Option1 Value": v.option1,
                "Option2 Value": v.option2,
                "Option3 Value": v.option3,
                "Variant SKU": v.sku,
                "Variant Grams": str(v.grams) if v.grams else "",
                "Variant Barcode": v.barcode,
                "Variant Price": v.price,
                "Variant Compare At Price": v.compare_at,
                "Variant Requires Shipping": DEFAULTS["Variant Requires Shipping"],
                "Variant Taxable": DEFAULTS["Variant Taxable"],
                "Variant Image": v.image,
            })
            if i == 0:
                # product-level (row 1 only)
                row.update({
                    "Title": self.title,
                    "Body (HTML)": self.body_html,
                    "Vendor": self.vendor,
                    "Tags": self.tags,
                    "SEO Title": self.seo_title or f"{self.title} {self.vendor}".strip(),
                    "SEO Description": self.seo_description,
                    "Published": DEFAULTS["Published"],
                    "Variant Inventory Qty": DEFAULTS["Variant Inventory Qty"],
                    "Gift Card": DEFAULTS["Gift Card"],
                    "Status": DEFAULTS["Status"],
                    "Variant Weight Unit": DEFAULTS["Variant Weight Unit"],
                    "Included / Australia": DEFAULTS["Included / Australia"],
                    "Included / International": DEFAULTS["Included / International"],
                    "Product Category": self.product_category,
                    "Type": self.product_type,
                    "Option1 Name": self.option1_name,
                    "Option2 Name": self.option2_name,
                    "Option3 Name": self.option3_name,
                })
                if images:
                    row["Image Src"] = images[0]
                    row["Image Position"] = "1"
            else:
                # attach the (i+1)-th gallery image to this variant row if we have one
                if i < len(images):
                    row["Image Src"] = images[i]
                    row["Image Position"] = str(i + 1)
            out.append(row)

        # gallery overflow: images not yet placed get their own Handle-only rows
        placed = min(len(self.variants), len(images))
        for pos in range(placed, len(images)):
            row = {k: "" for k in HEADER}
            row["Handle"] = self.handle
            row["Image Src"] = images[pos]
            row["Image Position"] = str(pos + 1)
            out.append(row)

        return out


def _dedupe(seq: list[str]) -> list[str]:
    seen, out = set(), []
    for s in seq:
        s = (s or "").strip()
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def write_csv(path: str, products: list[Product]) -> int:
    """Write products to a Shopify submission CSV. Returns the row count."""
    n = 0
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=HEADER, extrasaction="ignore")
        w.writeheader()
        for p in products:
            for row in p.rows():
                w.writerow(row)
                n += 1
    return n
