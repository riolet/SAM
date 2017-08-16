from spec.python import db_connection
from spec.browser import conftest
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from sam.models.datasources import Datasources
browser = conftest.get_browser()
host = "http://localhost:8080/"
browser.get(host + "settings_page")

DATABASE_TIME = 0.7  # seconds to allow for transactions
ds_model = Datasources(conftest.db, {}, conftest.sub_id)
pages = browser.find_element_by_id("ds_tab_contents")
active_pages = pages.find_elements_by_css_selector(".segment.active")
assert len(active_pages) == 1
page = active_pages[0]
dsid = page.get_attribute("data-tab")
dsid = int(dsid[2:])
