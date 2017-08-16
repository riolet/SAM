from spec.python import db_connection
from spec.browser import conftest
browser = conftest.get_browser()
host = "http://localhost:8080/"
browser.get(host + "settings_page")