"""Small checks reused across sites."""
import json


def has_horizontal_scroll(driver):
    return driver.execute_script(
        "return document.documentElement.scrollWidth > window.innerWidth + 1")


def console_errors(driver):
    """Severe JS errors (Chrome only; Edge returns the same log format)."""
    try:
        logs = driver.get_log("browser")
    except Exception:  # some drivers do not expose logs
        return []
    return [l["message"] for l in logs if l.get("level") == "SEVERE" and "favicon" not in l["message"]]


def meta(driver, selector, attr="content"):
    els = driver.find_elements("css selector", selector)
    return els[0].get_attribute(attr) if els else None


def broken_images(driver):
    """Load every image (also lazy ones in closed panels), then list images that failed or have no alt."""
    driver.execute_script("""
        document.querySelectorAll('img[loading=lazy]').forEach(i => i.loading = 'eager');
        return new Promise(done => { let y = 0; const step = () => { window.scrollTo(0, y += 700);
          y < document.body.scrollHeight ? setTimeout(step, 60) : setTimeout(done, 1500); }; step(); });""")
    return driver.execute_script("""
        return [...document.images].filter(i => i.getAttribute('src'))
          .filter(i => !i.complete || i.naturalWidth === 0 || !i.hasAttribute('alt'))
          .map(i => i.currentSrc || i.src)""")


def anchors_without_target(driver, selector="a[href^='#']"):
    """In-page links (#id) whose target element does not exist."""
    return driver.execute_script(
        "return [...document.querySelectorAll(arguments[0])].map(a => a.getAttribute('href'))"
        ".filter(h => h.length > 1 && !document.getElementById(decodeURIComponent(h.slice(1))))", selector)


def json_ld(driver):
    return [json.loads(s.get_attribute("textContent")) for s in
            driver.find_elements("css selector", 'script[type="application/ld+json"]')]
