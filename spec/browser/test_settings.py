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
from sam.models.links import Links
from sam.pages import settings_page
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
def test_switch_datasource(browser):
    """Clicking on the datasource name should switch datasources.
    :type browser: webdriver.Firefox
    """
    # determine currently active tab page:
    page = browser.find_element_by_id("ds_tab_contents")
    active_pages = page.find_elements_by_css_selector(".segment.active")
    assert len(active_pages) == 1
    initial_ds = active_pages[0].get_attribute("data-tab")

    # determine the current tab
    tablist = browser.find_element_by_id("ds_tabs")
    active_tabs = tablist.find_elements_by_css_selector(".item.active")
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
    active_pages = page.find_elements_by_css_selector(".segment.active")
    assert len(active_pages) == 1
    assert active_pages[0].get_attribute("data-tab") == other_ds
    active_tabs = tablist.find_elements_by_css_selector(".item.active")
    active_tab = active_tabs[0].find_element_by_class_name("tablabel")
    assert len(active_tabs) == 1
    assert active_tab.get_attribute("data-tab") == other_ds

    # switch back
    initial_tab.click()
    active_pages = page.find_elements_by_css_selector(".segment.active")
    assert len(active_pages) == 1
    assert active_pages[0].get_attribute("data-tab") == initial_ds
    active_tabs = tablist.find_elements_by_css_selector(".item.active")
    active_tab = active_tabs[0].find_element_by_class_name("tablabel")
    assert len(active_tabs) == 1
    assert active_tab.get_attribute("data-tab") == initial_ds


@ensure_settings_page
def test_create_delete_datasource(browser):
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
    btnCancel = modal.find_element_by_css_selector(".cancel.button")
    btnConfirm = modal.find_element_by_css_selector(".ok.button")
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
    lk_dropdown = live_updates.find_element_by_css_selector(".ui.selection.dropdown")
    upload_modal = browser.find_element_by_id("uploadModal")
    up_dropdown = upload_modal.find_element_by_css_selector(".ui.selection.dropdown.ds_selection")
    ids = [item[0] for item in conftest.get_semantic_dropdown_data(lk_dropdown)]
    assert sorted(ids) == sorted(UI_dses_updated)
    ids = [item[0] for item in conftest.get_semantic_dropdown_data(up_dropdown)]
    assert sorted(ids) == sorted(UI_dses_updated)

    # delete DS -- Cancel
    btnDelete = [btn for btn in tablist.find_elements_by_css_selector(".del_ds.button") if btn.get_attribute("data-tab") == "ds{}".format(new_ds)][0]
    modal = browser.find_element_by_id("deleteModal")
    btnCancel = modal.find_element_by_css_selector(".cancel.button")
    btnConfirm = modal.find_element_by_css_selector(".ok.button")
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
    lk_dropdown = live_updates.find_element_by_css_selector(".ui.selection.dropdown")
    upload_modal = browser.find_element_by_id("uploadModal")
    up_dropdown = upload_modal.find_element_by_css_selector(".ui.selection.dropdown.ds_selection")
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
    active_pages = pages.find_elements_by_css_selector(".segment.active")
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
    active_pages = pages.find_elements_by_css_selector(".segment.active")
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
    active_pages = pages.find_elements_by_css_selector(".segment.active")
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
    active_pages = pages.find_elements_by_css_selector(".segment.active")
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


