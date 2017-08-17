"""
Tests:

Changing the ds switcher
    changes address to reflect new DS
    clears and reloads page info/details
Changing the search input text [loads results] after a timeout
    Quick Info is cleared
    Detailed info is cleared
    If [Not Found]
        Error presented
    If [Found]
        Quick Info segment is filled with data
        Inbound Connections is filled with data
        Outbound Connections is filled with data
        Detailed Info [arrives]
            Unique Inputs tab is filled
            Unique Outputs tab is filled
            Local Ports tab is filled
            Child Nodes tab is filled
            Pagination if more than 50 entries in a tab
                User can page forwards or backwards
            Tables can all be sorted by all columns
Quick Info
    Changing the name field will update the DB
    Changing the tags field will update the DB
    Changing the environment field will update the DB
"""
import operator
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from sam.models.nodes import Nodes
from spec.browser import conftest

LOAD_TIMEOUT = 0.8


def at_metadata_page(browser):
    return browser.current_url.endswith("/metadata")


def ensure_metadata_page(func):
    def func_wrapper(browser):
        if not at_metadata_page(browser):
            browser.get(conftest.host + "metadata")
        func(browser)
    return func_wrapper


@ensure_metadata_page
def test_changing_input_invokes_search(browser):
    """
    Changing the search input text [loads results] after a timeout
        Quick Info is cleared
        Detailed info is cleared
        If [Not Found]
            Error presented
        If [Found]
            Quick Info segment is filled with data
            Inbound Connections is filled with data
            Outbound Connections is filled with data
    :type browser: webdriver.Firefox
    """
    # find some useful elements for this test
    search_div = browser.find_element_by_id("hostSearch")
    search_input = search_div.find_element_by_tag_name("input")
    qi_tbody = browser.find_element_by_id("quickinfo")
    ib_seg = browser.find_element_by_id("in_col")
    ob_seg = browser.find_element_by_id("out_col")

    # check all is empty
    rows = qi_tbody.find_elements_by_tag_name("tr")
    assert len(rows) == 1  # "Waiting..."
    rows = ib_seg.find_elements_by_tag_name("tr")
    assert len(rows) == 0
    rows = ob_seg.find_elements_by_tag_name("tr")
    assert len(rows) == 0
    assert search_input.get_attribute("value") == u''
    tab_input_table = browser.find_element_by_id("conn_in")
    tab_output_table = browser.find_element_by_id("conn_out")
    tab_ports_table = browser.find_element_by_id("ports_in")
    tab_kids_table = browser.find_element_by_id("child_nodes")
    assert len(tab_input_table.find_elements_by_tag_name("tr")) == 0
    assert len(tab_output_table.find_elements_by_tag_name("tr")) == 0
    assert len(tab_ports_table.find_elements_by_tag_name("tr")) == 0
    assert len(tab_kids_table.find_elements_by_tag_name("tr")) == 0

    # update search with absent IP
    search_input.send_keys("40")
    rows = qi_tbody.find_elements_by_tag_name("tr")
    assert len(rows) == 1  # "Waiting..."
    rows = ib_seg.find_elements_by_tag_name("tr")
    assert len(rows) == 0
    rows = ob_seg.find_elements_by_tag_name("tr")
    assert len(rows) == 0
    # wait for the loading function to kick in. (700ms)
    time.sleep(LOAD_TIMEOUT)
    rows = qi_tbody.find_elements_by_tag_name("tr")
    assert len(rows) == 2  # Address 40;  No host found
    rows = ib_seg.find_elements_by_tag_name("tr")
    assert len(rows) == 0
    rows = ob_seg.find_elements_by_tag_name("tr")
    assert len(rows) == 0
    tab_input_table = browser.find_element_by_id("conn_in")
    tab_output_table = browser.find_element_by_id("conn_out")
    tab_ports_table = browser.find_element_by_id("ports_in")
    tab_kids_table = browser.find_element_by_id("child_nodes")
    assert len(tab_input_table.find_elements_by_tag_name("tr")) == 0
    assert len(tab_output_table.find_elements_by_tag_name("tr")) == 0
    assert len(tab_ports_table.find_elements_by_tag_name("tr")) == 0
    assert len(tab_kids_table.find_elements_by_tag_name("tr")) == 0

    # update search with real IP
    search_input.clear()
    search_input.send_keys("10")
    rows = qi_tbody.find_elements_by_tag_name("tr")
    assert len(rows) == 2  # "Waiting..."
    rows = ib_seg.find_elements_by_tag_name("tr")
    assert len(rows) == 0
    rows = ob_seg.find_elements_by_tag_name("tr")
    assert len(rows) == 0
    # wait for the loading function to kick in. (700ms)
    time.sleep(LOAD_TIMEOUT)
    rows = qi_tbody.find_elements_by_tag_name("tr")
    assert len(rows) == 9
    rows = ib_seg.find_elements_by_tag_name("tr")
    assert len(rows) == 11
    rows = ob_seg.find_elements_by_tag_name("tr")
    assert len(rows) == 11
    tab_input_table = browser.find_element_by_id("conn_in")
    tab_output_table = browser.find_element_by_id("conn_out")
    tab_ports_table = browser.find_element_by_id("ports_in")
    tab_kids_table = browser.find_element_by_id("child_nodes")
    assert len(tab_input_table.find_elements_by_tag_name("tr")) == 50
    assert len(tab_output_table.find_elements_by_tag_name("tr")) == 50
    assert len(tab_ports_table.find_elements_by_tag_name("tr")) == 40
    assert len(tab_kids_table.find_elements_by_tag_name("tr")) == 2

    # update search with blank
    search_input.send_keys(Keys.BACKSPACE*18)
    rows = qi_tbody.find_elements_by_tag_name("tr")
    assert len(rows) == 9
    rows = ib_seg.find_elements_by_tag_name("tr")
    assert len(rows) == 11
    rows = ob_seg.find_elements_by_tag_name("tr")
    assert len(rows) == 11
    # wait for the loading function to kick in. (700ms)
    time.sleep(LOAD_TIMEOUT)
    rows = qi_tbody.find_elements_by_tag_name("tr")
    assert len(rows) == 1  # Waiting...
    rows = ib_seg.find_elements_by_tag_name("tr")
    assert len(rows) == 0
    rows = ob_seg.find_elements_by_tag_name("tr")
    assert len(rows) == 0
    tab_input_table = browser.find_element_by_id("conn_in")
    tab_output_table = browser.find_element_by_id("conn_out")
    tab_ports_table = browser.find_element_by_id("ports_in")
    tab_kids_table = browser.find_element_by_id("child_nodes")
    assert len(tab_input_table.find_elements_by_tag_name("tr")) == 0
    assert len(tab_output_table.find_elements_by_tag_name("tr")) == 0
    assert len(tab_ports_table.find_elements_by_tag_name("tr")) == 0
    assert len(tab_kids_table.find_elements_by_tag_name("tr")) == 0


