"""Majstori Pazova (web app + Android app): home screen, categories, search, privacy, app links, manifest."""
import os
import re

import pytest
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from helpers import has_horizontal_scroll

BASE = os.environ.get("MP_URL", "https://majstoripazova.rs").rstrip("/")
HOME_TEXT = "Koji majstor ti treba?"


def test_home_shows_categories(driver, wait):
    driver.get(BASE + "/")
    assert "Majstori Pazova" in driver.title
    wait(driver).until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), HOME_TEXT))
    body = driver.find_element(By.TAG_NAME, "body").text
    for category in ["Struja", "Voda", "Keramika"]:
        assert category in body


def test_category_opens_list_of_tradespeople(driver, wait):
    driver.get(BASE + "/")
    wait(driver).until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), HOME_TEXT))
    card = driver.find_element(By.XPATH, "//*[normalize-space(text())='Struja']")
    driver.execute_script("arguments[0].click()", card)
    wait(driver).until(EC.url_contains("#/k/"))


def test_search_field_accepts_text(driver, wait):
    driver.get(BASE + "/")
    field = wait(driver).until(EC.element_to_be_clickable((By.ID, "pretragaMajstora")))
    field.send_keys("bojler")
    assert field.get_attribute("value") == "bojler"


def test_privacy_policy_page(driver):
    driver.get(BASE + "/privatnost.html")
    assert driver.find_element(By.TAG_NAME, "h1").text.strip()
    assert "Google Analytics" in driver.page_source


@pytest.mark.mobile
def test_no_horizontal_scroll_on_phone(phone, wait):
    phone.get(BASE + "/")
    wait(phone).until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), HOME_TEXT))
    assert not has_horizontal_scroll(phone)


def test_search_field_with_empty_category_list_shows_feedback(driver, wait):
    """Searching for something nobody offers must not leave a blank screen."""
    driver.get(BASE + "/")
    field = wait(driver).until(EC.element_to_be_clickable((By.ID, "pretragaMajstora")))
    field.send_keys("zzzz-nema-takvog-majstora")
    wait(driver).until(lambda d: d.find_element(By.TAG_NAME, "body").text.strip())
    assert not has_horizontal_scroll(driver)


# ---- HTTP level (requests): what the Android app and Google need ----

def test_android_app_links_are_verified():
    """assetlinks.json lets the Google Play app open the site full screen (Trusted Web Activity)."""
    response = requests.get(BASE + "/.well-known/assetlinks.json", timeout=20)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/json")
    target = response.json()[0]["target"]
    assert target["namespace"] == "android_app"
    assert target["package_name"] == "rs.majstoripazova.app"
    assert all(len(f.split(":")) == 32 for f in target["sha256_cert_fingerprints"])


def test_web_app_manifest_is_installable():
    manifest = requests.get(BASE + "/manifest.webmanifest", timeout=20).json()
    assert manifest["name"] and manifest["start_url"] == "/"
    assert manifest["display"] == "standalone"
    sizes = {icon.get("sizes") for icon in manifest["icons"]}
    assert {"192x192", "512x512"} <= sizes


@pytest.mark.parametrize("url", ["https://www.majstoripazova.rs/", "http://majstoripazova.rs/"])
def test_alternate_hosts_redirect_to_the_main_domain(url):
    response = requests.get(url, allow_redirects=False, timeout=20)
    assert response.status_code == 301
    assert response.headers["Location"] == "https://majstoripazova.rs/"


def test_sitemap_pages_are_reachable():
    xml = requests.get(BASE + "/sitemap.xml", timeout=20).text
    urls = re.findall(r"<loc>([^<]+)</loc>", xml)
    assert BASE + "/" in urls
    assert all(requests.get(u, timeout=20).status_code == 200 for u in urls)
    assert "Sitemap: " + BASE + "/sitemap.xml" in requests.get(BASE + "/robots.txt", timeout=20).text


def test_unknown_page_returns_404():
    assert requests.get(BASE + "/nema-ove-strane", timeout=20).status_code == 404


def test_https_is_enforced_with_hsts():
    assert "max-age" in requests.get(BASE + "/", timeout=20).headers.get("Strict-Transport-Security", "")
