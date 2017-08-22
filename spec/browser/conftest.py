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
import multiprocessing
import time
import requests
from spec.python import db_connection
from sam import launcher
from selenium import webdriver


driver = webdriver.Firefox
# driver = webdriver.Chrome
_browser_ = None
port = "8888"
host = "http://localhost:{}/".format(port)
webserver_process = None

db = db_connection.db
sub_id = db_connection.default_sub
ds = db_connection.dsid_default
ds_live = db_connection.dsid_live
ds_short = db_connection.dsid_short


def get_browser():
    global _browser_, driver
    if _browser_:
        return _browser_
    try:
        _browser_ = driver()
    except:
        print("Cannot load Firefox. Did you install the gecko webdriver?")
        traceback.print_exc()

    return _browser_


def start_test_webserver():
    global webserver_process
    argv = ["test_invocation", "--port={}".format(port), "--target=webserver"]
    environment = {
        'SAM__ACCESS_CONTROL__ACTIVE': 'FALSE',
        'SAM__DATABASE__DB': db_connection.TEST_DATABASE_MYSQL
    }
    launch_args = (environment, argv)
    webserver_process = multiprocessing.Process(target=launcher.testing_entrypoint, args=launch_args)
    webserver_process.start()


def wait_for_webserver_ready(max_seconds):
    giveup_time = time.time() + max_seconds
    response_code = 0
    while response_code != 200 and time.time() < giveup_time:
        msg = "pinging webserver..."
        try:
            response = requests.request("GET", host + "stats?q=1")
            response_code = response.status_code
            msg += "response code: {}".format(response_code)
        except:
            msg += "silence"
        time.sleep(0.25)
        print(msg)


def stop_test_webserver():
    global webserver_process
    os.kill(webserver_process.pid, signal.SIGINT)
    webserver_process.join()


# scope = "module", "function", "session"
@pytest.fixture(scope="session")
def browser():
    # Setup code
    global _browser_
    start_test_webserver()
    wait_for_webserver_ready(3)
    _browser_ = get_browser()

    # Run the tests with this instance of the browser
    yield _browser_

    # Teardown code
    _browser_.close()
    _browser_ = None
    stop_test_webserver()


def get_path(browser):
    path = browser.current_url
    path = path[len(host):]
    path = path.lstrip("/")
    return path


def modal_is_visible(modal):
    classes = modal.get_attribute("class").split()

    # wait until finished animating
    max_wait = time.time() + 5
    while "animating" in classes and time.time() < max_wait:
        time.sleep(0.3)
        classes = modal.get_attribute("class").split()

    return "visible" in classes and \
           "active" in classes and \
           "hidden" not in classes

def get_semantic_dropdown_data(dropdown):
    items = dropdown.find_elements_by_class_name("item")
    # Use .get_property("innerText") here instead of .text because the item is hidden
    data_values = [(item.get_attribute("data-value"), item.get_property("innerText")) for item in items]
    return data_values