@ensure_metadata_page
def test_changing_ds_switcher(browser):
    """
    Changing the ds switcher
        changes address to reflect new DS
        clears and reloads page info/details
    :type browser: webdriver.Firefox
    """
    # find some useful elements
    search_div = browser.find_element_by_id("hostSearch")
    search_input = search_div.find_element_by_tag_name("input")
    qi_tbody = browser.find_element_by_id("quickinfo")
    ib_seg = browser.find_element_by_id("in_col")
    ob_seg = browser.find_element_by_id("out_col")

    # set ds and search target to starting condition: default ds, search for "10"
    browser.execute_script("""$("div.floating.dropdown.button").dropdown("set selected", "ds{}");""".format(conftest.ds))
    search_input.send_keys("10")

    time.sleep(LOAD_TIMEOUT)
    # assert content is loaded
    rows = qi_tbody.find_elements_by_tag_name("tr")
    assert len(rows) == 9  # Address 40;  No host found
    rows = ib_seg.find_elements_by_tag_name("tr")
    assert len(rows) == 11
    rows = ob_seg.find_elements_by_tag_name("tr")
    assert len(rows) == 11
    # assert values represent correct DS
    ib_rows = ib_seg.find_elements_by_tag_name("tr")
    assert ib_rows[2].text == u'Total connections recorded: 138 over 113 weeks'
    ob_rows = ob_seg.find_elements_by_tag_name("tr")
    assert ob_rows[2].text == u'Total connections recorded: 142 over 113 weeks'

    # switch ds
    browser.execute_script("""$("div.floating.dropdown.button").dropdown("set selected", "ds{}");""".format(conftest.ds_short))
    time.sleep(LOAD_TIMEOUT)
    # assert content is loaded
    rows = qi_tbody.find_elements_by_tag_name("tr")
    assert len(rows) == 9  # Address 40;  No host found
    rows = ib_seg.find_elements_by_tag_name("tr")
    assert len(rows) == 11
    rows = ob_seg.find_elements_by_tag_name("tr")
    assert len(rows) == 11
    # assert values represent correct DS
    ib_rows = ib_seg.find_elements_by_tag_name("tr")
    assert ib_rows[2].text == u'Total connections recorded: 0 over 5 minutes'
    ob_rows = ob_seg.find_elements_by_tag_name("tr")
    assert ob_rows[2].text == u'Total connections recorded: 0 over 5 minutes'

    # set the ds back
    browser.execute_script("""$("div.floating.dropdown.button").dropdown("set selected", "ds{}");""".format(conftest.ds))


