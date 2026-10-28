"""Shared fixtures: one browser per test, desktop or phone-sized, Chrome or Edge.

Options:
    pytest --browser edge      run in Microsoft Edge instead of Chrome
    pytest --headed            show the browser window (default is headless)
"""
import os
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

SCREENSHOTS = Path(__file__).parent.parent / "screenshots"


def pytest_addoption(parser):
    parser.addoption("--browser", default="chrome", choices=["chrome", "edge"])
    parser.addoption("--headed", action="store_true", help="show the browser window")


def _make_driver(config, width, height, mobile=False):
    name = config.getoption("--browser")
    options = webdriver.EdgeOptions() if name == "edge" else webdriver.ChromeOptions()
    if not config.getoption("--headed"):
        options.add_argument("--headless=new")
    options.add_argument(f"--window-size={width},{height}")
    options.add_argument("--lang=en-US")
    if mobile:
        options.add_experimental_option("mobileEmulation", {
            "deviceMetrics": {"width": width, "height": height, "pixelRatio": 2},
            "userAgent": ("Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/130.0 Mobile Safari/537.36"),
        })
    driver = webdriver.Edge(options=options) if name == "edge" else webdriver.Chrome(options=options)
    driver.set_page_load_timeout(45)
    return driver


@pytest.fixture
def driver(request):
    d = _make_driver(request.config, 1366, 900)
    yield d
    _screenshot_on_failure(request, d)
    d.quit()


@pytest.fixture
def phone(request):
    """A 375px-wide phone (iPhone SE / small Android size)."""
    d = _make_driver(request.config, 375, 812, mobile=True)
    yield d
    _screenshot_on_failure(request, d)
    d.quit()


@pytest.fixture
def wait():
    def _wait(driver, seconds=15):
        return WebDriverWait(driver, seconds)
    return _wait


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


def pytest_terminal_summary(terminalreporter, exitstatus):
    """On GitHub Actions, show every failure and error (setup, test, teardown or collection) as an annotation on the
    run page, so the reason is visible without opening the log."""
    if not os.environ.get("GITHUB_ACTIONS"):
        return
    counts = {k: len(terminalreporter.stats.get(k, [])) for k in ("passed", "failed", "error", "skipped", "xfailed", "rerun")}
    terminalreporter.write_line("::notice title=Results::" + ", ".join(f"{n} {k}" for k, n in counts.items() if n))
    shown = 0
    for kind in ("failed", "error"):
        for report in terminalreporter.stats.get(kind, []):
            lines = str(getattr(report, "longrepr", "") or kind).strip().splitlines()
            where = f'{getattr(report, "when", "collect")}: {getattr(report, "nodeid", "") or "collection"}'
            terminalreporter.write_line(f"::error title={kind} in {where}::{lines[-1][:300] if lines else kind}")
            shown += 1
    if exitstatus and not shown:
        terminalreporter.write_line(f"::error title=pytest exit status {int(exitstatus)}::no test failed, see the log")


def _screenshot_on_failure(request, driver):
    rep = getattr(request.node, "rep_call", None)
    if rep is not None and rep.failed:
        SCREENSHOTS.mkdir(exist_ok=True)
        driver.save_screenshot(str(SCREENSHOTS / f"{request.node.name}.png"))