# works on chrome, fails on firefox (due to webdrive and fileinput accepting send_keys)
def test_ds_upload_delete(browser, tmpdir):
    """
      "Upload Log" should open [upload modal]
        Modal should allow file picking, no type filter
        Log Format dropdown should include all format options
        Data source dropdown should include all available datasources
        Cancel should close modal with no action
        Upload should perform [uploading action]
          If no file selected, nothing happens, modal stays open.
          On completion, a new modal indicates success/failure of upload

      "Delete Connections" should open a [modal]
        Cancel should close modal without action
        Confirm should perform action (delete link information)
    :type browser: webdriver.Firefox
    """
    # replacement for the decorator
    if not at_settings_page(browser):
        browser.get(conftest.host + "settings_page")
    # make sure "short" ds is selected.
    tabs = browser.find_elements_by_css_selector("#ds_tabs .tablabel")
    tab = None
    for t in tabs:
        if t.get_attribute("data-tab") == "ds{}".format(conftest.ds_short):
            tab = t
            break
    tab.click()

    # find some elements on the page to test with
    link_model = Links(conftest.db, conftest.sub_id, conftest.ds_short)
    pages = browser.find_element_by_id("ds_tab_contents")
    page = pages.find_element_by_css_selector(".segment.active")
    btn_delete = page.find_element_by_css_selector(".button.del_con")
    delete_modal = browser.find_element_by_id("deleteModal")
    dm_cancel = delete_modal.find_element_by_css_selector(".cancel.button")
    dm_confirm = delete_modal.find_element_by_css_selector(".ok.button")
    btn_upload = page.find_element_by_css_selector(".button.upload_con")
    upload_modal = browser.find_element_by_id("uploadModal")
    input_file = browser.find_element_by_id("log_path")
    input_ds = upload_modal.find_element_by_css_selector(".selection.dropdown.ds_selection")
    dropdowns = upload_modal.find_elements_by_css_selector(".selection.dropdown")
    assert len(dropdowns) == 2
    input_format = filter(lambda x: x is not input_ds, dropdowns)[0]
    um_cancel = upload_modal.find_element_by_css_selector(".cancel.button")
    um_confirm = upload_modal.find_element_by_css_selector(".ok.button")
    response_modal = browser.find_element_by_css_selector(".ui.response.modal")
    rm_cancel = response_modal.find_element_by_css_selector(".cancel.button")

    # create dummy file to upload
    f = tmpdir.join("dummy.log")
    f.write("""{"message":"1,2016/06/21 17:11:02,0009C100218,TRAFFIC,end,1,2016/06/21 17:11:02,12.34.220.185,12.34.169.215,0.0.0.0,0.0.0.0,Alert Rule,,,dns,vsys1,TAP-T0000R021,TAP-T0000R021,ethernet1/3,ethernet1/3,Copy Traffic Logs to Syslog,2016/06/21 17:11:02,303318,1,53,47288,0,0,0x100019,udp,allow,106,106,0,1,2016/06/21 17:10:29,30,any,0,598681,0x0,US,US,0,1,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy","@version":"1","@timestamp":"2016-06-22T00:11:02.000Z","host":"172.21.35.5","priority":14,"timestamp":"Jun 21 17:11:02","logsource":"Palo-Alto-Networks","severity":6,"facility":1,"facility_label":"user-level","severity_label":"Informational"}
{"message":"1,2016/06/21 17:11:02,0009C100218,TRAFFIC,end,1,2016/06/21 17:11:02,10.0.160.228,12.34.171.158,0.0.0.0,0.0.0.0,Alert Rule,,,incomplete,vsys1,TAP-T0000R022,TAP-T0000R022,ethernet1/4,ethernet1/4,Copy Traffic Logs to Syslog,2016/06/21 17:11:02,352949,1,61003,443,0,0,0x19,tcp,allow,66,66,0,1,2016/06/21 17:10:54,5,any,0,598688,0x0,10.0.0.0-10.255.255.255,US,0,1,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy","@version":"1","@timestamp":"2016-06-22T00:11:02.000Z","host":"172.21.35.5","priority":14,"timestamp":"Jun 21 17:11:02","logsource":"Palo-Alto-Networks","severity":6,"facility":1,"facility_label":"user-level","severity_label":"Informational"}
{"message":"1,2016/06/21 17:11:02,0009C100218,TRAFFIC,end,1,2016/06/21 17:11:02,10.1.244.52,12.34.91.22,0.0.0.0,0.0.0.0,Alert Rule,,,incomplete,vsys1,TAP-T0000R021,TAP-T0000R021,ethernet1/3,ethernet1/3,Copy Traffic Logs to Syslog,2016/06/21 17:11:02,190635,1,56473,443,0,0,0x19,tcp,allow,12195,12195,0,20,2016/06/21 16:10:59,3600,any,0,598689,0x0,10.0.0.0-10.255.255.255,US,0,20,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy","@version":"1","@timestamp":"2016-06-22T00:11:02.000Z","host":"172.21.35.5","priority":14,"timestamp":"Jun 21 17:11:02","logsource":"Palo-Alto-Networks","severity":6,"facility":1,"facility_label":"user-level","severity_label":"Informational"}
""")
    assert f.check()

    # make sure the destination ds starts empty, and modal is hidden
    link_model.delete_connections()
    ends = link_model.get_all_endpoints()
    assert len(ends) == 0
    assert not conftest.modal_is_visible(upload_modal)

    # click upload
    btn_upload.click()
    assert conftest.modal_is_visible(upload_modal)
    # cancel, modal closes
    um_cancel.click()
    assert not conftest.modal_is_visible(upload_modal)
    btn_upload.click()
    assert conftest.modal_is_visible(upload_modal)
    # confirm without file, modal stays open
    um_confirm.click()
    assert conftest.modal_is_visible(upload_modal)

    # data sources represented:
    dd = conftest.get_semantic_dropdown_data(input_ds)
    dd = set([d[0] for d in dd])
    assert dd == set(map("ds{}".format, [conftest.ds, conftest.ds_short, conftest.ds_live]))
    # choose paloalto:
    browser.execute_script("""$("#log_format").parent().dropdown("set selected", "import_paloalto");""")
    assert browser.find_element_by_id("log_format").get_attribute("value") == "import_paloalto"

    # log formats represented:
    expected = settings_page.SettingsPage.get_available_importers()
    actual = conftest.get_semantic_dropdown_data(input_format)
    assert actual == expected
    # choose ds_short
    browser.execute_script("""$("#log_ds").parent().dropdown("set selected", "short");""")
    assert browser.find_element_by_id("log_ds").get_attribute("value") == "ds{}".format(conftest.ds_short)

    # offer a file
    # TODO: tests fail in firefox because fileinput will not accept send_keys.
    # selenium.common.exceptions.WebDriverException: Message: File not found:
    input_file.send_keys("/home/joe/test.log")
    # input_file.send_keys(os.path.abspath(str(f)))

    # click confirm
    um_confirm.click()
    # upload modal should close
    assert not conftest.modal_is_visible(upload_modal)
    # sleep for file upload
    time.sleep(0.2)
    # after a short period, an info modal should appear indicating success.
    assert conftest.modal_is_visible(response_modal)
    rm_cancel.click()
    assert not conftest.modal_is_visible(response_modal)

    # check that links model has new rows in it
    ends = link_model.get_all_endpoints()
    assert len(ends) != 0

    # delete newly uploaded connections
    btn_delete.click()
    assert conftest.modal_is_visible(delete_modal)
    # abort, and db is unchanged
    dm_cancel.click()
    assert not conftest.modal_is_visible(delete_modal)
    ends = link_model.get_all_endpoints()
    assert len(ends) != 0
    # confirm and db is cleared
    btn_delete.click()
    assert conftest.modal_is_visible(delete_modal)
    dm_confirm.click()
    assert not conftest.modal_is_visible(delete_modal)
    # sleep for DB update
    time.sleep(0.2)
    ends = link_model.get_all_endpoints()
    assert len(ends) == 0


