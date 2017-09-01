from spec.python import db_connection
from sam.local import en, rv, fr


def test_consistent_en_fr():
    en_keys = {k for k in dir(en) if not k.startswith("__")}
    fr_keys = {k for k in dir(fr) if not k.startswith("__")}
    assert en_keys == fr_keys


def test_consistent_en_rv():
    en_keys = {k for k in dir(en) if not k.startswith("__")}
    rv_keys = {k for k in dir(rv) if not k.startswith("__")}
    assert en_keys == rv_keys