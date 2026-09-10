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
        """Assign option axes to slots 0/1/2 and return both the option *names*
        and a {attr_name: slot_index} map so variant values land in the same
        slot as their name."""
        slots = ["", "", ""]
        slot_of: dict[str, int] = {}
        pending = []
        for name in axis_names:
            role = self._attr_role(name)
            if role == "colour" and not slots[0]:
                slots[0], slot_of[name] = "Colour", 0
            elif role == "size" and not slots[1]:
                slots[1], slot_of[name] = "Size ", 1   # trailing space matches the sample
            else:
                pending.append(name)
        for name in pending:
            for i in range(3):
                if not slots[i]:
                    slots[i], slot_of[name] = name, i
                    break
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
            opts[slot] = self.normalise_size(disp) if slot == 1 else disp
        sku = var.get("sku") or ""
        if not any(opts):
            opts[0] = "Default Title"
        return Variant(
            option1=opts[0],
            option2=opts[1],
            option3=opts[2],
            sku=sku,
            grams=common.grams(var.get("weight"), "kg"),
            barcode=barcodes.get(sku, "") or barcodes.get(var.get("name", ""), ""),
            price="",   # client sets pricing (blank in the sample)
            image=(var.get("images") or [{}])[0].get("src", ""),
        )

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
            out.append(self._variant_from({"sku": "", "weight": raw.get("weight"), "images": []},
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
            variants.append(Variant(
                option1="Default Title",
                sku=raw.get("sku") or "",
                grams=common.grams(raw.get("weight"), "kg"),
                barcode=next(iter(barcodes.values()), ""),
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
        for i, raw in enumerate(self.iter_parent_products()):
            if limit and i >= limit:
                break
            products.append(self.build_product(raw))
            print(f"  [{self.vendor}] {i + 1:>4}  {raw.get('name', '')[:60]}")
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