def test_meta_hosts(browser):
    """
      Should show a few hostnames currently stored in DB
      "Delete [*]" should open a modal to confirm action
        Cancel should close modal with no action
        Confirm should perform [action]
          hostnames, tags or envs deleted
          display updated to show results of action.
    :type browser: webdriver.Firefox
    """
    # put some hostnames into the db
    table = "s{}_Nodes".format(conftest.sub_id)
    conftest.db.update(table, "ipstart=167772160 AND ipend=184549375", alias="Albert")
    conftest.db.update(table, "ipstart=169082880 AND ipend=169148415", alias="Betty")
    conftest.db.update(table, "ipstart=169090560 AND ipend=169090815", alias="Charles")
    conftest.db.update(table, "ipstart=169090600 AND ipend=169090600", alias="Dorothy")
    conftest.db.update(table, "ipstart=169090601 AND ipend=169090601", alias="Elvis")
    conftest.db.update(table, "ipstart=169091072 AND ipend=169091327", alias="Fiona")
    conftest.db.update(table, "ipstart=169091114 AND ipend=169091114", alias="Gerald")
    conftest.db.update(table, "ipstart=169091115 AND ipend=169091115", alias="Heather")
    conftest.db.update(table, "ipstart=169345024 AND ipend=169410559", alias="Ivan")
    conftest.db.update(table, "ipstart=169353728 AND ipend=169353983", alias="Julie")
    conftest.db.update(table, "ipstart=169353772 AND ipend=169353772", alias="Karl")
    conftest.db.update(table, "ipstart=169353773 AND ipend=169353773", alias="Laura")
    conftest.db.update(table, "ipstart=169354240 AND ipend=169354495", alias="Marvin")
    conftest.db.update(table, "ipstart=169354286 AND ipend=169354286", alias="Nancy")
    conftest.db.update(table, "ipstart=169354287 AND ipend=169354287", alias="Orville")
    conftest.db.update(table, "ipstart=838860800 AND ipend=855638015", alias="Penny")
    conftest.db.update(table, "ipstart=842792960 AND ipend=842858495", alias="Quentin")
    conftest.db.update(table, "ipstart=842810880 AND ipend=842811135", alias="Rachel")
    conftest.db.update(table, "ipstart=842810960 AND ipend=842810960", alias="Sam")
    conftest.db.update(table, "ipstart=842810961 AND ipend=842810961", alias="Tammy")
    conftest.db.update(table, "ipstart=842811392 AND ipend=842811647", alias="Umar")
    conftest.db.update(table, "ipstart=842811474 AND ipend=842811474", alias="Violet")
    conftest.db.update(table, "ipstart=842811475 AND ipend=842811475", alias="Winston")
    conftest.db.update(table, "ipstart=843055104 AND ipend=843120639", alias="Xena")
    conftest.db.update(table, "ipstart=843074048 AND ipend=843074303", alias="Yngwie")
    conftest.db.update(table, "ipstart=843074132 AND ipend=843074132", alias="Zillah")
    time.sleep(0.1)
    # reload page to show hostnames
    browser.get(conftest.host + "settings_page")

    # test that 10 hostnames are shown
    meta = browser.find_element_by_class_name("del_hostnames")
    p = meta.find_element_by_tag_name("p")
    expected = "Current hosts include: Albert, Betty, Charles, Dorothy, Elvis, Fiona, Gerald, Heather, Ivan, and Julie."
    assert p.text == expected

    # delete but cancel
    btn_del = browser.find_element_by_id("del_host")
    modal = browser.find_element_by_id("deleteModal")
    modal_cancel = modal.find_element_by_css_selector(".cancel.button")
    btn_del.click()
    assert conftest.modal_is_visible(modal)
    modal_cancel.click()
    assert not conftest.modal_is_visible(modal)
    browser.get(conftest.host + "settings_page")

    # test that 10 hostnames are shown
    meta = browser.find_element_by_class_name("del_hostnames")
    p = meta.find_element_by_tag_name("p")
    expected = "Current hosts include: Albert, Betty, Charles, Dorothy, Elvis, Fiona, Gerald, Heather, Ivan, and Julie."
    assert p.text == expected

    # delete hostnames
    btn_del = browser.find_element_by_id("del_host")
    modal = browser.find_element_by_id("deleteModal")
    modal_confirm = modal.find_element_by_css_selector(".ok.button")
    btn_del.click()
    assert conftest.modal_is_visible(modal)
    modal_confirm.click()
    assert not conftest.modal_is_visible(modal)
    browser.get(conftest.host + "settings_page")

    # test that no hostnames are shown
    meta = browser.find_element_by_class_name("del_hostnames")
    p = meta.find_element_by_tag_name("p")
    expected = "No hostnames are currently stored."
    assert p.text == expected