@ensure_metadata_page
def test_qi_name(browser):
    """
    Quick Info
        Changing the name field will update the DB
    :type browser: webdriver.Firefox
    """
    # find some useful elements for this test
    search_div = browser.find_element_by_id("hostSearch")
    search_input = search_div.find_element_by_tag_name("input")
    search_input.send_keys("10")
    time.sleep(LOAD_TIMEOUT)
    edit_name = browser.find_element_by_id("edit_name")

    # name should match from DB:
    nodes_model = Nodes(conftest.db, conftest.sub_id)
    node = nodes_model.get("10")
    if node.alias is None:
        assert edit_name.get_attribute("value") == u''
    else:
        assert edit_name.get_attribute("value") == node.alias

    # edit name
    edit_name.clear()
    edit_name.send_keys("plo777", Keys.RETURN)
    # give DB a chance to update
    time.sleep(0.1)
    node = nodes_model.get("10")
    assert node.alias == "plo777"

    #clear name
    edit_name.send_keys(Keys.BACKSPACE*10, Keys.RETURN)
    time.sleep(0.1)
    node = nodes_model.get("10")
    assert node.alias == u''


@ensure_metadata_page
def test_qi_tags(browser):
    """
    Quick Info
        Changing the tags field will update the DB
    :type browser: webdriver.Firefox
    """
    # find some useful elements for this test
    qi_tbody = browser.find_element_by_id("quickinfo")
    search_div = browser.find_element_by_id("hostSearch")
    search_input = search_div.find_element_by_tag_name("input")
    search_input.clear()
    search_input.send_keys("10")
    time.sleep(LOAD_TIMEOUT)
    edit_tags = browser.find_element_by_id("edit_tags")

    # name should match from DB:
    nodes_model = Nodes(conftest.db, conftest.sub_id)
    tags = nodes_model.get_tags("10")
    assert tags == {'p_tags': [], 'tags': []}
    # tags on node:
    assert edit_tags.get_attribute("value") == u''
    # tags on parent node:
    parent_tags = qi_tbody.find_elements_by_class_name("parenttag")
    assert [pt.text for pt in parent_tags] == []

    # add tags to 10
    browser.execute_script("""$(".multiple.search.selection.dropdown").dropdown("set selected", "Tag10");""")
    browser.execute_script("""$(".multiple.search.selection.dropdown").dropdown("set selected", "Tag 10b");""")
    # verify tags on 10 in DB
    time.sleep(0.1)
    tags = nodes_model.get_tags("10")
    assert tags['p_tags'] == []
    assert set(tags['tags']) == {u'Tag10', u'Tag 10b'}
    # tags on node:
    assert set(edit_tags.get_attribute("value").split(",")) == set(tags['tags'])
    # tags on parent node:
    parent_tags = qi_tbody.find_elements_by_class_name("parenttag")
    assert {pt.text for pt in parent_tags} == set(tags['p_tags'])


    # add tags to 10.20
    search_input.clear()
    search_input.send_keys("10.20")
    time.sleep(LOAD_TIMEOUT)
    edit_tags = browser.find_element_by_id("edit_tags")
    browser.execute_script("""$(".multiple.search.selection.dropdown").dropdown("set selected", "Tag20");""")
    browser.execute_script("""$(".multiple.search.selection.dropdown").dropdown("set selected", "Tag 20b");""")
    # verify tags on 10.20 in DB
    time.sleep(0.1)
    tags = nodes_model.get_tags("10.20")
    assert set(tags['p_tags']) == {u'Tag10', u'Tag 10b'}
    assert set(tags['tags']) == {u'Tag20', u'Tag 20b'}
    # tags on node:
    assert set(edit_tags.get_attribute("value").split(",")) == set(tags['tags'])
    # tags on parent node:
    parent_tags = qi_tbody.find_elements_by_class_name("parenttag")
    assert {pt.text for pt in parent_tags} == set(tags['p_tags'])


    # remove tags from 10.20
    browser.execute_script("""$(".multiple.search.selection.dropdown").dropdown("remove selected", "Tag20");""")
    browser.execute_script("""$(".multiple.search.selection.dropdown").dropdown("remove selected", "Tag 20b");""")
    # verify tags on 10.20 in DB
    time.sleep(0.1)
    tags = nodes_model.get_tags("10.20")
    assert set(tags['p_tags']) == {u'Tag10', u'Tag 10b'}
    assert tags['tags'] == []
    # tags on node:
    assert edit_tags.get_attribute("value") == u''
    # tags on parent node:
    parent_tags = qi_tbody.find_elements_by_class_name("parenttag")
    assert {pt.text for pt in parent_tags} == set(tags['p_tags'])

    # remove tags from 10
    # verify tags on 10
    search_input.clear()
    search_input.send_keys("10")
    time.sleep(LOAD_TIMEOUT)
    edit_tags = browser.find_element_by_id("edit_tags")
    browser.execute_script("""$(".multiple.search.selection.dropdown").dropdown("remove selected", "Tag10");""")
    browser.execute_script("""$(".multiple.search.selection.dropdown").dropdown("remove selected", "Tag 10b");""")
    # verify tags on 10.20 in DB
    time.sleep(0.1)
    tags = nodes_model.get_tags("10")
    assert tags['p_tags'] == []
    assert tags['tags'] == []
    # tags on node:
    assert edit_tags.get_attribute("value") == u''
    # tags on parent node:
    parent_tags = qi_tbody.find_elements_by_class_name("parenttag")
    assert [pt.text for pt in parent_tags] == []


