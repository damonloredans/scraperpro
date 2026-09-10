"""Offline check of the Oakley SI parser against saved real HTML.

Proves the PDP -> Shopify-row transform without hitting the (Akamai-protected)
live site. Fixtures in tests/fixtures/ were captured 2026-09-10.

    python -m pytest tests/test_oakley_parser.py      # or just run this file
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scraperpro.fetch import FixtureFetcher
from scraperpro.sites.oakleysi import (
    OakleySIScraper, _style_codes, _utag_products, _product_type, _type_from_code,
)
from scraperpro.shopify_columns import HEADER

FIX = os.path.join(os.path.dirname(__file__), "fixtures")
PDP = os.path.join(FIX, "oakleysi_pdp_holbrook.html")
CAT = os.path.join(FIX, "oakleysi_category_sunglasses.html")
BOOT = os.path.join(FIX, "oakleysi_pdp_boot_11190.html")


def _html(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def test_category_discovery_finds_products():
    codes = _style_codes(_html(CAT))
    assert len(codes) >= 40
    assert "W0OO9102OSI" in codes or any(c.startswith("W0OO") for c in codes)


def test_utag_products_parsed():
    recs = _utag_products(_html(PDP))
    assert recs, "utag_data Products block not parsed"
    upc, rec = next(iter(recs.items()))
    assert upc.isdigit() and len(upc) >= 12          # UPC/EAN
    assert rec["Sku"] == "OO9102-B9"
    assert rec["FrameColor"] == "Matte Tortoise"


def test_type_from_taxonomy_code():
    # most specific known segment wins; unknown segments (lens tech, marketing) skipped
    assert _type_from_code("osi_ew_sun_ond_bs") == "Sunglasses"
    assert _type_from_code("oo_afa_foot_boot") == "Boots"
    assert _type_from_code("oo_afa_app_topw_tshirt_lifestyle") == "T-Shirts"
    assert _type_from_code("osi_afa_app_topw_hod-swea") == "Hoodies & Sweatshirts"
    assert _type_from_code("") == ""


def test_promo_breadcrumb_still_gets_a_real_type():
    # this boot's breadcrumb is "Home / Landing / Holiday Gifts for Tactical
    # Missions / Top Performing Gear" — the old breadcrumb[1] logic returned junk
    html = _html(BOOT)
    from bs4 import BeautifulSoup
    assert _product_type(BeautifulSoup(html, "lxml"), html) == "Boots"


def test_pdp_parses_to_product():
    s = OakleySIScraper(fetcher=FixtureFetcher({"W0OO9102OSI": PDP}))
    p = s.parse_product("https://www.oakleysi.com/en-us/product/W0OO9102OSI")

    assert "Holbrook" in p.title
    assert p.product_type == "Sunglasses"                 # from breadcrumb
    assert p.option1_name == "Colour"
    assert len(p.images) >= 5
    assert "Holbrook is a timeless" in p.body_html
    assert "Bridge Width 18 mm" in p.body_html            # measurements present
    assert p.body_html.count("Bridge Width 18 mm") == 1   # ...exactly once (no dup)

    v = p.variants[0]
    assert v.option1 == "Matte Tortoise"
    assert v.sku == "OO9102-B9"
    assert v.barcode == "888392235763"
    assert v.price == ""                                   # login-gated

    rows = p.rows()
    assert len(rows) == max(len(p.variants), len(p.images))
    # every row key is a real template column (HEADER has one duplicate name)
    assert set(rows[0].keys()) == set(HEADER)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("\nAll offline parser checks passed.")
