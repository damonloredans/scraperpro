"""Princeton Tec — princetontec.com — WooCommerce, public Store API.

Catalogue: ~50-70 variable products (headlamps, handhelds, helmet/marker lights,
accessories), 2-6 colour variations each. Store API is wide open; barcodes are
not exposed by Woo so we try JSON-LD gtin on each PDP.
"""
from __future__ import annotations

from ..woo import WooScraper


class PrincetonTecScraper(WooScraper):
    vendor = "Princeton Tec"
    base_url = "https://princetontec.com"
    colour_attr_names = {"color", "colour"}
    size_attr_names = {"size"}
    # LED Pattern etc. fall through to Option3.
    fetch_barcodes = True
    throttle = 0.6
