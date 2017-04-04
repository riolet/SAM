import constants
import common
import integrity
import traceback

mysql_params = constants.dbconfig.copy()
sqlite_params = constants.dbconfig.copy()

mysql_params['dbn'] = 'mysql'
mysql_params['db'] = 'samapper_test'
sqlite_params['dbn'] = 'sqlite'
sqlite_params['db'] = '/tmp/sam_test.db'

db_mysql, _ = common.get_db(mysql_params)
db_sqlite, _ = common.get_db(sqlite_params)


def test_mysql_access():
    print(mysql_params)
    assert integrity.check_and_fix_db_access_MySQL(mysql_params) == 0


def test_sqlite_access():
    assert integrity.check_and_fix_db_access_SQLite(sqlite_params) == 0


def test_mysql_shared_tables():
    try:
        errors = integrity.check_shared_tables(db_mysql)
        integrity.fix_shared_tables(db_mysql, errors)
    except:
        traceback.print_exc()
        assert False


def test_sqlite_shared_tables():
    try:
        errors = integrity.check_shared_tables(db_sqlite)
        integrity.fix_shared_tables(db_sqlite, errors)
    except:
        traceback.print_exc()
        assert False


def test_mysql_UDF():
    integrity.fix_UDF_MySQL(db_mysql)
    rows = db_mysql.query('SELECT decodeIP(1234567890)')
    assert rows.first().values()[0] == '73.150.2.210'
    rows = db_mysql.query('SELECT encodeIP(12,34,56,78)')
    assert rows.first().values()[0] == 203569230L


def test_sqlite_UDF():
    integrity.fix_UDF_SQLite(db_sqlite)
    rows = db_sqlite.query('SELECT decodeIP(1234567890)')
    assert rows.first().values()[0] == '73.150.2.210'
    rows = db_sqlite.query('SELECT encodeIP(12,34,56,78)')
    assert rows.first().values()[0] == 203569230L


def test_mysql_def_subscription():
    try:
        errors = integrity.check_default_subscription(db_mysql)
        integrity.fix_default_subscription(db_mysql, errors)
    except:
        traceback.print_exc()
        assert False

def test_sqlite_def_subscription():
    try:
        errors = integrity.check_default_subscription(db_sqlite)
        integrity.fix_default_subscription(db_sqlite, errors)
    except:
        traceback.print_exc()
        assert False


def test_mysql_subscriptions():
    try:
        errors = integrity.check_default_subscription(db_mysql)
        integrity.fix_default_subscription(db_mysql, errors)
    except:
        traceback.print_exc()
        assert False


def test_sqlite_subscriptions():
    try:
        errors = integrity.check_subscriptions(db_sqlite)
        integrity.fix_subscriptions(db_sqlite, errors)
    except:
        traceback.print_exc()
        assert False


def test_mysql_settings():
    try:
        errors = integrity.check_settings(db_mysql)
        integrity.fix_settings(db_mysql, errors)
    except:
        traceback.print_exc()
        assert False


def test_sqlite_settings():
    try:
        errors = integrity.check_settings(db_sqlite)
        integrity.fix_settings(db_sqlite, errors)
    except:
        traceback.print_exc()
        assert False


def test_mysql_datasources():
    try:
        errors = integrity.check_data_sources(db_mysql)
        integrity.fix_data_sources(db_mysql, errors)
    except:
        traceback.print_exc()
        assert False


def test_sqlite_datasources():
    try:
        errors = integrity.check_data_sources(db_sqlite)
        integrity.fix_data_sources(db_sqlite, errors)
    except:
        traceback.print_exc()
        assert False


def test_mysql_session():
    try:
        errors = integrity.check_sessions_table(db_mysql)
        integrity.fix_sessions_table(db_mysql, errors)
    except:
        traceback.print_exc()
        assert False


def test_sqlite_session():
    try:
        errors = integrity.check_sessions_table(db_sqlite)
        integrity.fix_sessions_table(db_sqlite, errors)
    except:
        traceback.print_exc()
        assert False
