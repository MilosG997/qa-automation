"""Tan Ti Studio (salon website): navigation, sections and phone layout."""
import os

import pytest
from selenium.webdriver.common.by import By

from helpers import has_horizontal_scroll, meta

BASE = os.environ.get("TT_URL", "https://tantistudio.netlify.app").rstrip("/")


def test_home_loads_with_title(driver):
    driver.get(BASE + "/")
    assert "Tan Ti Studio" in driver.title
    assert driver.find_element(By.TAG_NAME, "h1").text.strip()
    assert meta(driver, 'meta[name="description"]')


def test_menu_links_point_to_sections_on_page(driver):
    driver.get(BASE + "/")
    links = driver.find_elements(By.CSS_SELECTOR, "#nav a[href*='#']")
    assert links, "main menu should have in-page links"
    for a in links:
        target = a.get_attribute("href").split("#", 1)[1]
        if target:
            assert driver.find_elements(By.ID, target), f"section #{target} is missing"


@pytest.mark.mobile
def test_no_horizontal_scroll_on_phone(phone):
    phone.get(BASE + "/")
    assert not has_horizontal_scroll(phone)
