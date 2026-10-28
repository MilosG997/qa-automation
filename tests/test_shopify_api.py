"""Shopify storefront JSON endpoints of Eskay Products (read-only, no browser).

Themes and apps rely on these public endpoints; if a theme change or an app breaks them, the store breaks quietly.
Nothing is bought and no cart is created: only GET requests.
"""
import os
import re

import pytest

from helpers import http

pytestmark = pytest.mark.shopify
STORE = os.environ.get("SHOP_URL", "https://eskayproducts.com").rstrip("/")


@pytest.fixture(scope="module")
def products():
    response = http.get(STORE + "/products.json?limit=10", timeout=30)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/json")
    return response.json()["products"]


def test_catalog_has_published_products(products):
    assert len(products) >= 5
    assert all(p["published_at"] for p in products)


def test_every_product_has_handle_title_and_image(products):
    for p in products:
        assert re.fullmatch(r"[a-z0-9-]+", p["handle"]), p["handle"]
        assert p["title"].strip()
        assert p["images"], f'{p["handle"]} has no image'


def test_variant_prices_are_positive_numbers(products):
    for p in products:
        for v in p["variants"]:
            assert float(v["price"]) > 0, f'{p["handle"]}: price {v["price"]}'


def test_product_js_matches_products_json(products):
    """The theme's /products/<handle>.js (used by Add to cart) must agree with the catalog."""
    first = products[0]
    detail = http.get(f'{STORE}/products/{first["handle"]}.js', timeout=30).json()
    assert detail["id"] == first["id"]
    assert detail["handle"] == first["handle"]
    assert len(detail["variants"]) == len(first["variants"])


def test_collections_are_published():
    collections = http.get(STORE + "/collections.json", timeout=30).json()["collections"]
    assert len(collections) >= 5
    assert all(c["handle"] and c["title"] for c in collections)


def test_collection_lists_its_products():
    handle = http.get(STORE + "/collections.json", timeout=30).json()["collections"][0]["handle"]
    response = http.get(f"{STORE}/collections/{handle}/products.json?limit=5", timeout=30)
    assert response.status_code == 200
    assert "products" in response.json()


def test_new_visitor_cart_is_empty():
    cart = http.get(STORE + "/cart.js", timeout=30).json()
    assert cart["item_count"] == 0
    assert cart["items"] == []


def test_search_suggestions_return_products():
    response = http.get(STORE + "/search/suggest.json", params={"q": "cups", "resources[type]": "product"}, timeout=30)
    found = response.json()["resources"]["results"]["products"]
    assert found
    assert all(item["url"].startswith("/products/") for item in found)


def test_robots_keeps_checkout_out_of_search():
    robots = http.get(STORE + "/robots.txt", timeout=30).text
    assert "Disallow: /checkout" in robots
    assert "Sitemap:" in robots


def test_sitemap_index_lists_child_sitemaps():
    xml = http.get(STORE + "/sitemap.xml", timeout=30).text
    assert xml.count("<sitemap>") >= 3


def test_www_redirects_to_the_main_domain():
    response = http.get("https://www.eskayproducts.com/", allow_redirects=False, timeout=30)
    assert response.status_code == 301
    assert response.headers["Location"] == STORE + "/"