@ensure_metadata_page
def test_qi_env(browser):
    """
    Quick Info
        Changing the environment field will update the DB
    :type browser: webdriver.Firefox
    """
    # find some useful elements for this test
    node_model = Nodes(conftest.db, conftest.sub_id)
    search_div = browser.find_element_by_id("hostSearch")
    search_input = search_div.find_element_by_tag_name("input")
    search_input.clear()
    search_input.send_keys("10")
    time.sleep(LOAD_TIMEOUT)
    edit_env = browser.find_element_by_id("edit_env")

    # verify it starting conditions
    ui_env = edit_env.get_attribute("value")
    node = node_model.get("10")
    db_env = node.env
    if db_env is None:
        assert ui_env == "inherit"
    else:
        assert ui_env == db_env

    # change the env
    browser.execute_script("""$("#edit_env").parent().dropdown("set selected", "alternative");""")
    time.sleep(0.1)
    ui_env = edit_env.get_attribute("value")
    node = node_model.get("10")
    db_env = node.env
    assert ui_env == "alternative"
    assert db_env == "alternative"

    # change it back
    browser.execute_script("""$("#edit_env").parent().dropdown("set selected", "inherit");""")
    time.sleep(0.1)
    ui_env = edit_env.get_attribute("value")
    node = node_model.get("10")
    db_env = node.env
    assert ui_env == "inherit"
    assert db_env == "inherit"


