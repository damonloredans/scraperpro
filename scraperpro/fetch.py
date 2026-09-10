"""Fetchers — pluggable HTTP backends.

`CurlCffiFetcher` impersonates Chrome's TLS/JA3 fingerprint, which (as of
2026-09-10) is enough to get past Oakley SI's Akamai edge for plain GETs.

Akamai still soft-blocks after a burst: it returns HTTP 200 with a JS-challenge
shell instead of the real page. curl_cffi can't run that JS, so the mitigations
here are (a) a real throttle, (b) `expect=` — a substring the real page must
contain; if it's missing we treat the response as a soft block and back off.

For production-scale crawling, seed `Session` cookies from a real browser once
per run, or swap in a Playwright-based fetcher with the same `.get()` signature.
"""
from __future__ import annotations

import random
import time

_SOFT_BLOCK_MARKERS = ("security has been notified", "pardon our interruption",
                       "access to this page has been denied")


class CurlCffiFetcher:
    def __init__(self, impersonate: str = "chrome", throttle: float = 3.0,
                 retries: int = 5) -> None:
        from curl_cffi import requests as cr  # lazy: optional dependency
        self._session = cr.Session(impersonate=impersonate)
        self.throttle = throttle
        self.retries = retries
        self._last = 0.0

    def get(self, url: str, expect: str | None = None) -> str:
        last = "?"
        for attempt in range(self.retries):
            gap = self.throttle + random.uniform(0, 1.0) - (time.time() - self._last)
            if gap > 0:
                time.sleep(gap)
            self._last = time.time()
            try:
                r = self._session.get(url, timeout=30)
                body = r.text
                low = body.lower()
                if r.status_code == 200 and not any(m in low for m in _SOFT_BLOCK_MARKERS):
                    if expect is None or expect.lower() in low:
                        return body
                    last = "soft block (missing expected content)"
                else:
                    last = f"HTTP {r.status_code}"
            except Exception as e:  # noqa: BLE001 - curl_cffi raises its own types
                last = str(e)
            backoff = (attempt + 1) ** 2 * 5          # 5, 20, 45, 80, 125 s
            print(f"      retry {attempt + 1}/{self.retries} in {backoff}s ({last})")
            time.sleep(backoff)
        raise RuntimeError(f"GET {url} failed after {self.retries} tries: {last}")
