"""
This file is for:
- Establishing a robot browser to test with
- Populating the demo database with data
- Starting a webserver to host the site, using the demo database
"""
import os
import signal
import traceback
import pytest
from multiprocessing import process
from sam import launcher
from selenium import webdriver

browser_driver = None
host = "http://localhost:8080/"
webserver_process = None


def get_browser():
    global browser_driver
    if browser_driver:
        return browser_driver
    try:
        browser_driver = webdriver.Firefox()
    except:
        print("Cannot load Firefox. Did you install the gecko webdriver?")
        traceback.print_exc()

    return browser_driver


def start_test_webserver():
    global webserver_process
    argv = "--port=8080 --target=webserver"
    environment = {
        'SAM__ACCESS_CONTROL__ACTIVE': 'TRUE',
        'SAM__ACCESS_CONTROL__LOCAL_TLS': 'True',
        'SAM__DATABASE__PW': 'bitnami'
    }
    launch_args = (environment, argv)
    webserver_process = process.Process(target=launcher.testing_entrypoint, args=launch_args)
    webserver_process.start()


def stop_test_webserver():
    global webserver_process
    os.kill(webserver_process.pid, signal.SIGINT)
    webserver_process.join()


# scope = "module", "function", "session"
@pytest.fixture(scope="session")
def browser():
    # Setup code
    global browser_driver
    start_test_webserver()
    browser_driver = get_browser()

    # Run the tests with this instance of the browser
    yield browser_driver

    # Teardown code
    browser_driver.close()
    browser_driver = None
    stop_test_webserver()


def get_path(browser):
    path = browser.current_url
    path = path[len(host):]
    path = path.lstrip("/")
    return path