def test_meta_tags(browser):
    """
      Should show a few tags currently stored in DB
      "Delete [*]" should open a modal to confirm action
        Cancel should close modal with no action
        Confirm should perform [action]
          hostnames, tags or envs deleted
          display updated to show results of action.
    :type browser: webdriver.Firefox
    """
    # put some tags into the db
    table = "s{}_Tags".format(conftest.sub_id)
    tags = [
        {'ipstart': 167772160, 'ipend': 184549375, 'tag': 'Albert'},
        {'ipstart': 169082880, 'ipend': 169148415, 'tag': 'Betty'},
        {'ipstart': 169090560, 'ipend': 169090815, 'tag': 'Charles'},
        {'ipstart': 169090600, 'ipend': 169090600, 'tag': 'Dorothy'},
        {'ipstart': 169090601, 'ipend': 169090601, 'tag': 'Elvis'},
        {'ipstart': 169091072, 'ipend': 169091327, 'tag': 'Fiona'},
        {'ipstart': 169091114, 'ipend': 169091114, 'tag': 'Gerald'},
        {'ipstart': 169091115, 'ipend': 169091115, 'tag': 'Heather'},
        {'ipstart': 169345024, 'ipend': 169410559, 'tag': 'Ivan'},
        {'ipstart': 169353728, 'ipend': 169353983, 'tag': 'Julie'},
        {'ipstart': 169353772, 'ipend': 169353772, 'tag': 'Karl'},
        {'ipstart': 169353773, 'ipend': 169353773, 'tag': 'Laura'},
        {'ipstart': 169354240, 'ipend': 169354495, 'tag': 'Marvin'},
        {'ipstart': 169354286, 'ipend': 169354286, 'tag': 'Nancy'},
        {'ipstart': 169354287, 'ipend': 169354287, 'tag': 'Orville'},
        {'ipstart': 838860800, 'ipend': 855638015, 'tag': 'Penny'},
        {'ipstart': 842792960, 'ipend': 842858495, 'tag': 'Quentin'},
        {'ipstart': 842810880, 'ipend': 842811135, 'tag': 'Rachel'},
        {'ipstart': 842810960, 'ipend': 842810960, 'tag': 'Sam'},
        {'ipstart': 842810961, 'ipend': 842810961, 'tag': 'Tammy'},
        {'ipstart': 842811392, 'ipend': 842811647, 'tag': 'Umar'},
        {'ipstart': 842811474, 'ipend': 842811474, 'tag': 'Violet'},
        {'ipstart': 842811475, 'ipend': 842811475, 'tag': 'Winston'},
        {'ipstart': 843055104, 'ipend': 843120639, 'tag': 'Xena'},
        {'ipstart': 843074048, 'ipend': 843074303, 'tag': 'Yngwie'},
        {'ipstart': 843074132, 'ipend': 843074132, 'tag': 'Zillah'},
    ]
    conftest.db.multiple_insert(table, tags)

    # reload page to show tags
    time.sleep(0.1)
    browser.get(conftest.host + "settings_page")

    # test that 10 tags are shown
    meta = browser.find_element_by_class_name("del_tags")
    p = meta.find_element_by_tag_name("p")
    expected = "Current tags include: Albert, Betty, Charles, Dorothy, Elvis, Fiona, Gerald, Heather, Ivan, and Julie."
    assert p.text == expected

    # delete but cancel
    btn_del = browser.find_element_by_id("del_tag")
    modal = browser.find_element_by_id("deleteModal")
    modal_cancel = modal.find_element_by_css_selector(".cancel.button")
    btn_del.click()
    assert conftest.modal_is_visible(modal)
    modal_cancel.click()
    assert not conftest.modal_is_visible(modal)
    browser.get(conftest.host + "settings_page")

    # test that 10 tags are shown
    meta = browser.find_element_by_class_name("del_tags")
    p = meta.find_element_by_tag_name("p")
    expected = "Current tags include: Albert, Betty, Charles, Dorothy, Elvis, Fiona, Gerald, Heather, Ivan, and Julie."
    assert p.text == expected

    # delete tags
    btn_del = browser.find_element_by_id("del_tag")
    modal = browser.find_element_by_id("deleteModal")
    modal_confirm = modal.find_element_by_css_selector(".ok.button")
    btn_del.click()
    assert conftest.modal_is_visible(modal)
    modal_confirm.click()
    assert not conftest.modal_is_visible(modal)
    browser.get(conftest.host + "settings_page")

    # test that no tags are shown
    meta = browser.find_element_by_class_name("del_tags")
    p = meta.find_element_by_tag_name("p")
    expected = "No tags are currently stored."
    assert p.text == expected


