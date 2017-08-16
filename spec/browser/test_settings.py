"""
Tests:

[Data Sources]
  Clicking on the datasource name should switch datasources.
  New Data Source button should open a [modal window] to collect name
    Cancel should close modal without action
    Confirm should show validation error or perform [action]
      Datasource added to Data Source list
      Live Updates dropdown should include new datasource
      Upload Log dropdown should include new datasource
  X button should request confirmation via [modal window] to delete data source
    Cancel should close modal without action
    Confirm should remove datasource from list
  [Data Source]
    "Name" should be editable and save
    "Auto-refresh" should be editable and save
    "Auto-refresh interval" should be editable and save
    "Flat mode" should be editable and save
    "Delete Connections" should open a [modal]
      Cancel should close modal without action
      Confirm should perform action (delete link information)
    "Upload Log" should open [upload modal]
      Modal should allow file picking, no type filter
      Log Format dropdown should include all format options
      Data source dropdown should include all available datasources
      Cancel should close modal with no action
      Upload should perform [uploading action]
        If no file selected, nothing happens, modal stays open.
        On completion, a new modal indicates success/failure of upload
[Metadata]
  Should show a few hostnames currently stored in DB
  Should show a few tags currently stored in DB
  Should show a few envs currently stored in DB
  "Delete [*]" should open a modal to confirm action
    Cancel should close modal with no action
    Confirm should perform [action]
      hostnames, tags or envs deleted
      display updated to show results of action.
[Live Updates]
  Each live update key in the database should be displayed as a row
  dropdown should list all available datasources
  "Generate" should add a row to the DB and the UI table
    new row should include unique access key
    new row should have chosen destination (from dropdown list)
  X button should remove access key from UI table and from DB
"""
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from sam.models.datasources import Datasources
from spec.browser import conftest
# from sam.local import en as strings


def at_settings_page(browser):
    return browser.current_url.endswith("/settings_page")


def ensure_settings_page(func):
    def func_wrapper(browser, *args, **kwargs):
        if not at_settings_page(browser):
            browser.get(conftest.host + "settings_page")
        func(browser, *args, **kwargs)
    return func_wrapper


@ensure_settings_page
def xtest_switch_datasource(browser):
    """Clicking on the datasource name should switch datasources.
    :type browser: webdriver.Firefox
    """
    # determine currently active tab page:
    page = browser.find_element_by_id("ds_tab_contents")
    active_pages = page.find_elements_by_class_name("segment.active")
    assert len(active_pages) == 1
    initial_ds = active_pages[0].get_attribute("data-tab")

    # determine the current tab
    tablist = browser.find_element_by_id("ds_tabs")
    active_tabs = tablist.find_elements_by_class_name("item.active")
    assert len(active_tabs) == 1
    initial_tab = active_tabs[0].find_element_by_class_name("tablabel")
    assert initial_tab.get_attribute("data-tab") == initial_ds

    # find a different inactive tab
    tabs = tablist.find_elements_by_class_name("item")
    assert len(tabs) >= 2
    if tabs[0].find_element_by_class_name("tablabel") == initial_tab:
        other_tab_tr = tabs[1]
    else:
        other_tab_tr = tabs[0]
    other_tab = other_tab_tr.find_element_by_class_name("tablabel")
    other_ds = other_tab.get_attribute("data-tab")

    # click the inactive tab.
    other_tab.click()

    # check that tab has indeed switched
    active_pages = page.find_elements_by_class_name("segment.active")
    assert len(active_pages) == 1
    assert active_pages[0].get_attribute("data-tab") == other_ds
    active_tabs = tablist.find_elements_by_class_name("item.active")
    active_tab = active_tabs[0].find_element_by_class_name("tablabel")
    assert len(active_tabs) == 1
    assert active_tab.get_attribute("data-tab") == other_ds

    # switch back
    initial_tab.click()
    active_pages = page.find_elements_by_class_name("segment.active")
    assert len(active_pages) == 1
    assert active_pages[0].get_attribute("data-tab") == initial_ds
    active_tabs = tablist.find_elements_by_class_name("item.active")
    active_tab = active_tabs[0].find_element_by_class_name("tablabel")
    assert len(active_tabs) == 1
    assert active_tab.get_attribute("data-tab") == initial_ds


