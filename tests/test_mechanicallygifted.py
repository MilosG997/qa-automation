"""Mechanically Gifted (my own site): SEO, language switch, contact, portfolio, About, Google reviews, mobile, HTTP."""
import os

import pytest
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC

from helpers import anchors_without_target, broken_images, console_errors, has_horizontal_scroll, json_ld, meta

BASE = os.environ.get("MG_URL", "https://mechanicallygifted.rs").rstrip("/")
PAGES = [("/", "sr"), ("/en/", "en")]


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
    links = driver.find_elements(By.CSS_SELECTOR, "#radovi .folders .item a")
    assert len(links) >= 5
    for a in links:
        assert a.get_attribute("href").startswith("https://")
        assert a.get_attribute("target") == "_blank"
        assert "noopener" in a.get_attribute("rel")


@pytest.mark.parametrize("path", ["/", "/en/"])
def test_portfolio_folders_open_one_at_a_time(driver, wait, path):
    """Folders start closed; opening one shows its items and closes the others; badge = number of items."""
    driver.get(BASE + path)
    folders = driver.find_elements(By.CSS_SELECTOR, "#radovi .folders .f")
    assert len(folders) == 4
    heads = [f.find_element(By.CSS_SELECTOR, ".head") for f in folders]
    assert all(h.get_attribute("aria-expanded") == "false" for h in heads)
    for folder, head in zip(folders, heads):
        driver.execute_script("arguments[0].click()", head)
        items = folder.find_elements(By.CSS_SELECTOR, ".item")
        wait(driver, 5).until(lambda d: all(i.is_displayed() for i in items))
        assert int(folder.find_element(By.CSS_SELECTOR, ".cnt").text) == len(items)
        assert [h.get_attribute("aria-expanded") for h in heads].count("true") == 1


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


ABOUT = {"sr": ("Zdravo, ja sam Miloš", "Upoznaj čoveka iza Mechanically Gifted"),
         "en": ("Hi, I'm Miloš", "Meet the person behind Mechanically Gifted")}


@pytest.mark.parametrize("path,lang", PAGES)
def test_about_card_opens_and_closes(driver, wait, path, lang):
    """About starts closed (content inert, not focusable); a click opens it, a second click closes it."""
    driver.get(BASE + path)
    button, body = driver.find_element(By.ID, "abBtn"), driver.find_element(By.ID, "abBody")
    title, lead = ABOUT[lang]
    assert title in button.get_attribute("textContent")
    assert button.get_attribute("aria-expanded") == "false"
    assert driver.execute_script("return arguments[0].inert", body)
    driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click()", button)
    wait(driver, 5).until(lambda d: button.get_attribute("aria-expanded") == "true")
    assert not driver.execute_script("return arguments[0].inert", body)
    wait(driver, 5).until(lambda d: lead in body.text)
    assert len(body.find_elements(By.CSS_SELECTOR, ".tools h4")) == 3
    driver.execute_script("arguments[0].click()", button)
    wait(driver, 5).until(lambda d: button.get_attribute("aria-expanded") == "false")


@pytest.mark.parametrize("path", ["/", "/en/"])
def test_about_photo_loads(driver, path):
    driver.get(BASE + path)
    img = driver.find_element(By.CSS_SELECTOR, "#omeni .pic img")
    driver.execute_script("arguments[0].scrollIntoView({block:'center'})", img)
    assert driver.execute_script("return arguments[0].decode().then(() => arguments[0].naturalWidth)", img) > 0


def _open_reviews(driver, wait):
    section = driver.find_element(By.ID, "recenzije")
    driver.execute_script("arguments[0].scrollIntoView({block:'start'})", section)
    wait(driver, 15).until(lambda d: d.find_elements(By.CSS_SELECTOR, "#recenzije .rev-card"))
    return section


@pytest.mark.parametrize("path", ["/", "/en/"])
def test_reviews_show_up_to_five_cards_with_stars(driver, wait, path):
    driver.get(BASE + path)
    section = _open_reviews(driver, wait)
    cards = section.find_elements(By.CSS_SELECTOR, ".rev-card")
    assert 1 <= len(cards) <= 5
    for card in cards:
        assert card.find_element(By.CSS_SELECTOR, ".rev-who b").get_attribute("textContent").strip()
        assert card.find_element(By.CSS_SELECTOR, ".rev-txt").get_attribute("textContent").strip()
        assert card.find_element(By.CSS_SELECTOR, ".rev-stars").get_attribute("aria-label")
    score = section.find_element(By.CSS_SELECTOR, ".rev-big").text
    assert 1 <= float(score.replace(",", ".")) <= 5
    leave = section.find_element(By.CSS_SELECTOR, ".rev-ostavi")
    assert leave.get_attribute("href").startswith("https://g.page/")
    assert leave.get_attribute("target") == "_blank"


