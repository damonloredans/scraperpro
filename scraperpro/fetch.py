"""Fetchers — pluggable HTTP backends (same `.get(url, expect=None) -> str`).

`CurlCffiFetcher` impersonates Chrome's TLS/JA3 fingerprint, which (2026-09-10)
gets past Oakley SI's Akamai edge for plain GETs — but only for ~40–50 requests
before Akamai returns a JS-challenge shell (HTTP 200, no product data). curl_cffi
can't run that JS, so:
  - `throttle` paces requests,
  - `expect=` is a substring the real page must contain; if missing we treat the
    response as a soft block and back off exponentially.
For a full ~1,400-product crawl, seed the session with Akamai cookies from one
real-browser visit, rotate residential proxies, or use an unblocker API.

`FixtureFetcher` serves saved HTML from tests/fixtures — used by the offline
parser test so the transform can be verified without hitting the site.
"""
from __future__ import annotations

import glob
import os
import random
import time

_SOFT_BLOCK_MARKERS = ("security has been notified", "pardon our interruption",
                       "access to this page has been denied")


def _dotenv_get(key: str, path: str = ".env") -> str | None:
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip() or None
    return None


class BlockedError(RuntimeError):
    """Raised when the fetcher is persistently blocked — abort the whole run."""


class CurlCffiFetcher:
    def __init__(self, impersonate: str = "chrome", throttle: float = 3.0,
                 retries: int = 2, give_up_after: int = 2, proxy: str | None = None) -> None:
        from curl_cffi import requests as cr  # lazy: optional dependency
        # proxy: a rotating-residential endpoint, e.g.
        #   http://USER:PASS@gate.smartproxy.com:7000
        # Set it here, or via the SCRAPER_PROXY env var / .env. With a rotating
        # endpoint each request exits a different IP, so give_up_after can be high.
        proxy = proxy or os.environ.get("SCRAPER_PROXY") or _dotenv_get("SCRAPER_PROXY")
        kw = {"proxies": {"http": proxy, "https": proxy}} if proxy else {}
        self._session = cr.Session(impersonate=impersonate, **kw)
        self.proxied = bool(proxy)
        self.throttle = throttle if not proxy else min(throttle, 0.5)
        self.retries = retries
        self.give_up_after = give_up_after if not proxy else 8
        self._fails_in_a_row = 0
        self._last = 0.0
        if proxy:
            print(f"  [fetch] using proxy {proxy.split('@')[-1]}")

    def seed_cookies(self, cookies: dict) -> None:
        """Prime the session with Akamai cookies (_abck / bm_sv / ak_bmsc …)
        captured from a real browser, to ride past the JS challenge."""
        for k, v in cookies.items():
            self._session.cookies.set(k, v, domain=".oakleysi.com")

    def get(self, url: str, expect: str | None = None) -> str:
        if self._fails_in_a_row >= self.give_up_after:
            raise BlockedError(
                f"aborting: {self._fails_in_a_row} GETs in a row blocked by Akamai. "
                "Wait ~20-30 min, or use residential proxies / an unblocker.")
        last = "?"
        for attempt in range(self.retries):
            gap = self.throttle + random.uniform(0, 1.0) - (time.time() - self._last)
            if gap > 0:
                time.sleep(gap)
            self._last = time.time()
            try:
                r = self._session.get(url, timeout=30)
                low = r.text.lower()
                if r.status_code == 200 and not any(m in low for m in _SOFT_BLOCK_MARKERS):
                    if expect is None or expect.lower() in low:
                        self._fails_in_a_row = 0
                        return r.text
                    last = "soft block (missing expected content)"
                else:
                    last = f"HTTP {r.status_code}"
            except Exception as e:  # noqa: BLE001 - curl_cffi raises its own types
                last = str(e)
            if attempt < self.retries - 1:
                backoff = (attempt + 1) * 15          # 15, 30 s  (was 5/20/45/80/125)
                print(f"      retry {attempt + 1}/{self.retries} in {backoff}s ({last})")
                time.sleep(backoff)
        self._fails_in_a_row += 1
        raise RuntimeError(f"GET {url} failed after {self.retries} tries: {last}")


class UnblockerFetcher:
    """Routes every request through ScraperAPI, which solves Akamai and returns
    the target page's HTML. Free tier = 5,000 credits (covers the 1,541 catalogue
    even at ~2-3 credits/request). Set SCRAPERAPI_KEY in .env."""

    ENDPOINT = "http://api.scraperapi.com/"

    def __init__(self, key: str | None = None, throttle: float = 0.0) -> None:
        import requests  # plain requests is fine — ScraperAPI is the one hitting Oakley
        self._requests = requests
        self.key = key or os.environ.get("SCRAPERAPI_KEY") or _dotenv_get("SCRAPERAPI_KEY")
        if not self.key:
            raise RuntimeError("SCRAPERAPI_KEY not set")
        self.throttle = throttle
        self._fails_in_a_row = 0
        self.give_up_after = 5
        print("  [fetch] using ScraperAPI unblocker")

    def get(self, url: str, expect: str | None = None) -> str:
        if self._fails_in_a_row >= self.give_up_after:
            raise BlockedError("ScraperAPI returned unusable pages 5x in a row — "
                               "check credit balance / try ultra_premium")
        for attempt in range(3):
            if self.throttle:
                time.sleep(self.throttle)
            try:
                r = self._requests.get(self.ENDPOINT, params={
                    "api_key": self.key, "url": url, "country_code": "us",
                }, timeout=70)
                if r.status_code == 200 and (expect is None or expect.lower() in r.text.lower()):
                    self._fails_in_a_row = 0
                    return r.text
                last = f"HTTP {r.status_code}" if r.status_code != 200 else "missing expected content"
            except Exception as e:  # noqa: BLE001
                last = str(e)
            print(f"      scraperapi retry {attempt + 1}/3 ({last})")
            time.sleep(5)
        self._fails_in_a_row += 1
        raise RuntimeError(f"ScraperAPI GET {url} failed: {last}")


def make_fetcher(**kw):
    """SCRAPERAPI_KEY -> UnblockerFetcher; else CurlCffiFetcher (which auto-uses
    SCRAPER_PROXY if set)."""
    if os.environ.get("SCRAPERAPI_KEY") or _dotenv_get("SCRAPERAPI_KEY"):
        return UnblockerFetcher()
    return CurlCffiFetcher(**kw)


class FixtureFetcher:
    """Serves saved HTML by matching a substring of the URL to a fixture filename.
    `mapping` = {url_substring: path}."""

    def __init__(self, mapping: dict[str, str]) -> None:
        self.mapping = mapping

    @classmethod
    def from_dir(cls, path: str) -> "FixtureFetcher":
        m = {}
        for f in glob.glob(os.path.join(path, "*.html")):
            m[os.path.splitext(os.path.basename(f))[0]] = f
        return cls(m)

    def get(self, url: str, expect: str | None = None) -> str:
        for key, path in self.mapping.items():
            if key in url:
                with open(path, encoding="utf-8") as fh:
                    return fh.read()
        raise RuntimeError(f"no fixture for {url}")
