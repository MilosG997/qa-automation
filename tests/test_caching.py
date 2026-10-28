"""Browser caching on my sites: fingerprinted CSS and fonts cached for a year, images for a month.

Wrong cache headers do not break anything visibly, they just make every repeat visit slower, so they are tested.
"""
import pytest

from helpers import http

LONG = 31536000   # one year, for files whose name changes when the content changes
MONTH = 2592000

CASES = {
    "mg-font": ("https://mechanicallygifted.rs/fonts/geist-mono-latin-wght-normal.woff2", LONG, "font/woff2"),
    "mg-photo": ("https://mechanicallygifted.rs/img/milos.webp", MONTH, "image/webp"),
    "mg-favicon": ("https://mechanicallygifted.rs/favicon.svg", MONTH, "image/svg+xml"),
    "ds-font": ("https://draganicstolarija.rs/fonts/archivo-latin.woff2", LONG, "font/woff2"),
    "ds-photo": ("https://draganicstolarija.rs/img/radovi/pvc-ulazna-vrata-1-640.webp", MONTH, "image/webp"),
}


def _max_age(cache_control):
    for part in cache_control.replace(" ", "").split(","):
        if part.startswith("max-age="):
            return int(part.split("=", 1)[1])
    return 0


@pytest.mark.parametrize("name", CASES)
def test_static_files_are_cached(name):
    url, at_least, content_type = CASES[name]
    response = http.head(url, timeout=20)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(content_type)
    assert _max_age(response.headers.get("Cache-Control", "")) >= at_least


def test_fingerprinted_css_is_immutable():
    """The stylesheet name carries a content hash, so it can be cached forever."""
    html = http.get("https://draganicstolarija.rs/", timeout=20).text
    css = html.split('rel="stylesheet" href="', 1)[1].split('"', 1)[0]
    assert css.startswith("/css/stil.") and css.endswith(".css")
    headers = http.head("https://draganicstolarija.rs" + css, timeout=20).headers
    assert "immutable" in headers["Cache-Control"]


@pytest.mark.parametrize("url", ["https://mechanicallygifted.rs/", "https://draganicstolarija.rs/"])
def test_html_is_not_cached_for_long(url):
    """Pages themselves must be revalidated, or visitors would keep seeing an old version after a deploy."""
    assert _max_age(http.head(url, timeout=20).headers.get("Cache-Control", "")) <= 3600