def test_meta_envs(browser):
    """
      Should show a few envs currently stored in DB
      "Delete [*]" should open a modal to confirm action
        Cancel should close modal with no action
        Confirm should perform [action]
          hostnames, tags or envs deleted
          display updated to show results of action.
    :type browser: webdriver.Firefox
    """
    # put some envs into the db
    table = "s{}_Nodes".format(conftest.sub_id)
    conftest.db.update(table, "ipstart=167772160 AND ipend=184549375", env="Albert")
    conftest.db.update(table, "ipstart=169082880 AND ipend=169148415", env="Betty")
    conftest.db.update(table, "ipstart=169090560 AND ipend=169090815", env="Charles")
    conftest.db.update(table, "ipstart=169090600 AND ipend=169090600", env="Dorothy")
    conftest.db.update(table, "ipstart=169090601 AND ipend=169090601", env="Elvis")
    conftest.db.update(table, "ipstart=169091072 AND ipend=169091327", env="Fiona")
    conftest.db.update(table, "ipstart=169091114 AND ipend=169091114", env="Gerald")
    conftest.db.update(table, "ipstart=169091115 AND ipend=169091115", env="Heather")
    conftest.db.update(table, "ipstart=169345024 AND ipend=169410559", env="Ivan")
    conftest.db.update(table, "ipstart=169353728 AND ipend=169353983", env="Julie")
    conftest.db.update(table, "ipstart=169353772 AND ipend=169353772", env="Karl")
    conftest.db.update(table, "ipstart=169353773 AND ipend=169353773", env="Laura")
    conftest.db.update(table, "ipstart=169354240 AND ipend=169354495", env="Marvin")
    conftest.db.update(table, "ipstart=169354286 AND ipend=169354286", env="Nancy")
    conftest.db.update(table, "ipstart=169354287 AND ipend=169354287", env="Orville")
    conftest.db.update(table, "ipstart=838860800 AND ipend=855638015", env="Penny")
    conftest.db.update(table, "ipstart=842792960 AND ipend=842858495", env="Quentin")
    conftest.db.update(table, "ipstart=842810880 AND ipend=842811135", env="Rachel")
    conftest.db.update(table, "ipstart=842810960 AND ipend=842810960", env="Sam")
    conftest.db.update(table, "ipstart=842810961 AND ipend=842810961", env="Tammy")
    conftest.db.update(table, "ipstart=842811392 AND ipend=842811647", env="Umar")
    conftest.db.update(table, "ipstart=842811474 AND ipend=842811474", env="Violet")
    conftest.db.update(table, "ipstart=842811475 AND ipend=842811475", env="Winston")
    conftest.db.update(table, "ipstart=843055104 AND ipend=843120639", env="Xena")
    conftest.db.update(table, "ipstart=843074048 AND ipend=843074303", env="Yngwie")
    conftest.db.update(table, "ipstart=843074132 AND ipend=843074132", env="Zillah")
    # reload page to show envs
    time.sleep(0.1)
    browser.get(conftest.host + "settings_page")

    # test that 10 envs are shown
    meta = browser.find_element_by_class_name("del_envs")
    p = meta.find_element_by_tag_name("p")
    expected = "Current environments include: Albert, Betty, Charles, Dorothy, Elvis, Fiona, Gerald, Heather, Ivan, and Julie."
    assert p.text == expected

    # delete but cancel
    btn_del = browser.find_element_by_id("del_env")
    modal = browser.find_element_by_id("deleteModal")
    modal_cancel = modal.find_element_by_css_selector(".cancel.button")
    btn_del.click()
    assert conftest.modal_is_visible(modal)
    modal_cancel.click()
    assert not conftest.modal_is_visible(modal)
    browser.get(conftest.host + "settings_page")

    # test that 10 envs are shown
    meta = browser.find_element_by_class_name("del_envs")
    p = meta.find_element_by_tag_name("p")
    expected = "Current environments include: Albert, Betty, Charles, Dorothy, Elvis, Fiona, Gerald, Heather, Ivan, and Julie."
    assert p.text == expected

    # delete environments
    btn_del = browser.find_element_by_id("del_env")
    modal = browser.find_element_by_id("deleteModal")
    modal_confirm = modal.find_element_by_css_selector(".ok.button")
    btn_del.click()
    assert conftest.modal_is_visible(modal)
    modal_confirm.click()
    assert not conftest.modal_is_visible(modal)
    browser.get(conftest.host + "settings_page")

    # test that only default envs are shown
    meta = browser.find_element_by_class_name("del_envs")
    p = meta.find_element_by_tag_name("p")
    expected = "Current environments include: dev, and production."
    assert p.text == expected


