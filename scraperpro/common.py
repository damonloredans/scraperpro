"""Shared helpers: HTTP session, slugify, HTML cleaning, weight parsing, JSON-LD."""
from __future__ import annotations

import html as _html
import json
import re
import time
import unicodedata


def html_unescape(s: str) -> str:
    return _html.unescape(s or "")

import requests
from bs4 import BeautifulSoup

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "application/json, text/html;q=0.9"})
    return s


def get_json(session: requests.Session, url: str, *, params: dict | None = None,
             retries: int = 3, pause: float = 1.0):
    """GET JSON with simple backoff. Returns parsed JSON or raises."""
    last = None
    for attempt in range(retries):
        try:
            r = session.get(url, params=params, timeout=30)
            if r.status_code == 200:
                return r.json()
            last = f"HTTP {r.status_code}"
        except requests.RequestException as e:  # network hiccup
            last = str(e)
        time.sleep(pause * (attempt + 1))
    raise RuntimeError(f"GET {url} failed after {retries} tries: {last}")


def get_html(session: requests.Session, url: str, *, retries: int = 3, pause: float = 1.0):
    last = None
    for attempt in range(retries):
        try:
            r = session.get(url, timeout=30)
            if r.status_code == 200:
                return r.text
            last = f"HTTP {r.status_code}"
        except requests.RequestException as e:
            last = str(e)
        time.sleep(pause * (attempt + 1))
    raise RuntimeError(f"GET {url} failed after {retries} tries: {last}")


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text).strip("-")


class HandlePool:
    """Hand out unique handles, appending -2, -3 ... on collision (Shopify behaviour)."""

    def __init__(self) -> None:
        self._seen: dict[str, int] = {}

    def take(self, base: str) -> str:
        base = slugify(base)
        n = self._seen.get(base, 0) + 1
        self._seen[base] = n
        return base if n == 1 else f"{base}-{n}"


# --- HTML / description cleaning -------------------------------------------------

_KEEP_TAGS = {"h1", "h2", "h3", "h4", "p", "ul", "ol", "li", "br", "strong", "em", "b", "i", "table", "tr", "td", "th"}


def clean_description(html: str) -> str:
    """Strip page-builder scaffolding (style blocks, wrapper divs, data-* attrs,
    inline styles) but keep the readable structure. Good enough for Magento
    PageBuilder and Avada/Fusion Builder markup."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["style", "script", "figure", "iframe", "noscript"]):
        tag.decompose()

    for tag in soup.find_all(True):
        if tag.name not in _KEEP_TAGS:
            tag.unwrap()
        else:
            tag.attrs = {}

    # collapse whitespace, drop empty blocks
    text = str(soup)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"<(p|li|h[1-4])>\s*</\1>", "", text)
    text = re.sub(r"(<br\s*/?>\s*){2,}", "<br>", text)
    return text.strip()


def plain_text(html: str) -> str:
    return re.sub(r"\s+", " ", BeautifulSoup(html or "", "lxml").get_text(" ")).strip()


def seo_description(html: str, limit: int = 320) -> str:
    t = plain_text(html)
    if len(t) <= limit:
        return t
    cut = t[:limit].rsplit(" ", 1)[0]
    return cut


# --- JSON-LD (barcode / gtin fallback) ----------------------------------------

def jsonld_blocks(html: str) -> list[dict]:
    out = []
    soup = BeautifulSoup(html, "lxml")
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(s.string or "{}")
        except (json.JSONDecodeError, TypeError):
            continue
        out.extend(data if isinstance(data, list) else [data])
    return out


def gtin_from_jsonld(html: str) -> dict[str, str]:
    """Return {sku_or_name: gtin} pulled from Product/Offer JSON-LD if present."""
    found: dict[str, str] = {}
    for block in jsonld_blocks(html):
        if block.get("@type") not in ("Product", ["Product"]):
            continue
        offers = block.get("offers") or []
        offers = offers if isinstance(offers, list) else [offers]
        for off in offers:
            key = off.get("sku") or off.get("mpn") or block.get("name") or ""
            gtin = (off.get("gtin13") or off.get("gtin12") or off.get("gtin")
                    or block.get("gtin13") or block.get("gtin12") or block.get("gtin"))
            if key and gtin:
                found[str(key)] = str(gtin)
    return found


class Progress:
    """Elapsed / rate / ETA printer for a loop of `total` items (total optional)."""

    def __init__(self, label: str, total: int | None = None) -> None:
        self.label = label
        self.total = total
        self.start = time.perf_counter()
        self.n = 0

    @staticmethod
    def _hms(s: float) -> str:
        s = int(s)
        return f"{s // 3600}h{s % 3600 // 60:02d}m{s % 60:02d}s" if s >= 3600 else f"{s // 60}m{s % 60:02d}s"

    def tick(self, note: str = "") -> None:
        self.n += 1
        el = time.perf_counter() - self.start
        rate = el / self.n
        msg = f"  [{self.label}] {self.n:>4}"
        if self.total:
            msg += f"/{self.total}"
        msg += f"  {note[:55]}"
        tail = f"{self._hms(el)} elapsed, {rate:.1f}s/item"
        if self.total and self.n < self.total:
            tail += f", ~{self._hms(rate * (self.total - self.n))} left"
        print(f"{msg}   ({tail})")

    def done(self) -> float:
        el = time.perf_counter() - self.start
        rate = el / self.n if self.n else 0
        print(f"  [{self.label}] done: {self.n} items in {self._hms(el)}  "
              f"({rate:.1f}s/item"
              + (f"  ->  ~{self._hms(rate * 1400)} for 1,400" if self.label == "Oakley SI" else "")
              + ")")
        return el


def grams(value, unit: str = "kg") -> int:
    """Normalise a weight to integer grams."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 0
    factor = {"kg": 1000, "g": 1, "lb": 453.592, "oz": 28.3495}.get(unit, 1000)
    return int(round(v * factor))
