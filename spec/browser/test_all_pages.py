from sam import constants
from spec.browser import conftest
from sam.local import en as strings


def test_home_page(browser):
    browser.get(conftest.host)
    assert browser.title == strings.map_title


def test_navbar_pages(browser):
    browser.get(conftest.host)
    urls = constants.get_navbar('en')
    for addr in urls:
        browser.get(conftest.host + addr['link'])
        assert browser.title == addr['name']
