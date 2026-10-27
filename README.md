# QA automation: Selenium + pytest

[![tests](https://github.com/MilosG997/qa-automation/actions/workflows/tests.yml/badge.svg)](https://github.com/MilosG997/qa-automation/actions/workflows/tests.yml)

End-to-end tests for a live Shopify store and three websites I built. The tests open a real browser, click through the site like a visitor and check what a customer (and Google) would see, on desktop and on a 375px phone. A second layer uses `requests` for what a browser hides: redirects, status codes, security headers and API responses.

**136 tests** across 4 live sites.

| Test file | Site | What it checks |
|---|---|---|
| [`test_shopify_store.py`](tests/test_shopify_store.py) | [Eskay Products](https://eskayproducts.com) (Shopify) | Search, collection page, product page with price and *Add to cart* form, `/products.json`, phone layout. Read-only: nothing is bought. |
| [`test_mechanicallygifted.py`](tests/test_mechanicallygifted.py) | [mechanicallygifted.rs](https://mechanicallygifted.rs) | SEO (title, description, one H1, canonical, hreflang, Open Graph, JSON-LD), SR/EN switch, contact links, portfolio folders and the design lightbox, the *About* card (opens, closes, inert when closed), Google review cards and their auto-slider, every image loads and has alt text, no dead in-page links, phone layout, redirects, 404 pages, security headers, the reviews serverless function. |
| [`test_draganic_stolarija.py`](tests/test_draganic_stolarija.py) | [draganicstolarija.rs](https://draganicstolarija.rs) (local window installer) | SEO on all 14 pages from the sitemap (one H1, self canonical, unique titles and descriptions), LocalBusiness structured data, every call / Viber / WhatsApp button dials the same number, photo gallery filters match their counters, lightbox with the keyboard, phone layout and tap target size, redirects, 404, security headers. |
| [`test_http_seo.py`](tests/test_http_seo.py) | Draganić Stolarija + mechanicallygifted.rs | What crawlers and link previews read from the raw HTML, page by page: language, Open Graph and share images, robots, hreflang pairs that point back to each other, every local asset served, sitemap alternates, `noindex` on 404 pages. |
| [`test_majstori_pazova.py`](tests/test_majstori_pazova.py) | [majstoripazova.rs](https://majstoripazova.rs) (web + Android app) | Categories load from the database, opening a category, search, privacy policy, phone layout, Android app links (`assetlinks.json`), installable web app manifest, redirects, sitemap, 404. |

A real bug this suite caught: the English meta description on my own site was 171 characters, over the ~160–170 that Google shows. Shortened and re-tested.

## Run it

```bash
pip install -r requirements.txt
pytest                      # headless Chrome
pytest --headed             # watch the browser
pytest -n auto              # in parallel (pytest-xdist)
pytest --browser edge       # Microsoft Edge
pytest -m shopify           # only the Shopify store
pytest -m mobile            # only phone-size tests
```

Point a test file at another environment (for example a staging theme) with an environment variable:

```bash
SHOP_URL=https://your-store.myshopify.com pytest -m shopify
MG_URL=http://localhost:5520 pytest tests/test_mechanicallygifted.py
DS_URL=http://localhost:5530 pytest tests/test_draganic_stolarija.py
```

## How it is built

- **pytest fixtures** in [`conftest.py`](tests/conftest.py): a fresh browser per test, a `phone` fixture with Chrome mobile emulation (375 × 812), `--browser` and `--headed` options.
- **Two layers**: Selenium for what a visitor sees, `requests` for HTTP behaviour (301s, 404s, headers, JSON).
- **Shared checks** in [`helpers.py`](tests/helpers.py): broken or alt-less images (lazy ones forced to load), in-page links without a target, JSON-LD parsing, horizontal scroll on phones.
- **Explicit waits** (`WebDriverWait` + expected conditions) instead of `sleep`, so tests are fast and stable on slow pages.
- **Screenshot on failure**: a failed test saves `screenshots/<test-name>.png`; in CI it is uploaded as an artifact.
- **GitHub Actions** runs the whole suite in parallel on every push and every Monday morning, so a change on a live site is caught within a week.
- Selenium Manager downloads the right driver automatically, no manual chromedriver.

---

By [Mechanically Gifted](https://mechanicallygifted.rs) · Shopify development, websites and QA automation.