@ensure_metadata_page
def test_tab_pagination(browser):
    """
    Tabs paginate when more than 50 rows
        Pagination can be forwards and backwards
    :type browser: webdriver.Firefox
    """
    # find some useful elements for this test
    search_div = browser.find_element_by_id("hostSearch")
    search_input = search_div.find_element_by_tag_name("input")
    tab_menu = browser.find_element_by_css_selector(".ui.pointing.secondary.menu")
    tabs = tab_menu.find_elements_by_class_name("item")
    assert len(tabs) == 4
    tabs.sort(key=operator.attrgetter('text'))
    tab_input = tabs[2]
    tab_output = tabs[3]
    tab_ports = tabs[1]
    tab_children = tabs[0]
    assert tab_input.text == "Unique Inputs"
    assert tab_output.text == "Unique Outputs"
    assert tab_ports.text == "Local Ports"
    assert tab_children.text == "Child Nodes"
    tabpage_input = browser.find_element_by_id("tab-input")
    tabpage_output = browser.find_element_by_id("tab-output")
    tabpage_ports = browser.find_element_by_id("tab-ports")
    tabpage_children = browser.find_element_by_id("tab-children")

    # load host 110
    search_input.clear()
    search_input.send_keys("110", Keys.RETURN)
    time.sleep(LOAD_TIMEOUT)

    # all pagination inputs should be disabled
    tab_input.click()
    buttons = tabpage_input.find_elements_by_tag_name("button")
    assert len(buttons) == 2
    assert 'disabled' in set(buttons[0].get_attribute("class").split())
    assert 'disabled' in set(buttons[1].get_attribute("class").split())
    buttons = tabpage_output.find_elements_by_tag_name("button")
    assert len(buttons) == 2
    assert 'disabled' in set(buttons[0].get_attribute("class").split())
    assert 'disabled' in set(buttons[1].get_attribute("class").split())
    buttons = tabpage_ports.find_elements_by_tag_name("button")
    assert len(buttons) == 2
    assert 'disabled' in set(buttons[0].get_attribute("class").split())
    assert 'disabled' in set(buttons[1].get_attribute("class").split())
    buttons = tabpage_children.find_elements_by_tag_name("button")
    assert len(buttons) == 2
    assert 'disabled' in set(buttons[0].get_attribute("class").split())
    assert 'disabled' in set(buttons[1].get_attribute("class").split())

    # load host 10
    search_input.clear()
    search_input.send_keys("10", Keys.RETURN)
    time.sleep(LOAD_TIMEOUT + 0.3)
    # input and output pages exceed 50 and the 'next' btn should not be disabled.
    buttons = tabpage_input.find_elements_by_tag_name("button")
    assert len(buttons) == 2
    assert 'disabled' in set(buttons[0].get_attribute("class").split())
    assert 'disabled' not in set(buttons[1].get_attribute("class").split())
    buttons = tabpage_output.find_elements_by_tag_name("button")
    assert len(buttons) == 2
    assert 'disabled' in set(buttons[0].get_attribute("class").split())
    assert 'disabled' not in set(buttons[1].get_attribute("class").split())
    buttons = tabpage_ports.find_elements_by_tag_name("button")
    assert len(buttons) == 2
    assert 'disabled' in set(buttons[0].get_attribute("class").split())
    assert 'disabled' in set(buttons[1].get_attribute("class").split())
    buttons = tabpage_children.find_elements_by_tag_name("button")
    assert len(buttons) == 2
    assert 'disabled' in set(buttons[0].get_attribute("class").split())
    assert 'disabled' in set(buttons[1].get_attribute("class").split())

    # changing page should load new content.

    # inputs page:
    tab_input.click()
    tbody = tabpage_input.find_element_by_tag_name("tbody")
    rows = tbody.find_elements_by_tag_name("tr")
    p1 = {tuple(row.text.split()[:3]) for row in rows}
    row_sum = len(rows)
    # next page
    buttons = tabpage_input.find_elements_by_tag_name("button")
    assert buttons[1].text == "next"
    buttons[1].click()
    time.sleep(0.15)
    tbody = tabpage_input.find_element_by_tag_name("tbody")
    rows = tbody.find_elements_by_tag_name("tr")
    p2 = {tuple(row.text.split()[:3]) for row in rows}
    row_sum += len(rows)
    # next page
    buttons = tabpage_input.find_elements_by_tag_name("button")
    assert buttons[1].text == "next"
    buttons[1].click()
    time.sleep(0.15)
    tbody = tabpage_input.find_element_by_tag_name("tbody")
    rows = tbody.find_elements_by_tag_name("tr")
    p3 = {tuple(row.text.split()[:3]) for row in rows}
    row_sum += len(rows)
    # assert there are as many unique rows (src;dst;port) as presented rows
    assert row_sum == len(p1.union(p2).union(p3))
    # back page
    buttons = tabpage_input.find_elements_by_tag_name("button")
    assert buttons[0].text == "prev"
    buttons[0].click()
    time.sleep(0.15)
    tbody = tabpage_input.find_element_by_tag_name("tbody")
    rows = tbody.find_elements_by_tag_name("tr")
    assert p2 == {tuple(row.text.split()[:3]) for row in rows}
    # back page
    buttons = tabpage_input.find_elements_by_tag_name("button")
    assert buttons[0].text == "prev"
    buttons[0].click()
    time.sleep(0.15)
    tbody = tabpage_input.find_element_by_tag_name("tbody")
    rows = tbody.find_elements_by_tag_name("tr")
    assert p1 == {tuple(row.text.split()[:3]) for row in rows}

    # output page:
    tab_output.click()
    tbody = tabpage_output.find_element_by_tag_name("tbody")
    rows = tbody.find_elements_by_tag_name("tr")
    p1 = {tuple(row.text.split()[:3]) for row in rows}
    row_sum = len(rows)
    # next page
    buttons = tabpage_output.find_elements_by_tag_name("button")
    assert buttons[1].text == "next"
    buttons[1].click()
    time.sleep(0.15)
    tbody = tabpage_output.find_element_by_tag_name("tbody")
    rows = tbody.find_elements_by_tag_name("tr")
    p2 = {tuple(row.text.split()[:3]) for row in rows}
    row_sum += len(rows)
    # next page
    buttons = tabpage_output.find_elements_by_tag_name("button")
    assert buttons[1].text == "next"
    buttons[1].click()
    time.sleep(0.15)
    tbody = tabpage_output.find_element_by_tag_name("tbody")
    rows = tbody.find_elements_by_tag_name("tr")
    p3 = {tuple(row.text.split()[:3]) for row in rows}
    row_sum += len(rows)
    # assert there are as many unique rows (src;dst;port) as presented rows
    assert row_sum == len(p1.union(p2).union(p3))
    # back page
    buttons = tabpage_output.find_elements_by_tag_name("button")
    assert buttons[0].text == "prev"
    buttons[0].click()
    time.sleep(0.15)
    tbody = tabpage_output.find_element_by_tag_name("tbody")
    rows = tbody.find_elements_by_tag_name("tr")
    assert p2 == {tuple(row.text.split()[:3]) for row in rows}
    # back page
    buttons = tabpage_output.find_elements_by_tag_name("button")
    assert buttons[0].text == "prev"
    buttons[0].click()
    time.sleep(0.15)
    tbody = tabpage_output.find_element_by_tag_name("tbody")
    rows = tbody.find_elements_by_tag_name("tr")
    assert p1 == {tuple(row.text.split()[:3]) for row in rows}