@ensure_settings_page
def test_live_updates(browser):
    """
      Each live update key in the database should be displayed as a row
      dropdown should list all available datasources
      "Generate" should add a row to the DB and the UI table
        new row should include unique access key
        new row should have chosen destination (from dropdown list)
      X button should remove access key from UI table and from DB
    :type browser: webdriver.Firefox
    """
    live_updates = browser.find_element_by_id("seg_live_updates")
    btn_generate = browser.find_element_by_id("add_live_key")
    dropdown = browser.find_element_by_css_selector(".selection.dropdown")
    body = live_updates.find_element_by_tag_name("tbody")
    rows = body.find_elements_by_tag_name("tr")
    dest_text = ('default', 'short', 'live')
    assert len(rows) == 1

    # add 1 live key for each ds
    browser.execute_script("""$("#live_dest").parent().dropdown("set selected", "ds{}");""".format(conftest.ds))
    btn_generate.click()
    browser.execute_script("""$("#live_dest").parent().dropdown("set selected", "ds{}");""".format(conftest.ds_short))
    btn_generate.click()
    browser.execute_script("""$("#live_dest").parent().dropdown("set selected", "ds{}");""".format(conftest.ds_live))
    btn_generate.click()

    # should be 3 rows now
    time.sleep(0.1)
    rows = body.find_elements_by_tag_name("tr")
    assert len(rows) == 3

    # destinations should match:
    dests = [[data.text for data in row.find_elements_by_tag_name("td") if data.text in dest_text][0] for row in rows]
    assert set(dests) == {u'default', u'short', u'live'}
    # remove "short"
    to_drop = dests.index(u'short')
    rows[to_drop].find_element_by_tag_name("button").click()
    time.sleep(0.1)
    rows = body.find_elements_by_tag_name("tr")
    dests = [[data.text for data in row.find_elements_by_tag_name("td") if data.text in dest_text][0] for row in rows]
    assert set(dests) == {u'default', u'live'}

    # remove "live"
    to_drop = dests.index(u'live')
    rows[to_drop].find_element_by_tag_name("button").click()
    time.sleep(0.1)
    rows = body.find_elements_by_tag_name("tr")
    dests = [[data.text for data in row.find_elements_by_tag_name("td") if data.text in dest_text][0] for row in rows]
    assert dests == [u'default']

    # remove "live"
    rows[0].find_element_by_tag_name("button").click()
    time.sleep(0.1)
    rows = body.find_elements_by_tag_name("tr")
    assert len(rows) == 1
    assert len(rows[0].find_elements_by_tag_name("td")) == 2  # empty table: (x) | none
