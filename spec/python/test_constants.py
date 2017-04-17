from spec.python import db_connection
from sam import constants


def test_urls():
    assert (len(constants.urls) & 1) == 0
    pairs = zip(constants.urls[::2], constants.urls[1::2])
    for url, class_ in pairs:
        assert url[0] == '/'


def test_navbar():
    nav = constants.navbar
    assert type(nav) == list
    assert type(nav[0]) == dict
    for link in nav:
        assert 'name' in link
        assert 'link' in link
        assert 'icon' in link
        assert 'group' in link