@ensure_settings_page
def xtest_create_delete_datasource(browser):
    """
      New Data Source button should open a [modal window] to collect name
        Cancel should close modal without action
        Confirm should show validation error or perform [action]
          Datasource added to Data Source list
          Live Updates dropdown should include new datasource
          Upload Log dropdown should include new datasource
      X button should request confirmation via [modal window] to delete data source
        Cancel should close modal without action
        Confirm should remove datasource from list
    :type browser: webdriver.Firefox
    """
    ds_model = Datasources(conftest.db, {}, conftest.sub_id)

    # determine existing dses in UI
    tablist = browser.find_element_by_id("ds_tabs")
    tabs = tablist.find_elements_by_class_name("item")
    UI_dses_init = [tab.find_element_by_class_name("tablabel").get_attribute("data-tab") for tab in tabs]
    # ["ds1", "ds2", "ds3"]
    # determine existing dses in DB
    DB_dses_init = ds_model.ds_ids  # [1,2,3]

    # add DS -- Cancel
    btnNewDataSource = browser.find_element_by_id("add_ds")
    btnNewDataSource.click()
    modal = browser.find_element_by_id("newDSModal")
    btnCancel = modal.find_element_by_class_name("cancel.button")
    btnConfirm = modal.find_element_by_class_name("ok.button")
    assert conftest.modal_is_visible(modal)
    btnCancel.click()
    assert not conftest.modal_is_visible(modal)

    # check UI dses unchanged
    tabs = tablist.find_elements_by_class_name("item")
    UI_dses = [tab.find_element_by_class_name("tablabel").get_attribute("data-tab") for tab in tabs]
    assert UI_dses == UI_dses_init
    # check DB dses unchanged
    ds_model.clear_cache()
    DB_dses = ds_model.ds_ids
    assert DB_dses == DB_dses_init

    # add DS -- Bad Name
    badName = "1"
    btnNewDataSource.click()
    assert conftest.modal_is_visible(modal)
    inputDSName = browser.find_element_by_id("newDSName")
    inputDSName.clear()
    inputDSName.send_keys(badName)
    btnConfirm.click()
    # check did not complete
    assert conftest.modal_is_visible(modal)

    # add DS -- Confirm
    goodName = "My New DS"
    inputDSName.clear()
    inputDSName.send_keys(goodName)
    btnConfirm.click()
    assert not conftest.modal_is_visible(modal)

    # check DB dses updated
    ds_model.clear_cache()
    DB_dses = ds_model.ds_ids
    assert len(DB_dses) == len(DB_dses_init) + 1
    new_ds = [dsid for dsid in DB_dses if dsid not in DB_dses_init][0]
    DB_dses_updated = DB_dses
    # check UI dses updated
    tabs = tablist.find_elements_by_class_name("item")
    UI_dses = [tab.find_element_by_class_name("tablabel").get_attribute("data-tab") for tab in tabs]
    assert UI_dses == UI_dses_init + ["ds{}".format(new_ds)]
    UI_dses_updated = UI_dses

    # verify DS added to dropdowns
    live_updates = browser.find_element_by_id("seg_live_updates")
    lk_dropdown = live_updates.find_element_by_class_name("ui.selection.dropdown")
    upload_modal = browser.find_element_by_id("uploadModal")
    up_dropdown = upload_modal.find_element_by_class_name("ui.selection.dropdown.ds_selection")
    ids = [item[0] for item in conftest.get_semantic_dropdown_data(lk_dropdown)]
    assert sorted(ids) == sorted(UI_dses_updated)
    ids = [item[0] for item in conftest.get_semantic_dropdown_data(up_dropdown)]
    assert sorted(ids) == sorted(UI_dses_updated)

    # delete DS -- Cancel
    btnDelete = [btn for btn in tablist.find_elements_by_class_name("del_ds.button") if btn.get_attribute("data-tab") == "ds{}".format(new_ds)][0]
    modal = browser.find_element_by_id("deleteModal")
    btnCancel = modal.find_element_by_class_name("cancel.button")
    btnConfirm = modal.find_element_by_class_name("ok.button")
    btnDelete.click()
    assert conftest.modal_is_visible(modal)
    btnCancel.click()
    assert not conftest.modal_is_visible(modal)

    # check UI not changed
    tabs = tablist.find_elements_by_class_name("item")
    UI_dses = [tab.find_element_by_class_name("tablabel").get_attribute("data-tab") for tab in tabs]
    assert UI_dses == UI_dses_updated
    # check DB not changed
    ds_model.clear_cache()
    DB_dses = ds_model.ds_ids
    assert DB_dses == DB_dses_updated

    # delete DS -- Confirm
    btnDelete.click()
    assert conftest.modal_is_visible(modal)
    btnConfirm.click()
    assert not conftest.modal_is_visible(modal)
    # check UI updated
    tabs = tablist.find_elements_by_class_name("item")
    UI_dses = [tab.find_element_by_class_name("tablabel").get_attribute("data-tab") for tab in tabs]
    assert UI_dses == UI_dses_init
    # check DB updated
    ds_model.clear_cache()
    DB_dses = ds_model.ds_ids
    assert DB_dses == DB_dses_init

    # verify new DS removed from dropdowns
    live_updates = browser.find_element_by_id("seg_live_updates")
    lk_dropdown = live_updates.find_element_by_class_name("ui.selection.dropdown")
    upload_modal = browser.find_element_by_id("uploadModal")
    up_dropdown = upload_modal.find_element_by_class_name("ui.selection.dropdown.ds_selection")
    ids = [item[0] for item in conftest.get_semantic_dropdown_data(lk_dropdown)]
    assert sorted(ids) == sorted(UI_dses_init)
    ids = [item[0] for item in conftest.get_semantic_dropdown_data(up_dropdown)]
    assert sorted(ids) == sorted(UI_dses_init)


