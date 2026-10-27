"""Draganić Stolarija (a site I designed, built and SEO-optimized for a local window installer).

Every page from the sitemap is checked for SEO basics, the work gallery is driven like a visitor would,
contact links must all dial the same number, and the HTTP layer (redirects, 404, headers) is verified too.
"""
import os
import re

import pytest
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from helpers import anchors_without_target, broken_images, console_errors, has_horizontal_scroll, json_ld, meta

BASE = os.environ.get("DS_URL", "https://draganicstolarija.rs").rstrip("/")
PHONE = "381641257573"
SERVICES = ["pvc-prozori", "alu-stolarija", "okapnice", "montaza-i-ugradnja", "popravka-prozora", "stolarija-po-meri"]
CITIES = ["stara-pazova", "nova-pazova", "beograd", "novi-sad"]
INNER_PAGES = ([f"/usluge/{s}/" for s in SERVICES] + [f"/pvc-stolarija-{c}/" for c in CITIES]
               + ["/usluge/", "/kontakt/", "/politika-privatnosti/"])


def test_home_page_seo(driver):
    driver.get(BASE + "/")
    assert driver.find_element(By.TAG_NAME, "html").get_attribute("lang") == "sr-Latn"
    assert "Draganić Stolarija" in driver.title and len(driver.title) <= 65
    assert len(driver.find_elements(By.TAG_NAME, "h1")) == 1
    description = meta(driver, 'meta[name="description"]')
    assert description and 50 <= len(description) <= 170
    assert meta(driver, 'link[rel="canonical"]', "href") == BASE + "/"
    assert meta(driver, 'meta[property="og:image"]').startswith("https://")
    assert console_errors(driver) == []


def test_local_business_structured_data(driver):
    driver.get(BASE + "/")
    nodes = [n for block in json_ld(driver) for n in block.get("@graph", [block])]
    business = next(n for n in nodes if n.get("@type") == "HomeAndConstructionBusiness")
    assert PHONE[3:] in re.sub(r"\D", "", business["telephone"])
    assert business["address"]["addressLocality"] == "Stara Pazova"
    assert len(business["areaServed"]) >= 4


@pytest.mark.parametrize("path", INNER_PAGES)
def test_inner_page_seo(driver, path):
    driver.get(BASE + path)
    assert len(driver.find_elements(By.TAG_NAME, "h1")) == 1, "exactly one h1"
    assert meta(driver, 'link[rel="canonical"]', "href") == BASE + path, "canonical points to itself"
    assert 30 <= len(meta(driver, 'meta[name="description"]') or "") <= 170
    assert "Draganić" in driver.title


def test_titles_and_descriptions_are_unique():
    """Duplicate titles make Google pick one page and drop the others."""
    titles, descriptions = {}, {}
    for path in ["/"] + INNER_PAGES:
        html = requests.get(BASE + path, timeout=20).text
        titles[path] = re.search(r"<title>(.*?)</title>", html).group(1)
        descriptions[path] = re.search(r'<meta name="description" content="([^"]*)"', html).group(1)
    assert len(set(titles.values())) == len(titles)
    assert len(set(descriptions.values())) == len(descriptions)


def test_contact_links_dial_the_same_number(driver):
    driver.get(BASE + "/")
    hrefs = {a.get_attribute("href") for a in driver.find_elements(By.CSS_SELECTOR, "a[href]")}
    assert f"tel:+{PHONE}" in hrefs
    assert f"https://wa.me/{PHONE}" in hrefs
    assert any(h.startswith("viber://chat?number=") and PHONE in h for h in hrefs)
    other_numbers = {h for h in hrefs if h.startswith("tel:") and PHONE not in h}
    assert not other_numbers, "every call button must use the same number"


def test_in_page_links_have_targets(driver):
    driver.get(BASE + "/")
    assert anchors_without_target(driver) == []


def test_all_images_load_and_have_alt(driver):
    driver.get(BASE + "/")
    assert broken_images(driver) == []


def _open_gallery(driver, wait):
    window = driver.find_element(By.CSS_SELECTOR, '[aria-controls="radovi-galerija"]')
    driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click()", window)
    wait(driver, 5).until(lambda d: window.get_attribute("aria-expanded") == "true")
    return driver.find_element(By.ID, "radovi-galerija")


def _visible_photos(gallery):
    return [li for li in gallery.find_elements(By.CSS_SELECTOR, ".slike li") if li.is_displayed()]


def test_gallery_window_opens(driver, wait):
    driver.get(BASE + "/")
    gallery = _open_gallery(driver, wait)
    assert gallery.is_displayed()
    assert len(_visible_photos(gallery)) >= 10


