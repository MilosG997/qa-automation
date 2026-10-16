"""Majstori Pazova (web app + Android app): home screen, categories, search, privacy page."""
import os

import pytest
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
