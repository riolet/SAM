import common


def test_navbar():
    nav = common.navbar
    assert type(nav) == list
    assert type(nav[0]) == dict
    assert sorted(nav[0].keys()) == ["icon", "link", "name"]


def test_IPtoString():
    convert = common.IPtoString
    assert convert(0) == "0.0.0.0"
    assert convert(2 ** 32 - 1) == "255.255.255.255"
    assert convert(0xFEDCBA98) == "254.220.186.152"


def test_IPtoInt():
    convert = common.IPtoInt
    assert convert(0, 0, 0, 0) == 0
    assert convert(255, 255, 255, 255) == 2 ** 32 - 1
    assert convert(254, 220, 186, 152) == 0xFEDCBA98


def test_IPStringtoInt():
    convert = common.IPStringtoInt
    assert convert("0.0.0.0") == 0
    assert convert("255.255.255.255") == 0xFFFFFFFF
    assert convert("254.220.186.152") == 0xFEDCBA98
    assert convert("6.7.8.9") == 0x06070809


def test_determine_range():
    assert common.determine_range() == (0x00000000, 0xffffffff, 0x1000000)
    assert common.determine_range(12) == (0xc000000, 0xcffffff, 0x10000)
    assert common.determine_range(12, 8) == (0xc080000, 0xc08ffff, 0x100)
    assert common.determine_range(12, 8, 192) == (0xc08c000, 0xc08c0ff, 0x1)
    assert common.determine_range(12, 8, 192, 127) == (0xc08c07f, 0xc08c07f, 0x1)


def test_determine_range_string():
    assert common.determine_range_string() == (0x00000000, 0xffffffff)
    assert common.determine_range_string("12") == (0xc000000, 0xcffffff)
    assert common.determine_range_string("12.12.12.12/8") == (0xc000000, 0xcffffff)
    assert common.determine_range_string("12.8") == (0xc080000, 0xc08ffff)
    assert common.determine_range_string("12.8.12.8/16") == (0xc080000, 0xc08ffff)
    assert common.determine_range_string("12.8.192") == (0xc08c000, 0xc08c0ff)
    assert common.determine_range_string("12.8.192.12/24") == (0xc08c000, 0xc08c0ff)
    assert common.determine_range_string("12.8.192.127") == (0xc08c07f, 0xc08c07f)
    assert common.determine_range_string("12.8.192.127/32") == (0xc08c07f, 0xc08c07f)