def test_reviews_slide_by_themselves(driver, wait):
    driver.get(BASE + "/")
    section = _open_reviews(driver, wait)
    if section.find_element(By.CSS_SELECTOR, ".rev-nav").get_attribute("hidden") is not None:
        pytest.skip("all cards fit on screen, nothing to slide")
    track = section.find_element(By.CSS_SELECTOR, ".rev-track")
    start = driver.execute_script("return arguments[0].scrollLeft", track)
    wait(driver, 9).until(lambda d: d.execute_script("return arguments[0].scrollLeft", track) > start + 50)


def test_review_arrows_move_the_track(driver, wait):
    driver.get(BASE + "/")
    section = _open_reviews(driver, wait)
    track = section.find_element(By.CSS_SELECTOR, ".rev-track")
    driver.execute_script("arguments[0].scrollTo({left: 0, behavior: 'instant'})", track)
    driver.execute_script("arguments[0].click()", section.find_elements(By.CSS_SELECTOR, ".rev-arrows button")[1])
    wait(driver, 5).until(lambda d: d.execute_script("return arguments[0].scrollLeft", track) > 50)


@pytest.mark.parametrize("path", ["/", "/en/"])
def test_in_page_links_have_targets(driver, path):
    driver.get(BASE + path)
    assert anchors_without_target(driver) == []
    nav = [a.get_attribute("href").rsplit("#", 1)[1] for a in driver.find_elements(By.CSS_SELECTOR, "nav.links a")]
    assert nav == ["usluge", "omeni", "radovi", "pitanja", "kontakt"]


@pytest.mark.parametrize("path", ["/", "/en/"])
def test_all_images_load_and_have_alt(driver, path):
    driver.get(BASE + path)
    assert broken_images(driver) == []


@pytest.mark.parametrize("path", ["/", "/en/"])
def test_structured_data(driver, path):
    driver.get(BASE + path)
    blocks = json_ld(driver)
    assert blocks, "JSON-LD missing"
    text = str(blocks)
    assert "Mechanically Gifted" in text and "+381" in text
    assert "AggregateRating" not in text, "no self-served review markup (Google guideline)"


def test_web_design_lightbox(driver, wait):
    driver.get(BASE + "/")
    head = driver.find_elements(By.CSS_SELECTOR, "#radovi .folders .f .head")[2]
    driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click()", head)
    first = wait(driver, 5).until(lambda d: [b for b in d.find_elements(By.CSS_SELECTOR, ".folders [data-lb]")
                                             if b.is_displayed()])[0]
    driver.execute_script("arguments[0].click()", first)
    box = wait(driver, 5).until(lambda d: d.find_element(By.CSS_SELECTOR, ".lb.otvoren"))
    counter = box.find_element(By.CSS_SELECTOR, ".lb-broj")
    assert counter.text.startswith("1 / ")
    driver.execute_script("arguments[0].click()", box.find_element(By.CSS_SELECTOR, ".lb-sled"))
    assert counter.text.startswith("2 / ")
    driver.switch_to.active_element.send_keys(Keys.ESCAPE)
    wait(driver, 5).until(lambda d: not box.is_displayed())


@pytest.mark.mobile
@pytest.mark.parametrize("path", ["/", "/en/"])
def test_about_and_reviews_fit_the_phone(phone, wait, path):
    phone.get(BASE + path)
    button = phone.find_element(By.ID, "abBtn")
    phone.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click()", button)
    wait(phone, 5).until(lambda d: button.get_attribute("aria-expanded") == "true")
    _open_reviews(phone, wait)
    assert not has_horizontal_scroll(phone)
    assert phone.find_element(By.CSS_SELECTOR, ".rev-card").rect["width"] <= 375


# ---- HTTP level (requests, no browser): redirects, status codes, headers, the reviews function ----

@pytest.mark.parametrize("url", ["https://www.mechanicallygifted.rs/", "http://mechanicallygifted.rs/",
                                 "https://mechanicallygifted.netlify.app/"])
def test_alternate_hosts_redirect_to_the_main_domain(url):
    response = requests.get(url, allow_redirects=False, timeout=20)
    assert response.status_code == 301
    assert response.headers["Location"].startswith("https://mechanicallygifted.rs/")


@pytest.mark.parametrize("path", ["/nema-ove-strane", "/en/no-such-page"])
def test_unknown_pages_return_404(path):
    response = requests.get(BASE + path, timeout=20)
    assert response.status_code == 404
    assert "Mechanically Gifted" in response.text


@pytest.mark.parametrize("path", ["/privatnost/", "/en/privacy/", "/sitemap.xml", "/robots.txt", "/site.webmanifest"])
def test_support_pages_are_served(path):
    assert requests.get(BASE + path, timeout=20).status_code == 200


def test_security_headers():
    headers = requests.get(BASE + "/", timeout=20).headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert "max-age" in headers.get("Strict-Transport-Security", "")
    assert headers.get("Referrer-Policy")


def test_reviews_function_returns_json():
    response = requests.get(BASE + "/.netlify/functions/reviews?lang=en", timeout=20)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["reviews"], list) and len(data["reviews"]) <= 5
