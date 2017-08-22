"""
Tests:
[Security Dashboard]
clicking refresh
    will read the existing filters
    retrieve updated information from the DB
    and display it in the table
editing Subnet Filter
    will normalize the entered value (or enter 0.0.0.0/0)
    will re-get alerts using all filters
    and display it in the table
Editing min severity
    will re-get alerts using all filters
    and display it in the table
Editing timerange
    will normalize the entered value to an accepted value or the last valid value
    will re-get alerts using all filters
    and display it in the table
Delete All
    prompts for confirmation before deleting alerts
Clicking "0 alerts to display"
    should do nothing
Clicking alert
    should display additional details below
    key fields on left, table of metadata on right
    clicking delete button
        should prompt confirmation
        cancel should do nothing
        confirmation should delete the specific individual alert
Pagination
    buttons will be disabled unless appropriate.

[Anomaly Detection]
    show section greyed out
    present link to more information

[Rules]
    default rules exist


"""
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from sam.models.nodes import Nodes
from spec.browser import conftest

