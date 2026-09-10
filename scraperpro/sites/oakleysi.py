"""Oakley SI — oakleysi.com/en-us — SAP Commerce Cloud + Akamai.

Recon 2026-09-10 (see docs/quote.md §3). Key facts the code below relies on:

* Akamai blocks plain HTTP clients, but a Chrome-TLS-impersonating client
  (curl_cffi) gets 200s. See scraperpro/fetch.py.
* Product pages are server-side rendered. Per page we read:
    - <h1>                                    -> title
    - .breadcrumb a                           -> Type / category
    - .singleContent blocks                   -> description + feature bullets
    - .sizeText parents                       -> frame/lens measurements
    - inline `utag_data.Products = {<UPC>:{ Sku, FrameColor, LensColor,
      LensTechnology, LensType, Category, ModelName, ... }}`  (CURRENT colour only)
    - body links `/en-us/product/<CODE>?variant=<UPC>`  -> this model's other colours
    - <img src=".../prod-onecp-record-files/...0OO9102__9102B9__P21__...">
      -> gallery, filter by the style-colour token (from Sku "OO9102-B9" -> "9102B9")
* Price is blank when logged out -> Variant Price stays "".
* Eyewear is one-size. Apparel/footwear/goggles have a size widget -> parse_sizes()
  (TODO: wire once discovery confirms the widget markup).

STATUS: eyewear path works end to end (`python run.py oakleysi --limit 3`).
Apparel/footwear size explosion is stubbed.
"""
from __future__ import annotations

import json
import re
import time

from bs4 import BeautifulSoup

from .. import common
from ..shopify_columns import Product, Variant

BASE = "https://www.oakleysi.com"

CATEGORIES = [
    "/en-us/category/sunglasses",
    "/en-us/category/eyeglasses",
    "/en-us/category/prescription",
    "/en-us/category/goggles/off-duty/snow-goggles",
    "/en-us/category/goggles/off-duty/mx-goggles",
    "/en-us/category/apparel",
    "/en-us/category/accessories",
    "/en-us/category/apparel/footwear",
]

_STYLE_RE = re.compile(r"/en-us/product/([A-Za-z0-9]+)")
_MAX_COLOURS = 12


