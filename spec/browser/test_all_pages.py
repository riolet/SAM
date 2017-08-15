# coding=utf-8
from sam import constants
from spec.browser import conftest
from sam.local import en as strings


def at_stats_page(browser):
    return browser.current_url.endswith("/stats")


def ensure_stats_page(browser):
    if not at_stats_page(browser):
        browser.get(conftest.host + "stats")


def test_home_page(browser):
    browser.get(conftest.host)
    assert browser.title == strings.map_title


def test_navbar_pages(browser):
    urls = constants.get_navbar('en')
    for addr in urls:
        browser.get(conftest.host + addr['link'])
        assert browser.title == addr['name']


def test_languages(browser):
    for lang in constants.supported_languages:
        urls = constants.get_navbar(lang)
        for addr in urls:
            url = "{}{}{}".format(conftest.host, lang, addr['link'][1:])
            browser.get(url)
            assert browser.title == addr['name']


def test_navbar(browser):
    # Starting state
    browser.get(conftest.host + "en/stats")
    assert at_stats_page(browser)

    # Home page button
    DOM_logo_link= browser.find_element_by_id("link_home")
    DOM_logo_link.click()
    assert browser.title == strings.map_title

    # Nav links
    navbar = constants.get_navbar('en')
    for i in range(len(navbar)):
        DOM_navbar = browser.find_element_by_id("navbar")
        DOM_links = DOM_navbar.find_elements_by_class_name("navlink")
        DOM_links[i].click()
        assert browser.title == navbar[i]['name']

    # TODO: Login link (if present)

    # language link
    DOM_navbar = browser.find_element_by_id("navbar")
    DOM_lang = DOM_navbar.find_element_by_class_name("langlink")
    # We should be in english at this point still
    assert DOM_lang.text == u'version française'
    old_path = conftest.get_path(browser)
    if old_path[0:2] in constants.supported_languages:
        old_path = old_path[3:]
    DOM_lang.click()

    DOM_navbar = browser.find_element_by_id("navbar")
    DOM_lang = DOM_navbar.find_element_by_class_name("langlink")
    path = conftest.get_path(browser)
    assert path == "fr/" + old_path
    assert DOM_lang.text == u'English version'
    DOM_lang.click()

    DOM_navbar = browser.find_element_by_id("navbar")
    DOM_lang = DOM_navbar.find_element_by_class_name("langlink")
    path = conftest.get_path(browser)
    assert path == "en/" + old_path
    assert DOM_lang.text == u'version française'



def test_footer_language_links(browser):
    # Starting state
    browser.get(conftest.host + "en/stats")
    assert at_stats_page(browser)

    # Testing footer language links
    DOM_footer = browser.find_element_by_id("footer")
    DOM_lang = DOM_footer.find_element_by_partial_link_text("rançais")
    old_path = conftest.get_path(browser)
    if old_path[0:2] in constants.supported_languages:
        old_path = old_path[3:]
    DOM_lang.click()

    DOM_footer = browser.find_element_by_id("footer")
    DOM_lang = DOM_footer.find_element_by_partial_link_text("nglish")
    path = conftest.get_path(browser)
    assert path == "fr/" + old_path
    DOM_lang.click()

    path = conftest.get_path(browser)
    assert path == "en/" + old_path
