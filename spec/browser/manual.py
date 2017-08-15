from selenium import webdriver
browser = webdriver.Firefox()
host = "http://localhost:8080/"
browser.get(host + "stats")