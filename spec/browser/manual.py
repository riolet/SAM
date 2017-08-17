python
from spec.python import db_connection
from spec.browser import conftest
import time, operator
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from sam.models.datasources import Datasources
browser = conftest.get_browser()
host = "http://localhost:8080/"
browser.get(host + "metadata")
