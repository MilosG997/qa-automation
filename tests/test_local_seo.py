"""Local SEO: each city landing page of Draganić Stolarija must really be about its city (requests, no browser)."""
import re

import pytest

from helpers import http

BASE = "https://draganicstolarija.rs"
CITIES = {  # page slug: (word that must appear in the H1, in the title)
    "stara-pazova": ("Staroj Pazovi", "Stara Pazova"),
    "nova-pazova": ("Novoj Pazovi", "Nova Pazova"),
    "beograd": ("Beogradu", "Beograd"),
    "novi-sad": ("Novom Sadu", "Novi Sad"),
}


def _page(slug):
    return http.get(f"{BASE}/pvc-stolarija-{slug}/", timeout=20).text


@pytest.mark.parametrize("slug", CITIES)
def test_city_page_headline_and_title_name_the_city(slug):
    html = _page(slug)
    in_h1, in_title = CITIES[slug]
    assert in_h1 in re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S).group(1)
    assert in_title in re.search(r"<title>(.*?)</title>", html).group(1)


@pytest.mark.parametrize("slug", CITIES)
def test_city_page_description_names_the_city(slug):
    description = re.search(r'<meta name="description" content="([^"]*)"', _page(slug)).group(1)
    assert CITIES[slug][0] in description, "same case as in the headline (u Staroj Pazovi)"


def test_home_page_mentions_every_city():
    html = http.get(BASE + "/", timeout=20).text
    for _, city in CITIES.values():
        assert city in html, city


def test_majstori_pazova_home_head():
    html = http.get("https://majstoripazova.rs/", timeout=20).text
    assert re.search(r'<html[^>]*lang="sr-Latn"', html)
    assert 'rel="canonical" href="https://majstoripazova.rs/"' in html
    assert "Stara Pazova" in re.search(r'<meta name="description" content="([^"]*)"', html).group(1)
    for prop in ["title", "description", "image", "url"]:
        assert f'property="og:{prop}"' in html
