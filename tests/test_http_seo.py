"""What Google and social apps read from the raw HTML, checked page by page with requests (no browser).

A browser test sees the page after JavaScript; crawlers and link previews often do not. These tests read the
HTML exactly as it is served: language, Open Graph, robots, hreflang pairs, assets and share images.
"""
import re

import pytest

from helpers import http

DS = "https://draganicstolarija.rs"
MG = "https://mechanicallygifted.rs"
DS_PAGES = ["/", "/usluge/", "/kontakt/", "/politika-privatnosti/"] + \
    [f"/usluge/{s}/" for s in ["pvc-prozori", "alu-stolarija", "okapnice", "montaza-i-ugradnja",
                               "popravka-prozora", "stolarija-po-meri"]] + \
    [f"/pvc-stolarija-{c}/" for c in ["stara-pazova", "nova-pazova", "beograd", "novi-sad"]]
MG_PAGES = {"/": "sr", "/en/": "en", "/privatnost/": "sr", "/en/privacy/": "en"}


def _get(url):
    response = http.get(url, timeout=20)
    response.raise_for_status()
    return response.text


def _og(html, prop):
    found = re.search(rf'property="og:{prop}" content="([^"]*)"', html)
    return found.group(1) if found else None


# ---- Draganić Stolarija ----

@pytest.mark.parametrize("path", DS_PAGES)
def test_draganic_page_head(path):
    html = _get(DS + path)
    assert re.search(r'<html[^>]*lang="sr-Latn"', html)
    assert _og(html, "url") == DS + path
    assert _og(html, "title") and "Draganić" in _og(html, "title")
    assert "index, follow" in re.search(r'name="robots" content="([^"]*)"', html).group(1)
    assert "tel:+381641257573" in html, "every page has a call link in the HTML itself"


@pytest.mark.parametrize("path", DS_PAGES)
def test_draganic_share_image_is_served(path):
    image = _og(_get(DS + path), "image")
    response = http.head(image, timeout=20)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("image/")


def test_draganic_404_is_not_indexed():
    response = http.get(DS + "/nema-ove-strane/", timeout=20)
    assert response.status_code == 404
    assert "noindex" in response.text


# ---- Mechanically Gifted ----

@pytest.mark.parametrize("path,lang", MG_PAGES.items())
def test_mg_page_language_and_locale(path, lang):
    html = _get(MG + path)
    assert re.search(rf'<html[^>]*lang="{lang}"', html)
    assert _og(html, "locale") == {"sr": "sr_RS", "en": "en_US"}[lang]
    assert len(re.findall(r"<h1[ >]", html)) == 1


@pytest.mark.parametrize("path", MG_PAGES)
def test_mg_hreflang_pairs_point_back(path):
    """Each language version must list the other one, and that one must list it back."""
    links = dict(re.findall(r'hreflang="([^"]+)" href="([^"]+)"', _get(MG + path)))
    assert {"sr", "en", "x-default"} <= links.keys()
    assert MG + path in links.values(), "a page lists itself"
    other = links["en"] if links["sr"] == MG + path else links["sr"]
    back = dict(re.findall(r'hreflang="([^"]+)" href="([^"]+)"', _get(other)))
    assert MG + path in back.values()


@pytest.mark.parametrize("path", ["/nema-ove-strane", "/en/no-such-page"])
def test_mg_404_is_not_indexed(path):
    response = http.get(MG + path, timeout=20)
    assert response.status_code == 404
    assert 'name="robots" content="noindex' in response.text


@pytest.mark.parametrize("path", ["/", "/en/"])
def test_mg_every_local_asset_is_served(path):
    assets = set(re.findall(r'(?:src|href)="(/[^"#?]+\.(?:webp|png|svg|ico|woff2|jpg))"', _get(MG + path)))
    assert len(assets) >= 15
    missing = [a for a in sorted(assets) if http.head(MG + a, timeout=20).status_code != 200]
    assert missing == []


def test_mg_sitemap_alternates_match_the_pages():
    xml = _get(MG + "/sitemap.xml")
    for path in MG_PAGES:
        assert f"<loc>{MG}{path}</loc>" in xml
    assert xml.count('hreflang="x-default"') == len(MG_PAGES)
