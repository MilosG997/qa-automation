"""Mechanically Gifted (my own site): SEO basics, language switch, contact links, mobile layout."""
import os

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from helpers import console_errors, has_horizontal_scroll, meta

BASE = os.environ.get("MG_URL", "https://mechanicallygifted.netlify.app").rstrip("/")


@pytest.mark.parametrize("path,lang", [("/", "sr"), ("/en/", "en")])
def test_page_has_seo_basics(driver, path, lang):
    driver.get(BASE + path)
    assert driver.find_element(By.TAG_NAME, "html").get_attribute("lang") == lang
    assert "Mechanically Gifted" in driver.title
    assert len(driver.find_elements(By.TAG_NAME, "h1")) == 1, "exactly one h1 per page"
    description = meta(driver, 'meta[name="description"]')
    assert description and 50 <= len(description) <= 170
    assert meta(driver, 'link[rel="canonical"]', "href")
    hreflangs = {e.get_attribute("hreflang") for e in
                 driver.find_elements(By.CSS_SELECTOR, 'link[rel="alternate"][hreflang]')}
    assert {"sr", "en", "x-default"} <= hreflangs
    assert meta(driver, 'meta[property="og:image"]')
    assert console_errors(driver) == []


def test_language_switch_goes_to_english_and_back(driver, wait):
    driver.get(BASE + "/")
    driver.find_element(By.CSS_SELECTOR, '.lang a[hreflang="en"]').click()
    wait(driver).until(EC.url_contains("/en/"))
    assert driver.find_element(By.TAG_NAME, "html").get_attribute("lang") == "en"
    assert "Shopify" in driver.find_element(By.TAG_NAME, "h1").text
    driver.find_element(By.CSS_SELECTOR, '.lang a[hreflang="sr"]').click()
    wait(driver).until(lambda d: d.find_element(By.TAG_NAME, "html").get_attribute("lang") == "sr")


def test_contact_links_are_clickable(driver):
    driver.get(BASE + "/")
    hrefs = [a.get_attribute("href") for a in driver.find_elements(By.CSS_SELECTOR, "#kontakt a")]
    assert any(h.startswith("mailto:") for h in hrefs)
    assert any(h.startswith("tel:+381") for h in hrefs)
    assert any("wa.me/" in h for h in hrefs)
    assert any(h.startswith("viber://") for h in hrefs)


def test_portfolio_links_open_in_new_tab(driver):
    driver.get(BASE + "/")
    links = driver.find_elements(By.CSS_SELECTOR, "#radovi .case a")
    assert len(links) == 4
    for a in links:
        assert a.get_attribute("href").startswith("https://")
        assert a.get_attribute("target") == "_blank"
        assert "noopener" in a.get_attribute("rel")


def test_copy_button_gives_feedback(driver, wait):
    driver.get(BASE + "/")
    button = driver.find_element(By.ID, "b0")
    before = button.text
    driver.execute_script("arguments[0].scrollIntoView({block:'center', behavior:'instant'})", button)
    button.click()
    # Clipboard can be blocked in headless mode; then the text is selected instead.
    wait(driver, 3).until(lambda d: button.text != before or d.execute_script("return getSelection().toString()"))


@pytest.mark.mobile
@pytest.mark.parametrize("path", ["/", "/en/"])
def test_no_horizontal_scroll_on_phone(phone, path):
    phone.get(BASE + path)
    assert not has_horizontal_scroll(phone)


def test_sitemap_and_robots(driver):
    driver.get(BASE + "/sitemap.xml")
    assert "/en/" in driver.page_source
    driver.get(BASE + "/robots.txt")
    assert "Sitemap:" in driver.find_element(By.TAG_NAME, "body").text
