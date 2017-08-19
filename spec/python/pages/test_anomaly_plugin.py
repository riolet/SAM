from spec.python import db_connection

import pytest
import web
from sam.pages.anomaly_plugin import ADPlugin
from sam import constants
from sam import errors
import json
import urllib

db = db_connection.db
sub_id = db_connection.default_sub
ds_full = db_connection.dsid_default


def test_decode_get_request():
    # request can be:
    #   (opt) method: "status"(default) | "warnings" | "warning"
    #   if warnings:
    #      (opt) all: "true" | "false"(default)
    #   if warning:
    #      warning_id: r"\d+"
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        ad = ADPlugin()
        data = {}
        expected = {'method': 'status'}
        request = ad.decode_get_request(data)
        assert request == expected

        data = {'method': 'status'}
        expected = {'method': 'status'}
        request = ad.decode_get_request(data)
        assert request == expected

        data = {'method': 'warning'}
        with pytest.raises(errors.RequiredKey):
            request = ad.decode_get_request(data)
        data = {'method': 'warning', 'warning_id': ''}
        with pytest.raises(errors.MalformedRequest):
            request = ad.decode_get_request(data)
        data = {'method': 'warning', 'warning_id': 'huh'}
        with pytest.raises(errors.MalformedRequest):
            request = ad.decode_get_request(data)
        
        data = {'method': 'warning', 'warning_id': '12'}
        expected = {'method': 'warning', 'warning': 12}
        request = ad.decode_get_request(data)
        assert request == expected

        data = {'method': 'warnings'}
        expected = {'method': 'warnings', 'show_all': False}
        request = ad.decode_get_request(data)
        assert request == expected

        data = {'method': 'warnings', 'all': 'false'}
        expected = {'method': 'warnings', 'show_all': False}
        request = ad.decode_get_request(data)
        assert request == expected

        data = {'method': 'warnings', 'all': 'other'}
        expected = {'method': 'warnings', 'show_all': False}
        request = ad.decode_get_request(data)
        assert request == expected

        data = {'method': 'warnings', 'all': 'true'}
        expected = {'method': 'warnings', 'show_all': True}
        request = ad.decode_get_request(data)
        assert request == expected

        data = {'method': 'warnings', 'all': 'TRUE'}
        expected = {'method': 'warnings', 'show_all': True}
        request = ad.decode_get_request(data)
        assert request == expected
        

def test_perform_get_command():
    # request can be one of:
    #   {'method': 'warning', 'warning_id': \d}
    #   {'method': 'warnings', 'show_all': True|False
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        ad = ADPlugin()
        
    