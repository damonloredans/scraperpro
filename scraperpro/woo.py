"""WooCommerce Store API scraper base.

Both Princeton Tec and Crispi AU expose the public, unauthenticated
`/wp-json/wc/store/v1/` API, which is enough for everything except barcodes
(not exposed by the Store API — we fall back to JSON-LD on the product page).

Verified endpoints (2026-09-10):
  GET /wp-json/wc/store/v1/products?per_page=100&page=N        -> parent products
  GET /wp-json/wc/store/v1/products?type=variation&parent=ID   -> variation objects
                                                                  (sku, prices, weight, images;
                                                                   NOTE: their `attributes` array is empty)

The attribute values for each variation come from the PARENT product:
  parent["attributes"]  -> {name, has_variations, terms:[{slug, name}]}   (slug -> display map)
  parent["variations"]  -> [{id, attributes:[{name, value(slug)}]}]        (variation id -> slugs)
"""
from __future__ import annotations

import re
import time

from . import common
from .shopify_columns import Product, Variant

STORE_API = "/wp-json/wc/store/v1/products"


class WooScraper:
    vendor = ""
    base_url = ""                       # e.g. "https://princetontec.com"
    colour_attr_names = {"color", "colour"}
    size_attr_names = {"size"}
    fetch_barcodes = True               # hit each PDP for JSON-LD gtin
    include_price = True                 # copy the source RRP into Variant Price
    throttle = 0.5                       # seconds between requests

    def __init__(self) -> None:
        self.session = common.make_session()
        self.handles = common.HandlePool()

    # -- crawling --------------------------------------------------------------

    def iter_parent_products(self):
        page = 1
        while True:
            data = common.get_json(
                self.session, self.base_url + STORE_API,
                params={"per_page": 100, "page": page},
            )
            if not data:
                return
            yield from data
            if len(data) < 100:
                return
            page += 1
            time.sleep(self.throttle)

    def fetch_variations(self, parent_id: int) -> list[dict]:
        try:
            return common.get_json(
                self.session, self.base_url + STORE_API,
                params={"type": "variation", "parent": parent_id, "per_page": 100},
            )
        except RuntimeError:
            return []

    def fetch_full_parent(self, parent_id: int) -> dict:
        """The single-product endpoint populates `variations` (id -> attribute
        slugs) more reliably than the list payload does."""
        try:
            return common.get_json(
                self.session, f"{self.base_url}{STORE_API}/{parent_id}",
            )
        except RuntimeError:
            return {}

    # -- attribute plumbing --------------------------------------------------------

    def _attr_role(self, name: str) -> str:
        n = (name or "").strip().lower()
        if n in self.colour_attr_names:
            return "colour"
        if n in self.size_attr_names:
            return "size"
        return "other"

    @staticmethod
    def _slug_to_name(parent: dict) -> dict[str, dict[str, str]]:
        """{attr_name: {term_slug: term_display_name}}"""
        out: dict[str, dict[str, str]] = {}
        for attr in parent.get("attributes", []):
            out[attr["name"]] = {t["slug"]: t.get("name", t["slug"])
                                 for t in attr.get("terms", [])}
        return out

    @staticmethod
    def _variation_attr_slugs(parent: dict) -> dict[int, list[tuple[str, str]]]:
        """{variation_id: [(attr_name, term_slug), ...]}"""
        return {
            v["id"]: [(a["name"], a.get("value", "")) for a in v.get("attributes", [])]
            for v in parent.get("variations", [])
        }

    _VAR_STRING_RE = re.compile(r"([A-Za-z][\w /-]*?):\s*(.*?)(?=,\s+[A-Za-z][\w /-]*?:\s|$)")

    @classmethod
    def _parse_variation_string(cls, s: str) -> list[tuple[str, str]]:
        """'Color: Black, Size: EU 42 [UK 8]' -> [('Color','Black'), ('Size','EU 42 [UK 8]')]"""
        return [(m.group(1).strip(), m.group(2).strip()) for m in cls._VAR_STRING_RE.finditer(s or "")]

    def _axis_attr_names(self, parent: dict) -> list[str]:
        """Attribute names that are real option axes: vary AND have >1 term."""
        names = []
        for attr in parent.get("attributes", []):
            if attr.get("has_variations") and len(attr.get("terms", [])) > 1:
                names.append(attr["name"])
        return names

    def _resolve_options(self, axis_names: list[str]) -> tuple[tuple[str, str, str], dict[str, int]]:
        """Pack the option axes into Option1/2/3 **in order, with no gaps** —
        Shopify rejects a product that has Option2 set but Option1 empty. Order
        of preference: Colour, then Size, then anything else. So a size-only
        product gets `Option1 Name = Size`, not Option2.

        Returns the option *names* tuple and a {attr_name: slot_index} map so
        each variant's values land in the slot matching its name.
        """
        def rank(name: str) -> int:
            return {"colour": 0, "size": 1}.get(self._attr_role(name), 2)

        display = {"colour": "Colour", "size": "Size"}
        # (the sample's "Size " has a stray trailing space — dropped; it risks a
        #  literal "Size " option name on import)
        ordered = sorted(axis_names, key=rank)[:3]
        slots = ["", "", ""]
        slot_of: dict[str, int] = {}
        for i, name in enumerate(ordered):
            slots[i] = display.get(self._attr_role(name), name)
            slot_of[name] = i
        return tuple(slots), slot_of  # type: ignore[return-value]

    # -- transform ----------------------------------------------------------------

    def normalise_size(self, value: str) -> str:
        return value

    def _variant_from(self, var: dict, translated: list[tuple[str, str]],
                      slot_of: dict[str, int], barcodes: dict) -> Variant:
        opts = ["", "", ""]
        for name, disp in translated:
            slot = slot_of.get(name)
            if slot is None:
                continue
            opts[slot] = self.normalise_size(disp) if self._attr_role(name) == "size" else disp
        sku = var.get("sku") or ""
        if not any(opts):
            opts[0] = "Default Title"
        price, compare_at = self._prices(var.get("prices"))
        return Variant(
            option1=opts[0],
            option2=opts[1],
            option3=opts[2],
            sku=sku,
            grams=common.grams(var.get("weight"), "kg"),
            barcode=barcodes.get(sku, "") or barcodes.get(var.get("name", ""), ""),
            price=price,
            compare_at=compare_at,
            image=(var.get("images") or [{}])[0].get("src", ""),
        )

    def _prices(self, prices: dict | None) -> tuple[str, str]:
        """Source RRP -> (Variant Price, Variant Compare At Price).

        WooCommerce Store API gives amounts in minor units (cents). This is the
        *source retailer's* list price -- Princeton Tec in USD, Crispi in AUD.
        The client decides whether to keep it, convert it, or apply a margin
        (see docs/quote.md confirmations). We just capture what the site shows.
        """
        if not self.include_price or not prices:
            return "", ""
        unit = 10 ** int(prices.get("currency_minor_unit", 2))

        def _fmt(v):
            try:
                amount = int(v) / unit
            except (TypeError, ValueError):
                return ""
            return f"{amount:.2f}" if amount > 0 else ""   # 0 = "not published via API"

        price = _fmt(prices.get("price"))
        regular = _fmt(prices.get("regular_price"))
        # only set Compare At when there's a genuine markdown
        compare_at = regular if regular and price and regular != price else ""
        return price, compare_at

    @staticmethod
    def _expected_combo_count(raw: dict, axis_names: list[str]) -> int:
        n = 1
        for attr in raw.get("attributes", []):
            if attr["name"] in axis_names:
                n *= max(1, len(attr.get("terms", [])))
        return n

    def _synth_variants(self, raw: dict, axis_names: list[str],
                        slot_of: dict[str, int]) -> list[Variant]:
        import itertools
        per_axis = []
        for attr in raw.get("attributes", []):
            if attr["name"] not in axis_names:
                continue
            per_axis.append([(attr["name"], t.get("name", t["slug"]))
                             for t in attr.get("terms", [])])
        out = []
        for combo in itertools.product(*per_axis):
            out.append(self._variant_from(
                {"sku": "", "weight": raw.get("weight"), "images": [],
                 "prices": raw.get("prices")},
                list(combo), slot_of, {}))
        return out

    def build_product(self, raw: dict) -> Product:
        title = common.html_unescape(raw.get("name", ""))
        title = f"{self.vendor} {title}".strip() if self.vendor else title
        handle = self.handles.take(title)

        desc_src = raw.get("description") or raw.get("short_description") or ""
        body = common.clean_description(desc_src)
        images = [img.get("src", "") for img in raw.get("images", [])]

        barcodes: dict[str, str] = {}
        if self.fetch_barcodes and raw.get("permalink"):
            try:
                barcodes = common.gtin_from_jsonld(common.get_html(self.session, raw["permalink"]))
            except RuntimeError:
                pass
            time.sleep(self.throttle)

        axis_names = self._axis_attr_names(raw)
        (o1, o2, o3), slot_of = self._resolve_options(axis_names)
        slug2name = self._slug_to_name(raw)

        variants: list[Variant] = []
        if raw.get("type") == "variable":
            variations = self.fetch_variations(raw["id"])
            var_slugs = self._variation_attr_slugs(raw)
            if variations and not any(var_slugs.get(v["id"]) for v in variations):
                # list payload didn't carry the attribute map — ask the single-product endpoint
                var_slugs = self._variation_attr_slugs(self.fetch_full_parent(raw["id"]))

            for var in variations:
                slugs = var_slugs.get(var["id"], [])
                if slugs:
                    translated = [(n, slug2name.get(n, {}).get(s, s)) for n, s in slugs]
                else:
                    translated = self._parse_variation_string(var.get("variation", ""))
                variants.append(self._variant_from(var, translated, slot_of, barcodes))

            expected = self._expected_combo_count(raw, axis_names)
            if axis_names and len(_dedupe_variants(variants)) < expected:
                # Store API under-reports variations for this product (common on
                # Crispi). Synthesize the full option grid from the parent's
                # attribute terms, then splice back any real SKU'd variants we
                # did get, matched on option values.
                synth = self._synth_variants(raw, axis_names, slot_of)
                real = {(v.option1, v.option2, v.option3): v for v in variants if v.sku}
                for i, sv in enumerate(synth):
                    hit = real.get((sv.option1, sv.option2, sv.option3))
                    if hit:
                        synth[i] = hit
                missing = sum(1 for v in synth if not v.sku)
                variants = synth
                print(f"      ! {raw.get('name','')}: {len(synth)} variants, "
                      f"{missing} without SKU (Store API exposed {len(variations)}/{expected})")

        variants = _dedupe_variants(variants)

        if not variants:
            price, compare_at = self._prices(raw.get("prices"))
            variants.append(Variant(
                option1="Default Title",
                sku=raw.get("sku") or "",
                grams=common.grams(raw.get("weight"), "kg"),
                barcode=next(iter(barcodes.values()), ""),
                price=price,
                compare_at=compare_at,
            ))
            o1 = o2 = o3 = ""

        return Product(
            handle=handle,
            title=title,
            body_html=body,
            vendor=self.vendor,
            seo_title=f"{title} {self.vendor}".strip(),
            seo_description=common.seo_description(desc_src),
            option1_name=o1, option2_name=o2, option3_name=o3,
            variants=variants,
            images=images,
        )

    def run(self, limit: int | None = None) -> list[Product]:
        products: list[Product] = []
        prog = common.Progress(self.vendor)
        for i, raw in enumerate(self.iter_parent_products()):
            if limit and i >= limit:
                break
            products.append(self.build_product(raw))
            prog.tick(raw.get("name", ""))
        prog.done()
        return products


def _dedupe_variants(variants: list[Variant]) -> list[Variant]:
    seen, out = set(), []
    for v in variants:
        key = (v.option1, v.option2, v.option3, v.sku)
        if key in seen:
            continue
        seen.add(key)
        out.append(v)
    return out