class OakleySIScraper:
    vendor = "Oakley SI"

    def __init__(self, fetcher=None, throttle: float = 1.5) -> None:
        if fetcher is None:
            from ..fetch import CurlCffiFetcher
            fetcher = CurlCffiFetcher(throttle=throttle)
        self.fetch = fetcher
        self.handles = common.HandlePool()

    # ------------------------------------------------------------------ crawl
    def discover_product_urls(self, categories=CATEGORIES, max_pages: int = 60,
                              stop_at: int | None = None) -> list[str]:
        seen: dict[str, str] = {}          # style code -> full URL
        for cat in categories:
            if stop_at and len(seen) >= stop_at:
                break
            empty_streak = 0
            for page in range(1, max_pages + 1):
                if stop_at and len(seen) >= stop_at:
                    break
                sep = "&" if "?" in cat else "?"
                url = f"{BASE}{cat}{sep}q=%3AoakleyRelevanceSort&page={page}"
                try:
                    html = self.fetch.get(url, expect="/en-us/product/")
                except RuntimeError as e:
                    print(f"    ! {url}: {e}")
                    break
                codes = _style_codes(html)
                new = [c for c in codes if c not in seen]
                for c in new:
                    seen[c] = f"{BASE}/en-us/product/{c}"
                print(f"    {cat} p{page}: {len(codes)} links, {len(new)} new "
                      f"({len(seen)} total)")
                if not new:
                    empty_streak += 1
                    if empty_streak >= 2:
                        break
                else:
                    empty_streak = 0
        return list(seen.values())

    # ------------------------------------------------------------------- pdp
    def parse_product(self, url: str) -> Product | None:
        html = self.fetch.get(url, expect="pdp-hero-name")
        style = _STYLE_RE.search(url).group(1)
        soup = _clean_soup(html)

        h1 = soup.select_one("h1")
        if not h1:
            print(f"    ! no <h1> at {url}")
            return None
        name = common.html_unescape(h1.get_text(" ", strip=True))
        title = f"{self.vendor} {name}".strip()
        handle = self.handles.take(f"{style} {name}")

        crumbs = [a.get_text(strip=True) for a in soup.select(".breadcrumb a")]
        crumbs = [c for c in crumbs if c.lower() != "home"]
        product_type = crumbs[1] if len(crumbs) > 1 else (crumbs[0] if crumbs else "")

        body_html = _description(soup)
        seo_desc = _meta(soup, "description") or common.plain_text(body_html)[:320]

        # colour variants: this model's ?variant= UPCs in the body
        colour_upcs = _same_style_variants(html, style)
        current = _utag_products(html)                    # {upc: {...}} for the loaded colour
        by_upc = dict(current)
        for upc in colour_upcs:
            if upc in by_upc:
                continue
            if len(by_upc) >= _MAX_COLOURS:
                break
            try:
                vhtml = self.fetch.get(f"{BASE}/en-us/product/{style}?variant={upc}",
                                       expect="pdp-hero-name")
                by_upc.update(_utag_products(vhtml))
            except RuntimeError:
                by_upc.setdefault(upc, {})

        images = _images(soup)
        variants: list[Variant] = []
        for upc, d in by_upc.items():
            colour = d.get("FrameColor") or d.get("LensColor") or ""
            variants.append(Variant(
                option1=colour or "Default Title",
                option2="",                              # TODO apparel/footwear sizes
                sku=d.get("Sku") or style,
                grams=0,                                  # not on PDP
                barcode=str(upc),
                price="",                                 # login-gated
                image=_first_image_for(images, d.get("Sku", "")),
            ))
        if not variants:
            variants.append(Variant(option1="Default Title", sku=style, barcode=""))

        return Product(
            handle=handle,
            title=title,
            body_html=body_html,
            vendor=self.vendor,
            seo_title=f"{title}".strip(),
            seo_description=seo_desc,
            product_type=product_type,
            option1_name="Colour" if any(v.option1 != "Default Title" for v in variants) else "",
            variants=variants,
            images=images,
        )

    def run(self, limit: int | None = None) -> list[Product]:
        urls = self.discover_product_urls(stop_at=limit)
        print(f"  [{self.vendor}] discovered {len(urls)} products")
        if limit:
            urls = urls[:limit]
        out: list[Product] = []
        for i, u in enumerate(urls, 1):
            try:
                p = self.parse_product(u)
            except RuntimeError as e:
                print(f"    ! {u}: {e}")
                continue
            if p:
                out.append(p)
                print(f"  [{self.vendor}] {i:>4}  {p.title[:55]}  ({len(p.variants)} colours)")
            time.sleep(0.2)
        return out

    def download_images(self, products: list[Product], out_dir: str) -> int:
        """Save every product image to <out_dir>/<handle>/NN.png (origin PNG).

        Oakley images can't be imported into Shopify by URL (see `_images`), so
        the pipeline is: download here, bulk-upload to Shopify Files (or attach
        via the Admin API when creating the product), then swap the CSV
        `Image Src` values for the Shopify-hosted URLs.

        Image requests are NOT Akamai-gated the way page requests are, so a plain
        client works.
        """
        import os
        import requests

        sess = requests.Session()
        sess.headers["Accept"] = "image/*"          # not "image/avif" -> CDN returns origin PNG
        n = 0
        for p in products:
            pdir = os.path.join(out_dir, p.handle)
            os.makedirs(pdir, exist_ok=True)
            for idx, url in enumerate(dict.fromkeys(p.images), 1):
                dest = os.path.join(pdir, f"{idx:02d}.png")
                if os.path.exists(dest):
                    continue
                try:
                    r = sess.get(url, timeout=30)
                    r.raise_for_status()
                except requests.RequestException as e:
                    print(f"    ! image {url}: {e}")
                    continue
                with open(dest, "wb") as fh:
                    fh.write(r.content)
                n += 1
                time.sleep(0.1)
        return n


# --- helpers -----------------------------------------------------------------

def _style_codes(html: str) -> list[str]:
    soup = _clean_soup(html)
    out = []
    for a in soup.select('a[href*="/en-us/product/"]'):
        m = _STYLE_RE.search(a.get("href", ""))
        if m and m.group(1) not in out:
            out.append(m.group(1))
    return out


