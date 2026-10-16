"""Small checks reused across sites."""


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
