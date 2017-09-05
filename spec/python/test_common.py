import os
import pytest
import web
from spec.python import db_connection
from sam import common, constants, integrity

THIS_DIR = os.path.dirname(__file__)


def test_load_plugins():
    try:
        assert 'root' in constants.plugins
        constants.plugins['root'] = 'bad/directory'
        assert common.load_plugins() == []

        constants.plugins['root'] = os.path.join(THIS_DIR, 'plugins')
        constants.plugins['enabled'] = []
        assert constants.plugins['loaded'] == []
        assert common.load_plugins() == []
        assert constants.plugins['loaded'] == []

        constants.plugins['enabled'] = ['ALL']
        assert set(common.load_plugins()) == {'test_plugin1', 'test_plugin2'}
        assert set(constants.plugins['loaded']) == {'test_plugin1', 'test_plugin2'}
    finally:
        constants.plugin_templates = []
        constants.plugin_static = []
        constants.plugin_importers = []
        constants.plugin_urls = []
        constants.plugin_models = []
        constants.plugin_rules = []
        constants.plugin_navbar_edits = []
        constants.plugin_hooks_traffic_import = []
        constants.plugin_hooks_server_start = []


def test_init_globals():
    common.init_globals()
    assert isinstance(common.renderer, common.MultiRender)

    assert len(common.renderer.bare_paths) == 0
    test_path = os.path.join(THIS_DIR, 'plugins', 'test_plugin2')
    constants.plugin_templates = [test_path]
    common.init_globals()
    assert len(common.renderer.bare_paths) == 1

    constants.plugin_templates = []
    constants.plugin_urls = [
        '/test_url', 'test_plugin2.pages.test_url.TestUrl'
    ]
    old_len = len(constants.urls)
    common.init_globals()
    assert len(common.renderer.bare_paths) == 0
    assert len(constants.urls) == old_len + 2

    constants.plugin_urls = []
    common.init_globals()
    assert len(constants.urls) == old_len


def test_parse_sql_file():
    expected = ['DROP TABLE IF EXISTS tmyKey_blah',
                '\n \n \n CREATE TABLE IF NOT EXISTS tmyKey_blah\n'
                ' (port              INT UNSIGNED NOT NULL\n'
                ' ,CONSTRAINT PKportAliasLUT PRIMARY KEY (port)\n'
                ' )',
                '\n \n SELECT * FROM tmyKey_blah\n ']
    replacements = {'id': "myKey"}
    actual = common.parse_sql_file("./spec/python/test_sql.sql", replacements)
    assert actual == expected


def test_execute_sql_file():
    tables = integrity.get_table_names(db_connection.db)
    assert "t13531_blah" not in tables

    common.exec_sql(db_connection.db, os.path.join(THIS_DIR, "test_sql.sql"), {'id': '13531'})
    tables = integrity.get_table_names(db_connection.db)
    assert "t13531_blah" in tables

    db_connection.db.query("DROP TABLE t13531_blah")
    tables = integrity.get_table_names(db_connection.db)
    assert "t13531_blah" not in tables


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


def test_get_domain():
    assert common.get_domain('protocol://user:pass@subdomain.domain.tld:port/path/to/file.extension?key=value#hash') == 'subdomain.domain.tld'
    assert common.get_domain('protocol://user@subdomain.domain.tld:port/path/to/file.extension?key=value') == 'subdomain.domain.tld'
    assert common.get_domain('protocol://user@subdomain.domain.tld:port/path/to/file.extension') == 'subdomain.domain.tld'
    assert common.get_domain('protocol://user@subdomain.domain.tld:port/path/to/') == 'subdomain.domain.tld'
    assert common.get_domain('protocol://user@subdomain.domain.tld/path/to/') == 'subdomain.domain.tld'
    assert common.get_domain('protocol://:pass@subdomain.domain.tld:port/path/to/') == 'subdomain.domain.tld'
    assert common.get_domain('protocol://:pass@subdomain.domain.tld/path/to/') == 'subdomain.domain.tld'
    assert common.get_domain('protocol://subdomain.domain.tld/path/to/') == 'subdomain.domain.tld'
    assert common.get_domain('protocol://subdomain.domain.tld') == 'subdomain.domain.tld'
    assert common.get_domain('subdomain.domain.tld/path/to/') == 'subdomain.domain.tld'
    assert common.get_domain('subdomain.domain.tld:port') == 'subdomain.domain.tld'
    assert common.get_domain('subdomain.domain.tld') == 'subdomain.domain.tld'


def test_get_db():
    mysqlconfig = {
        'dbn': "mysql",
        'db': db_connection.TEST_DATABASE_MYSQL,
        'host': "localhost",
        'user': "root",
        'pw': constants.dbconfig['pw'],
        'port': 3306
    }
    sqliteconfig = {
        'dbn': "sqlite",
        'db': db_connection.TEST_DATABASE_SQLITE,
        'host': "localhost",
        'user': "root",
        'pw': constants.dbconfig['pw'],
        'port': 3306
    }
    db, dbq = common.get_db(mysqlconfig)
    print(db)
    print(type(db))
    assert isinstance(db, web.db.DB)
    assert isinstance(db, web.db.MySQLDB)

    db, dbq = common.get_db(sqliteconfig)
    print(db)
    print(type(db))
    assert isinstance(db, web.db.DB)
    assert isinstance(db, web.db.SqliteDB)


def test_db_concat():
    class C:
        def __init__(self, dbn):
            self.dbname = dbn
    mysql = C('mysql')
    sqlite = C('sqlite')

    with pytest.raises(ValueError):
        assert common.db_concat(mysql) == 'CONCAT()'
    assert common.db_concat(mysql, "hi") == "CONCAT('hi')"
    assert common.db_concat(mysql, "'hi'", "'lo'") == """CONCAT("'hi'","'lo'")"""
    assert common.db_concat(mysql, 1, 2, 3) == "CONCAT(1,2,3)"

    with pytest.raises(ValueError):
        assert common.db_concat(sqlite) == ''
    assert common.db_concat(sqlite, "hi") == "'hi'"
    assert common.db_concat(sqlite, "'hi'", "'lo'") == "\"'hi'\"||\"'lo'\""
    assert common.db_concat(sqlite, 1, 2, 3) == '1||2||3'