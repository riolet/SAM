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

import pytest
from sam import constants
from spec.browser import conftest
from sam.local import en as strings


def at_settings_page(browser):
    return browser.current_url.endswith("/settings_page")


def ensure_stats_page(browser):
    if not at_settings_page(browser):
        browser.get(conftest.host + "settings_page")


def test_