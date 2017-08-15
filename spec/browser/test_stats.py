import pytest
from sam import constants
from spec.browser import conftest
from sam.local import en as strings


def at_stats_page(browser):
    return browser.current_url.endswith("/stats")


def ensure_stats_page(browser):
    if not at_stats_page(browser):
        browser.get(conftest.host + "stats")


def test_navbar(browser):
    ensure_stats_page(browser)
    assert at_stats_page(browser)


def test_footer_language_links(browser):
    ensure_stats_page(browser)
    assert at_stats_page(browser)