@ensure_metadata_page
def test_tab_table_sorting_inputs(browser):
    """
    Tab tables sort on column clicked
    :type browser: webdriver.Firefox
    """
    # find some useful elements for this test
    search_div = browser.find_element_by_id("hostSearch")
    search_input = search_div.find_element_by_tag_name("input")
    tab_menu = browser.find_element_by_css_selector(".ui.pointing.secondary.menu")
    tabs = tab_menu.find_elements_by_class_name("item")
    assert len(tabs) == 4
    tabs.sort(key=operator.attrgetter('text'))
    tab_input = tabs[2]
    assert tab_input.text == "Unique Inputs"
    tab_input.click()
    tabpage_input = browser.find_element_by_id("tab-input")

    # load host 10.20.30
    search_input.clear()
    search_input.send_keys("10.20.30", Keys.RETURN)
    time.sleep(LOAD_TIMEOUT + 0.3)

    # each header click should change item order from previous state.
    thead = tabpage_input.find_element_by_tag_name("thead")
    tbody = tabpage_input.find_element_by_tag_name("tbody")
    rows = tbody.find_elements_by_tag_name("tr")
    old_page = [tuple(row.text.split()[:3]) for row in rows]
    headers = thead.find_elements_by_tag_name("th")
    for i in range(len(headers)):
        headers = thead.find_elements_by_tag_name("th")
        print("sorting {} descending".format(headers[i].text))
        headers[i].click()
        time.sleep(0.3)
        tbody = tabpage_input.find_element_by_tag_name("tbody")
        rows = tbody.find_elements_by_tag_name("tr")
        page = [tuple(row.text.split()[:3]) for row in rows]
        assert page != old_page
        old_page = page
        headers = thead.find_elements_by_tag_name("th")
        print("sorting {} ascending".format(headers[i].text))
        headers[i].click() # sort in reverse order
        time.sleep(0.3)
        tbody = tabpage_input.find_element_by_tag_name("tbody")
        rows = tbody.find_elements_by_tag_name("tr")
        page = [tuple(row.text.split()[:3]) for row in rows]
        assert page != old_page
        old_page = page