def test_gallery_filters_match_their_counters(driver, wait):
    driver.get(BASE + "/")
    gallery = _open_gallery(driver, wait)
    for button in gallery.find_elements(By.CSS_SELECTOR, ".filter"):
        driver.execute_script("arguments[0].click()", button)
        assert button.get_attribute("aria-pressed") == "true"
        expected = int(button.find_element(By.TAG_NAME, "span").text)
        wait(driver, 3).until(lambda d: len(_visible_photos(gallery)) == expected)
        kind = button.get_attribute("data-kat")
        if kind != "sve":
            assert all(li.get_attribute("data-kat") == kind for li in _visible_photos(gallery))


def test_gallery_lightbox_keyboard(driver, wait):
    driver.get(BASE + "/")
    gallery = _open_gallery(driver, wait)
    driver.execute_script("arguments[0].click()", _visible_photos(gallery)[0].find_element(By.TAG_NAME, "a"))
    box = wait(driver, 5).until(lambda d: [b for b in d.find_elements(By.CSS_SELECTOR, ".lb[role=dialog]")
                                           if b.is_displayed()])[0]
    caption = box.find_element(By.TAG_NAME, "p")
    assert "1 / " in caption.text
    driver.switch_to.active_element.send_keys(Keys.ARROW_RIGHT)
    assert "2 / " in caption.text
    image = box.find_element(By.TAG_NAME, "img")
    assert image.get_attribute("alt")
    driver.switch_to.active_element.send_keys(Keys.ESCAPE)
    wait(driver, 3).until(lambda d: not box.is_displayed())


def test_footer_credits_the_developer(driver):
    driver.get(BASE + "/")
    links = driver.find_elements(By.CSS_SELECTOR, 'footer a[href*="mechanicallygifted.rs"]')
    assert links and links[0].get_attribute("target") == "_blank"


@pytest.mark.mobile
@pytest.mark.parametrize("path", ["/", "/usluge/pvc-prozori/", "/kontakt/", "/pvc-stolarija-stara-pazova/"])
def test_phone_layout(phone, path):
    phone.get(BASE + path)
    assert not has_horizontal_scroll(phone)
    calls = [a for a in phone.find_elements(By.CSS_SELECTOR, f'a[href="tel:+{PHONE}"]') if a.is_displayed()]
    assert calls, "a visible call button on every page"


@pytest.mark.mobile
def test_phone_tap_targets_are_big_enough(phone):
    """Call / Viber / WhatsApp buttons must be at least ~44px tall to tap with a thumb.
    Plain text links inside a sentence or list are exempt (WCAG 2.5.8 inline exception)."""
    phone.get(BASE + "/")
    links = phone.find_elements(By.CSS_SELECTOR, "a[href^='tel:'], a[href^='viber:'], a[href*='wa.me/']")
    buttons = [a for a in links if a.is_displayed()
               and phone.execute_script("return getComputedStyle(arguments[0]).display", a) != "inline"]
    assert len(buttons) >= 3
    small = [(a.get_attribute("href"), a.rect["height"]) for a in buttons if a.rect["height"] < 40]
    assert small == []


# ---- HTTP level (requests, no browser) ----

def test_sitemap_lists_every_page():
    xml = requests.get(BASE + "/sitemap.xml", timeout=20).text
    listed = set(re.findall(r"<loc>([^<]+)</loc>", xml))
    assert {BASE + p for p in ["/"] + INNER_PAGES} <= listed
    for url in listed:
        assert requests.head(url, timeout=20).status_code == 200, url


def test_robots_points_to_the_sitemap():
    robots = requests.get(BASE + "/robots.txt", timeout=20).text
    assert f"Sitemap: {BASE}/sitemap.xml" in robots
    assert "Disallow: /\n" not in robots


@pytest.mark.parametrize("url", ["https://www.draganicstolarija.rs/", "http://draganicstolarija.rs/",
                                 "https://draganicstolarija.netlify.app/"])
def test_alternate_hosts_redirect_to_the_main_domain(url):
    response = requests.get(url, allow_redirects=False, timeout=20)
    assert response.status_code == 301
    assert response.headers["Location"] == "https://draganicstolarija.rs/"


def test_unknown_page_returns_404():
    assert requests.get(BASE + "/nema-ove-strane/", timeout=20).status_code == 404


def test_security_headers():
    headers = requests.get(BASE + "/", timeout=20).headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "SAMEORIGIN"
    assert "max-age" in headers["Strict-Transport-Security"]
    assert "camera=()" in headers["Permissions-Policy"]
