import common


def test_navbar():
    nav = common.navbar
    assert type(nav) == list
    assert type(nav[0]) == dict
    assert sorted(nav[0].keys()) == ["icon", "link", "name"]

def test_IPtoString():
    convert = common.IPtoString
    assert convert(0) == "0.0.0.0"
    assert convert(2**32-1) == "255.255.255.255"
    assert convert(0xFEDCBA98) == "254.220.186.152"

def test_IPtoInt():
    convert = common.IPtoInt
    assert convert(0,0,0,0) == 0
    assert convert(255,255,255,255) == 2**32-1
    assert convert(254,220,186,152) == 0xFEDCBA98