def _clean_soup(html: str) -> BeautifulSoup:
    """Strip site chrome (global header/nav/footer) but NOT the in-page
    `<header class="pdp-hero-header">` that holds the product <h1>."""
    soup = BeautifulSoup(html, "lxml")
    for t in soup.select(
        "script, style, "
        "#global-header-dropdown, .global-header, .navigation-menu, "
        ".site-footer, footer.footer, .footer-wrapper, .cart-flyout, "
        ".breadcrumb ~ nav, .so-container"
    ):
        t.decompose()
    return soup


def _same_style_variants(html: str, style: str) -> list[str]:
    return list(dict.fromkeys(
        re.findall(rf"/en-us/product/{re.escape(style)}\?variant=(\d+)", html)
    ))


def _brace_match(s: str, start: int) -> str:
    """Return the {...} literal beginning at s[start] == '{', brace-balanced,
    ignoring braces inside double-quoted strings."""
    depth, in_str, esc = 0, False, False
    for i in range(start, len(s)):
        c = s[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return s[start:i + 1]
    return ""


_UTAG_ASSIGN_RE = re.compile(r'"Products"\s*:\s*\{')


def _utag_products(html: str) -> dict:
    """Extract the `"Products":{ <UPC>:{...} }` object embedded in the page's
    inline `utag_data` literal. Keys are unquoted numeric UPCs (JS, not JSON).
    Several matches may exist; take whichever parses to a dict of variant
    records (each has a `Sku`)."""
    for m in _UTAG_ASSIGN_RE.finditer(html):
        blob = _brace_match(html, m.end() - 1)
        if not blob:
            continue
        blob = re.sub(r"([{,]\s*)(\d{6,})(\s*:)", r'\1"\2"\3', blob)  # quote numeric keys
        try:
            data = json.loads(blob)
        except json.JSONDecodeError:
            continue
        if set(data) == {"Products"} and isinstance(data["Products"], dict):
            data = data["Products"]
        recs = {str(k): v for k, v in data.items()
                if isinstance(v, dict) and "Sku" in v}
        if recs:
            return recs
    return {}


def _description(soup: BeautifulSoup) -> str:
    parts = [str(d) for d in soup.select(".singleContent")]
    if not any("FRAME & LENSES" in p or "Lens Width" in p for p in parts):
        # some PDPs keep the measurements outside .singleContent
        meas = soup.select(".sizeText")
        if meas:
            rows = "".join(f"<li>{m.find_parent().get_text(' ', strip=True)}</li>" for m in meas)
            parts.append(f"<h3>Frame &amp; Lenses</h3><ul>{rows}</ul>")
    return common.clean_description("".join(parts))


def _meta(soup: BeautifulSoup, name: str) -> str:
    m = soup.select_one(f'meta[name="{name}"]')
    return common.html_unescape(m["content"]) if m and m.get("content") else ""


IMG_ORIGIN_QS = "?imFmt=jpg"   # any non-`impolicy` param -> CDN serves the origin PNG, not AVIF


def _images(soup: BeautifulSoup) -> list[str]:
    """Product shots from the `assets*.oakley.com` CDN.

    The CDN does Accept-header format negotiation: the plain URL and any
    `?impolicy=...` transform URL serve **AVIF**, which Shopify's media pipeline
    rejects ("Media processing failed"). `IMG_ORIGIN_QS` forces the origin PNG.

    NOTE: importing these by URL in a CSV still fails for Oakley — Shopify's
    importer drops the query string and/or Akamai blocks Shopify's fetcher IPs.
    Oakley images must be **downloaded and rehosted** (Shopify Files, or attach
    via the Admin API when creating the product). See `download_images()` and
    docs/quote.md.
    """
    out = []
    for img in soup.select("img"):
        src = img.get("src") or img.get("data-src") or ""
        if "prod-onecp-record-files" in src:
            out.append(src.split("?")[0] + IMG_ORIGIN_QS)
    return list(dict.fromkeys(out))


def _first_image_for(images: list[str], sku: str) -> str:
    token = sku.replace("-", "").replace("OO", "", 1) if sku else ""
    for u in images:
        if token and token in u:
            return u
    return images[0] if images else ""
