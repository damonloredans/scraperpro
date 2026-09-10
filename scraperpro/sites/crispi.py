"""Crispi — crispiaustralia.com.au — WooCommerce, public Store API.

Catalogue: ~10-15 boot models, ~12 EU sizes each (37-48), some with a width
axis. Descriptions are heavy Avada / Fusion Builder markup — clean_description()
strips the scaffolding.
"""
from __future__ import annotations

import re

from ..woo import WooScraper


class CrispiScraper(WooScraper):
    vendor = "Crispi"
    base_url = "https://crispiaustralia.com.au"
    colour_attr_names = {"color", "colour"}
    size_attr_names = {"size", "eu size", "eu-size", "shoe size", "boot size"}
    fetch_barcodes = True
    throttle = 0.8

    def normalise_size(self, value: str) -> str:
        """"EU 42" / "42.0" -> "42" so Size option values are consistent."""
        m = re.search(r"\d+(?:\.\d+)?", value or "")
        if not m:
            return value
        num = m.group(0)
        return num.rstrip("0").rstrip(".") if "." in num else num