@ensure_metadata_page
def test_tab_table_sorting_outputs(browser):
    """
    Tab tables sort on column clicked
    :type browser: webdriver.Firefox
    """
    # find some useful elements for this test
    search_div = browser.find_element_by_id("hostSearch")
    search_input = search_div.find_element_by_tag_name("input")
    tab_menu = browser.find_element_by_css_selector(".ui.pointing.secondary.menu")
    tabs = tab_menu.find_elements_by_class_name("item")
    assert len(tabs) == 4
    tabs.sort(key=operator.attrgetter('text'))
    tab_output = tabs[3]
    assert tab_output.text == "Unique Outputs"
    tab_output.click()
    tabpage_output = browser.find_element_by_id("tab-output")

    # load host 10.20.30
    search_input.clear()
    search_input.send_keys("10.20.30", Keys.RETURN)
    time.sleep(LOAD_TIMEOUT + 0.3)

    # each header click should change item order from previous state.
    thead = tabpage_output.find_element_by_tag_name("thead")
    tbody = tabpage_output.find_element_by_tag_name("tbody")
    rows = tbody.find_elements_by_tag_name("tr")
    old_page = [tuple(row.text.split()[:3]) for row in rows]
    headers = thead.find_elements_by_tag_name("th")
    for i in range(len(headers)):
        headers = thead.find_elements_by_tag_name("th")
        print("sorting {} descending".format(headers[i].text))
        headers[i].click()
        time.sleep(0.3)
        tbody = tabpage_output.find_element_by_tag_name("tbody")
        rows = tbody.find_elements_by_tag_name("tr")
        page = [tuple(row.text.split()[:3]) for row in rows]
        assert page != old_page
        old_page = page
        headers = thead.find_elements_by_tag_name("th")
        print("sorting {} ascending".format(headers[i].text))
        headers[i].click() # sort in reverse order
        time.sleep(0.3)
        tbody = tabpage_output.find_element_by_tag_name("tbody")
        rows = tbody.find_elements_by_tag_name("tr")
        page = [tuple(row.text.split()[:3]) for row in rows]
        assert page != old_page
        old_page = page