@ensure_settings_page
def test_ds_name(browser):
    """
    [Data Source]
      "Name" should be editable and save
    :type browser: webdriver.Firefox
    """
    DATABASE_TIME = 0.3  # seconds to allow for transactions
    ds_model = Datasources(conftest.db, {}, conftest.sub_id)
    pages = browser.find_element_by_id("ds_tab_contents")
    active_pages = pages.find_elements_by_class_name("segment.active")
    assert len(active_pages) == 1
    page = active_pages[0]
    dsid = page.get_attribute("data-tab")
    dsid = int(dsid[2:])

    # test name changes
    input_name = page.find_element_by_class_name("ds_name")
    old_name = input_name.get_attribute("value")
    db_name = ds_model.datasources[dsid]['name']
    assert old_name == db_name

    # input_name.clear() was not working in selenium 3.5 and firefox 55.0.1
    input_name.send_keys(Keys.CONTROL + "a")
    input_name.send_keys(Keys.DELETE)
    input_name.send_keys("alternative" + Keys.RETURN)
    time.sleep(DATABASE_TIME)
    ds_model.clear_cache()
    db_name = ds_model.datasources[dsid]['name']
    assert db_name == "alternative"

    input_name.send_keys(Keys.CONTROL + "a")
    input_name.send_keys(Keys.DELETE)
    input_name.send_keys(old_name + Keys.RETURN)
    time.sleep(DATABASE_TIME)
    ds_model.clear_cache()
    db_name = ds_model.datasources[dsid]['name']
    assert db_name == old_name


@ensure_settings_page
def test_ds_autorefresh(browser):
    """
    [Data Source]
      "Auto-refresh" should be editable and save
    :type browser: webdriver.Firefox
    """
    DATABASE_TIME = 0.3  # seconds to allow for transactions
    ds_model = Datasources(conftest.db, {}, conftest.sub_id)
    pages = browser.find_element_by_id("ds_tab_contents")
    active_pages = pages.find_elements_by_class_name("segment.active")
    assert len(active_pages) == 1
    page = active_pages[0]
    dsid = page.get_attribute("data-tab")
    dsid = int(dsid[2:])

    # get old value
    input_ar = page.find_element_by_class_name("ds_live")
    old_value = input_ar.get_attribute("checked")
    ds_model.clear_cache()
    db_ar = ds_model.datasources[dsid]['ar_active']
    assert (db_ar == 1) == (old_value == "true")

    # change and check
    input_ar.click()
    time.sleep(DATABASE_TIME)
    ds_model.clear_cache()
    db_ar = ds_model.datasources[dsid]['ar_active']
    assert (db_ar == 1) == (not (old_value == "true"))

    # change back and check
    input_ar.click()
    time.sleep(DATABASE_TIME)
    ds_model.clear_cache()
    db_ar = ds_model.datasources[dsid]['ar_active']
    assert (db_ar == 1) == (old_value == "true")


