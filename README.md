# QA automation: Selenium + pytest

[![tests](https://github.com/MilosG997/qa-automation/actions/workflows/tests.yml/badge.svg)](https://github.com/MilosG997/qa-automation/actions/workflows/tests.yml)

End-to-end tests for a live Shopify store and three websites I built. The tests open a real browser, click through the site like a visitor and check what a customer (and Google) would see, on desktop and on a 375px phone.

| Test file | Site | What it checks |
|---|---|---|
| [`test_shopify_store.py`](tests/test_shopify_store.py) | [Eskay Products](https://eskayproducts.com) (Shopify) | Search, collection page, product page with price and *Add to cart* form, `/products.json`, phone layout. Read-only: nothing is bought. |
| [`test_mechanicallygifted.py`](tests/test_mechanicallygifted.py) | [mechanicallygifted.rs](https://mechanicallygifted.rs) | Title, meta description length, one H1, canonical, hreflang, Open Graph, SR/EN switch, contact links (mail, phone, Viber, WhatsApp), portfolio links, copy button, sitemap, robots, no JS errors. |
| [`test_majstori_pazova.py`](tests/test_majstori_pazova.py) | [majstoripazova.rs](https://majstoripazova.rs) (web + Android app) | Categories load from the database, opening a category, search field, privacy policy, phone layout. |
| [`test_tan_ti_studio.py`](tests/test_tan_ti_studio.py) | [Tan Ti Studio](https://tantistudio.netlify.app) | Title and description, menu links point to real sections, phone layout. |

A real bug this suite caught: the English meta description on my own site was 171 characters, over the ~160–170 that Google shows. Shortened and re-tested.

## Run it

```bash
pip install -r requirements.txt
pytest                      # headless Chrome
pytest --headed             # watch the browser
pytest --browser edge       # Microsoft Edge
pytest -m shopify           # only the Shopify store
pytest -m mobile            # only phone-size tests
```

Point a test file at another environment (for example a staging theme) with an environment variable:

```bash
SHOP_URL=https://your-store.myshopify.com pytest -m shopify
MG_URL=http://localhost:5520 pytest tests/test_mechanicallygifted.py
```

## How it is built

- **pytest fixtures** in [`conftest.py`](tests/conftest.py): a fresh browser per test, a `phone` fixture with Chrome mobile emulation (375 × 812), `--browser` and `--headed` options.
- **Explicit waits** (`WebDriverWait` + expected conditions) instead of `sleep`, so tests are fast and stable on slow pages.
- **Screenshot on failure**: a failed test saves `screenshots/<test-name>.png`; in CI it is uploaded as an artifact.
- **GitHub Actions** runs the whole suite on every push.
- Selenium Manager downloads the right driver automatically, no manual chromedriver.

---

By [Mechanically Gifted](https://mechanicallygifted.rs) · Shopify development, websites and QA automation.