@ensure_metadata_page
def test_tab_table_sorting_ports(browser):
    """
    Tab tables sort on column clicked
    :type browser: webdriver.Firefox
    """
    # find some useful elements for this test
    search_div = browser.find_element_by_id("hostSearch")
    search_input = search_div.find_element_by_tag_name("input")
    tab_menu = browser.find_element_by_css_selector(".ui.pointing.secondary.menu")
    tabs = tab_menu.find_elements_by_class_name("item")
    assert len(tabs) == 4
    tabs.sort(key=operator.attrgetter('text'))
    tab_ports = tabs[1]
    assert tab_ports.text == "Local Ports"
    tab_ports.click()
    tabpage_ports = browser.find_element_by_id("tab-ports")

    # load host 10.20.30
    search_input.clear()
    search_input.send_keys("10.20.30", Keys.RETURN)
    time.sleep(LOAD_TIMEOUT + 0.3)

    # each header click should change item order from previous state.
    thead = tabpage_ports.find_element_by_tag_name("thead")
    tbody = tabpage_ports.find_element_by_tag_name("tbody")
    rows = tbody.find_elements_by_tag_name("tr")
    old_page = [tuple(row.text.split()[:3]) for row in rows]
    headers = thead.find_elements_by_tag_name("th")
    for i in range(len(headers)):
        headers = thead.find_elements_by_tag_name("th")
        print("sorting {} descending".format(headers[i].text))
        headers[i].click()
        time.sleep(0.3)
        tbody = tabpage_ports.find_element_by_tag_name("tbody")
        rows = tbody.find_elements_by_tag_name("tr")
        page = [tuple(row.text.split()[:3]) for row in rows]
        assert page != old_page
        old_page = page
        headers = thead.find_elements_by_tag_name("th")
        print("sorting {} ascending".format(headers[i].text))
        headers[i].click() # sort in reverse order
        time.sleep(0.3)
        tbody = tabpage_ports.find_element_by_tag_name("tbody")
        rows = tbody.find_elements_by_tag_name("tr")
        page = [tuple(row.text.split()[:3]) for row in rows]
        assert page != old_page
        old_page = page


@ensure_metadata_page
def test_tab_table_sorting_children(browser):
    """
    Tab tables sort on column clicked
    :type browser: webdriver.Firefox
    """
    # find some useful elements for this test
    search_div = browser.find_element_by_id("hostSearch")
    search_input = search_div.find_element_by_tag_name("input")
    tab_menu = browser.find_element_by_css_selector(".ui.pointing.secondary.menu")
    tabs = tab_menu.find_elements_by_class_name("item")
    assert len(tabs) == 4
    tabs.sort(key=operator.attrgetter('text'))
    tab_children = tabs[0]
    assert tab_children.text == "Child Nodes"
    tab_children.click()
    tabpage_children = browser.find_element_by_id("tab-children")

    # load host 10.20.30
    search_input.clear()
    search_input.send_keys("10.20.30", Keys.RETURN)
    time.sleep(LOAD_TIMEOUT + 0.3)

    # each header click should change item order from previous state.
    thead = tabpage_children.find_element_by_tag_name("thead")
    old_page = []
    for i in (0, 3):
        headers = thead.find_elements_by_tag_name("th")
        print("sorting {} descending".format(headers[i].text))
        headers[i].click()
        time.sleep(0.3)
        tbody = tabpage_children.find_element_by_tag_name("tbody")
        rows = tbody.find_elements_by_tag_name("tr")
        page = [tuple(row.text.split()[:3]) for row in rows]
        assert page != old_page
        old_page = page
        headers = thead.find_elements_by_tag_name("th")
        print("sorting {} ascending".format(headers[i].text))
        headers[i].click() # sort in reverse order
        time.sleep(0.3)
        tbody = tabpage_children.find_element_by_tag_name("tbody")
        rows = tbody.find_elements_by_tag_name("tr")
        page = [tuple(row.text.split()[:3]) for row in rows]
        assert page != old_page
        old_page = page