@ensure_settings_page
def test_ds_autorefresh_interval(browser):
    """
    [Data Source]
      "Auto-refresh interval" should be editable and save
    :type browser: webdriver.Firefox
    """
    DATABASE_TIME = 0.7  # seconds to allow for transactions
    ds_model = Datasources(conftest.db, {}, conftest.sub_id)
    pages = browser.find_element_by_id("ds_tab_contents")
    active_pages = pages.find_elements_by_class_name("segment.active")
    assert len(active_pages) == 1
    page = active_pages[0]
    dsid = page.get_attribute("data-tab")
    dsid = int(dsid[2:])

    # get old value
    input_interval = page.find_element_by_class_name("ds_interval")
    old_interval = input_interval.get_attribute("value")
    db_interval = ds_model.datasources[dsid]['ar_interval']
    assert int(old_interval) == db_interval

    # input_interval.clear() was not working in selenium 3.5 and firefox 55.0.1
    input_interval.send_keys(Keys.CONTROL + "a")
    input_interval.send_keys(Keys.DELETE)
    input_interval.send_keys("150" + Keys.RETURN)
    time.sleep(DATABASE_TIME)
    ds_model.clear_cache()
    db_interval = ds_model.datasources[dsid]['ar_interval']
    assert db_interval == 150

    input_interval = page.find_element_by_class_name("ds_interval")
    input_interval.send_keys(Keys.CONTROL + "a")
    input_interval.send_keys(Keys.DELETE)
    input_interval.send_keys(old_interval + Keys.RETURN)
    time.sleep(DATABASE_TIME)
    ds_model.clear_cache()
    db_interval = ds_model.datasources[dsid]['ar_interval']
    assert db_interval == int(old_interval)


@ensure_settings_page
def test_ds_flat_mode(browser):
    """
    [Data Source]
      "Flat mode" should be editable and save
    :type browser: webdriver.Firefox
    """
    DATABASE_TIME = 0.3  # seconds to allow for transactions
    ds_model = Datasources(conftest.db, {}, conftest.sub_id)
    pages = browser.find_element_by_id("ds_tab_contents")
    active_pages = pages.find_elements_by_class_name("segment.active")
    assert len(active_pages) == 1
    page = active_pages[0]
    dsid = page.get_attribute("data-tab")
    dsid = int(dsid[2:])

    # get old value
    input_flat = page.find_element_by_class_name("ds_flat")
    old_value = input_flat.get_attribute("checked")
    ds_model.clear_cache()
    db_flat = ds_model.datasources[dsid]['flat']
    assert (db_flat == 1) == (old_value == "true")

    # change and check
    input_flat.click()
    time.sleep(DATABASE_TIME)
    ds_model.clear_cache()
    db_flat = ds_model.datasources[dsid]['flat']
    assert (db_flat == 1) == (not (old_value == "true"))

    # change back and check
    input_flat.click()
    time.sleep(DATABASE_TIME)
    ds_model.clear_cache()
    db_flat = ds_model.datasources[dsid]['flat']
    assert (db_flat == 1) == (old_value == "true")


@ensure_settings_page
def test_ds_del_connections(browser):
    """
      "Delete Connections" should open a [modal]
        Cancel should close modal without action
        Confirm should perform action (delete link information)
    :type browser: webdriver.Firefox
    """
    assert True


@ensure_settings_page
def test_ds_upload_log(browser):
    """
      "Upload Log" should open [upload modal]
        Modal should allow file picking, no type filter
        Log Format dropdown should include all format options
        Data source dropdown should include all available datasources
        Cancel should close modal with no action
        Upload should perform [uploading action]
          If no file selected, nothing happens, modal stays open.
          On completion, a new modal indicates success/failure of upload
    :type browser: webdriver.Firefox
    """
    assert True
