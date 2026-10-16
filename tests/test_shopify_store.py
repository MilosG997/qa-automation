"""Smoke tests for a live Shopify store (Eskay Products).

Read-only: nothing is bought, no account is created, the cart is never checked out.
"""
import os

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from helpers import has_horizontal_scroll

pytestmark = pytest.mark.shopify
STORE = os.environ.get("SHOP_URL", "https://eskayproducts.com").rstrip("/")
PRODUCT_LINKS = (By.CSS_SELECTOR, "main a[href*='/products/']")


def test_home_page_loads(driver):
    driver.get(STORE + "/")
    assert "Eskay" in driver.title
    assert driver.find_elements(By.CSS_SELECTOR, "a[href$='/cart']")


def test_search_returns_products(driver, wait):
    driver.get(STORE + "/search?q=cups&type=product")
    results = wait(driver).until(EC.presence_of_all_elements_located(PRODUCT_LINKS))
    assert len(results) >= 3


def test_collection_page_lists_products(driver, wait):
    driver.get(STORE + "/collections/all")
    products = wait(driver).until(EC.presence_of_all_elements_located(PRODUCT_LINKS))
    assert len({p.get_attribute("href").split("?")[0] for p in products}) >= 4


def test_product_page_has_price_and_add_to_cart(driver, wait):
    driver.get(STORE + "/search?q=cups&type=product")
    first = wait(driver).until(EC.presence_of_element_located(PRODUCT_LINKS))
    driver.get(first.get_attribute("href"))
    form = wait(driver).until(EC.presence_of_element_located((By.CSS_SELECTOR, "form[action*='/cart/add']")))
    assert form.find_elements(By.CSS_SELECTOR, "[type='submit'], button[name='add']")
    assert "$" in driver.find_element(By.TAG_NAME, "main").text


def test_products_json_endpoint(driver):
    """Shopify exposes /products.json: a quick check that the catalog is published."""
    driver.get(STORE + "/products.json?limit=5")
    assert '"products"' in driver.page_source


@pytest.mark.mobile
def test_no_horizontal_scroll_on_phone(phone):
    phone.get(STORE + "/")
    assert not has_horizontal_scroll(phone)
