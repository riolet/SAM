"""
This file is for:
- Establishing a robot browser to test with
- Populating the demo database with data
- Starting a webserver to host the site, using the demo database
"""
import traceback
import pytest
from selenium import webdriver

browser_driver = None
host = "http://localhost:8080/"

def get_browser():
    global browser_driver
    if browser_driver:
        return browser_driver

    try:
        browser_driver = webdriver.Firefox()
        print("Creating new browser {}".format(id(browser_driver)))
    except:
        print("Cannot load Firefox. Did you install the gecko webdriver?")
        traceback.print_exc()

    return browser_driver

# scope = "module", "function", "session"
@pytest.fixture(scope="session")
def browser():
    global browser_driver
    browser_driver = get_browser()
    yield browser_driver
    print("closing browser {}".format(id(browser_driver)))
    browser_driver.close()
    browser_driver = None