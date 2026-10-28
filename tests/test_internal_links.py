"""No broken internal links: every link and asset on every page of my sites must answer 200 (requests, no browser).

Pages come from each site's sitemap, so a new page is checked automatically the day it is published.
"""
import re
from urllib.parse import urljoin

import pytest

from helpers import http

SITES = {"draganicstolarija.rs": "https://draganicstolarija.rs", "mechanicallygifted.rs": "https://mechanicallygifted.rs"}


def _sitemap_pages(base):
    return re.findall(r"<loc>([^<]+)</loc>", http.get(base + "/sitemap.xml", timeout=20).text)


def _internal_targets(page_url, base):
    html = http.get(page_url, timeout=20).text
    found = set()
    for ref in re.findall(r'(?:href|src)="([^"]+)"', html):
        url = urljoin(page_url, ref).split("#")[0]
        if url.startswith(base) and not url.endswith("/sitemap.xml"):
            found.add(url)
    return found


PAGES = [(site, page) for site, base in SITES.items() for page in _sitemap_pages(base)]


@pytest.mark.parametrize("site,page", PAGES, ids=[p.split("//", 1)[1] for _, p in PAGES])
def test_no_broken_internal_links(site, page):
    targets = _internal_targets(page, SITES[site])
    assert targets, "a page with no internal links at all is suspicious"
    broken = [(url, code) for url in sorted(targets)
              if (code := http.head(url, timeout=20, allow_redirects=True).status_code) != 200]
    assert broken == []
