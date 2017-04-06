import os
import math
import re
import json
import constants
import common
import web
from MySQLdb import OperationalError
import models.subscriptions
import models.datasources
import models.settings

template_subscription_tables = map(lambda x: 's{acct}_' + x, constants.subscription_tables)
template_tables_per_ds = map(lambda x: 's{acct}_ds{id}_' + x, constants.datasource_tables)

default_db = common.db_quiet


def get_table_names(db):
    """
    :type db: web.DB
    :param db: 
    :return: 
    """
    if db.dbname == 'mysql':
        tables = [x.values()[0] for x in db.query("SHOW TABLES;")]
    elif db.dbname == 'sqlite':
        rows = list(db.select('sqlite_master', what='name', where="type='table'"))
        tables = [row['name'] for row in rows]
    else:
        raise ValueError("Unknown dbn. Cannot determine tables")
    return tables


def check_db_access_MySQL(params):
    # type: () -> int
    """
    Attempt to access the database.

    :return: 0 if successful else MySQL error code
    """
    print("Checking database access...")
    db_name = params.pop('db')
    error_code = 0
    try:
        connection = web.database(**params)
        connection.query("USE {0}".format(db_name))
        print("\tDatabase access confirmed")
    except OperationalError as e:
        print("\tERROR: Database access error:")
        print("\t\tError {0}: {1}".format(e[0], e[1]))
        error_code = e[0]
    return error_code


def check_db_access_SQLite(params):
    # type: () -> int
    """
    Attempt to access the database.

    :return: 0 if successful else non-zero error code
    """
    print("Checking database access...")
    error_code = 0
    try:
        params.pop('host', None)
        params.pop('port', None)
        params.pop('user', None)
        params.pop('pw', None)
        connection = web.database(**params)
        common.sqlite_udf(connection)
        connection.query('SELECT SQLITE_VERSION()')
        print("\tDatabase access confirmed")
    except Exception as e:
        print("\tERROR: Database access error:")
        print("\t\tError {0}: {1}".format(e.args, e.message))
        error_code = 1
    return error_code


def check_and_fix_db_access(params):
    if params['dbn'] == 'sqlite':
        return check_and_fix_db_access_SQLite(params)
    else:
        return check_and_fix_db_access_MySQL(params)


def check_and_fix_db_access_MySQL(params):
    print("Checking database access...")
    db_name = params.pop('db')
    error_code = 0
    print("connecting with {}".format(params))
    connection = web.database(**params)
    try:
        print("connecting to {}".format(db_name))
        connection.query("USE {0}".format(db_name))
        print("\tDatabase access confirmed")
    except OperationalError as e:
        error_code = e[0]
        if e[0] == 1049:
            print("\tERROR: Database {0} not found. Creating.".format(db_name))
            try:
                connection.query("CREATE DATABASE IF NOT EXISTS {0};".format(db_name))
                print("\tDatabase access restored.")
                error_code = 0
            except:
                print("\tError creating database: ")
                print("\t\tError {0}: {1}".format(e[0], e[1]))
        elif e[0] == 1045:  # Access Denied for '%s'@'%s' (using password: (YES|NO))
            print("\tERROR: Unable to continue: invalid username or password")
            print("\tCheck your config file or environment variables.")
        else:
            print("\tERROR: Unable to continue: ")
            print("\t\tError {0}: {1}".format(e[0], e[1]))
    return error_code


def check_and_fix_db_access_SQLite(params):
    print("Checking database access...")
    error_code = 0
    try:
        params.pop('host', None)
        params.pop('port', None)
        params.pop('user', None)
        params.pop('pw', None)
        connection = web.database(**params)
        common.sqlite_udf(connection)
        connection.query('SELECT SQLITE_VERSION()')
        print("\tDatabase access confirmed")
    except Exception as e:
        print("\tERROR: Database access error:")
        print("\t\tError {0}: {1}".format(e.args, e.message))
        error_code = 1
    return error_code


def check_shared_tables(db):
    # type: (web.DB) -> [str]
    """
    Check that all shared tables exist with no regard for contents or structure.

    :return: A list of expected tables that aren't found.
    """
    print("Checking shared tables...")
    tables = get_table_names(db)
    missing_shared_tables = []
    for table in constants.shared_tables:
        if table not in tables:
            missing_shared_tables.append(table)
    if missing_shared_tables:
        print("\tShared tables missing: {0}".format(repr(missing_shared_tables)))
    else:
        print("\tShared tables confirmed")
    return missing_shared_tables


def fix_shared_tables(db, missing_tables):
    print("Fixing shared tables...")
    if not missing_tables:
        print("\tNo tables to fix")
    else:
        print("\tRestoring missing tables: {0}".format(repr(missing_tables)))
        with db.transaction():
            if db.dbname == 'sqlite':
                common.exec_sql(db, os.path.join(constants.base_path, 'sql/setup_shared_tables_sqlite.sql'))
            else:
                common.exec_sql(db, os.path.join(constants.base_path, 'sql/setup_shared_tables_mysql.sql'))
            if "Ports" in missing_tables:
                print("\tPopulating port reference table with latest data")
                fill_port_table(db)
        print("\tShared Tables Fixed")


def fix_UDF_MySQL(db):
    query1 = "DROP FUNCTION IF EXISTS decodeIP;"
    query2 = \
"""CREATE FUNCTION decodeIP (ip INT UNSIGNED)
RETURNS CHAR(15) DETERMINISTIC
RETURN CONCAT_WS(".", ip DIV 16777216, ip DIV 65536 MOD 256, ip DIV 256 MOD 256, ip MOD 256);
"""
    query3 = "DROP FUNCTION IF EXISTS encodeIP;"
    query4 = \
"""CREATE FUNCTION encodeIP (ip8 INT, ip16 INT, ip24 INT, ip32 INT)
RETURNS INT UNSIGNED DETERMINISTIC
RETURN (ip8 * 16777216 + ip16 * 65536 + ip24 * 256 + ip32);"""

    db.query(query1)
    db.query(query2)
    db.query(query3)
    db.query(query4)


def fix_UDF_SQLite(db):
    common.sqlite_udf(db)


def chunk(list_, chunk_size):
    start = 0
    end = chunk_size
    max = len(list_)
    while start <= max:
        yield list_[start:end]
        start += chunk_size
        end += chunk_size


def fill_port_table(db):
    db.delete("Ports", "1=1")
    with open(os.path.join(constants.base_path, 'sql/default_port_data.json'), 'rb') as f:
        port_data = json.loads("".join(f.readlines()))

    ports = port_data["ports"].values()
    for port in ports:
        if len(port['name']) > 10:
            port['name'] = port['name'][:10]
        if len(port['description']) > 255:
            port['description'] = port['description'][:255]
    if db.supports_multiple_insert:
        db.multiple_insert('Ports', values=ports)
    elif db.dbname == 'sqlite':
        db.multiple_insert('Ports', values=ports)
    else:
        for port in ports:
            db.insert('Ports', **port)


def check_default_subscription(db):
    """
    :return: 0 if no problems, -1 if default subscription is missing, -2 if default subscription id is taken.
    """
    print("Checking default subscription")
    sub_model = models.subscriptions.Subscriptions(db)
    subs = sub_model.get_all()
    errors = -1
    for sub in subs:
        if sub['subscription'] == constants.demo['id']:
            if sub['plan'] == 'admin':
                errors = 0
                print("\tDefault subscription confirmed")
            else:
                errors = -2
                print("\tDefault subscription was misappropriated")
            break
    if errors == -1:
        print("\tDefault subscription is missing")
    return errors


def fix_default_subscription(db, errors):
    print("Fixing default subscription")
    if errors == 0:
        print("\tNo fix needed")
    elif errors == -1:
        print("\tCreating default subscription")
        sub_model = models.subscriptions.Subscriptions(db)
        sub_model.create_default_subscription()
    else:
        raise NotImplementedError("Cannot fix bad default subscription")


def check_subscriptions(db):
    """
    Check that each subscription has appropriate subscription-specific tables.
    :param db: the database to use
    :type db: web.DB
    :return: a dictionary containing issues identified in the subscriptions. dictionary may contain keys:
        "extra": a set of all extraneous subscription tables
        "malformed": a set of all subscriptions that are missing one or more tables.
    :rtype: dict[str, set[str]]
    """
    print("Checking subscription tables")
    sub_model = models.subscriptions.Subscriptions(db)
    sub_ids = sub_model.get_id_list()
    all_sub_tables = get_table_names(db)
    all_sub_tables = filter(lambda x: re.match(r'^s\d+_[a-zA-Z0-9]+$', x), all_sub_tables)

    # TODO: catch tables that belong to subscriptions that don't exist any more.
    all_extra_tables = set()
    subs_missing_tables = set()

    for sid in sub_ids:
        # find all tables starting this subscription's prefix
        prefix = "s{0}_".format(sid)
        found_tables = set(filter(lambda s_t: s_t.startswith(prefix), all_sub_tables))
        expected_tables = set([t_s_t.format(acct=sid) for t_s_t in template_subscription_tables])
        missing_tables = expected_tables - found_tables
        extra_tables = found_tables - expected_tables
        if missing_tables:
            print("\tERROR: Subscription {sid} missing tables: {tables}"
                  .format(sid=sid, tables=", ".join(missing_tables)))
            subs_missing_tables.add(sid)
        if extra_tables:
            print("\tERROR: Subscription {sid} has extra tables: {tables}"
                  .format(sid=sid, tables=", ".join(extra_tables)))
            all_extra_tables |= extra_tables
    if not all_extra_tables and not subs_missing_tables:
        print("\tSubscription tables confirmed")
        return {}
    return {'extra': all_extra_tables, 'malformed': subs_missing_tables}


def fix_subscriptions(db, errors):
    """
    :param errors: a dictionary containing issues identified in the subscriptions. dictionary may contain keys:
        "extra": a set of all extraneous subscription tables
        "malformed": a set of all subscriptions that are missing one or more tables.
    """
    print("Fixing subscription tables")
    # remove extra tables
    if 'extra' in errors and len(errors['extra']) > 0:
        print("\tRemoving extra tables")
        for table in errors['extra']:
            db.query("DROP TABLE {0};".format(table))
    # create tables for malformed subscriptions
    sub_model = models.subscriptions.Subscriptions(db)
    if 'malformed' in errors and len(errors['malformed']) > 0:
        for sid in errors['malformed']:
            print("\tRebuilding malformed tables for subscription {0}".format(sid))
            sub_model.create_subscription_tables(sid)
    if not any(map(len, errors.values())):
        print("\tNo fix needed")
    else:
        print("\tSubscriptions fixed")


def check_settings(db):
    """
    Ensure that each subscription has a settings row to go along with it and at least 1 default data source
    :type db: web.DB
    :return: a dictionary containing issues identified in the settings. Dictionary may contain keys:
        "extra": a set of all extraneous settings rows
        "missing": a set of all subscriptions that are missing their settings row
    """
    print("Checking settings...")
    sub_model = models.subscriptions.Subscriptions(db)
    expected = set(sub_model.get_id_list())

    settings_rows = list(db.select("Settings"))
    found = set([s['subscription'] for s in settings_rows])

    missing = expected - found
    extra = found - expected

    issues = {}
    if missing:
        print("\tERROR: Settings missing for subscriptions: {0}".format(missing))
        issues['missing'] = missing
    if extra:
        print("\tERROR: Settings discovered for subscriptions that don't exist: {0}".format(extra))
        issues['extra'] = extra
    if not extra and not missing:
        print("\tSettings confirmed")
    return issues


def fix_settings(db, errors):
    """
    :param errors: a dictionary containing issues identified in the settings. Dictionary may contain keys:
        "extra": a set of all extraneous settings rows
        "missing": a set of all subscriptions that are missing their settings row
    """
    print("Fixing settings...")
    if 'extra' in errors and len(errors['extra']) > 0:
        print("\tDeleting unused settings")
        for table in errors['extra']:
            db.query("DROP TABLE {0};".format(table))
    if 'missing' in errors and len(errors['missing']) > 0:
        for sub_id in errors['missing']:
            print("\tRepairing settings for {0}".format(sub_id))
            settings_model = models.settings.Settings(db, {}, sub_id)
            settings_model.create()

    if not any(map(len, errors.values())):
        print("\tNo fix needed")
    else:
        print("\tSettings fixed")


def check_data_sources(db):
    """
    Ensure that each datasource has all the appropriate ds-specific tables
    :type db: web.DB
    :return: a dictionary containing issues identified in the settings. Dictionary may contain keys:
        "unused": a set of all tables without an owner datasource
        "malformed": a set of all datasources that are missing some of their tables
    """
    print("Checking data sources...")
    sub_model = models.subscriptions.Subscriptions(db)
    all_tables = get_table_names(db)
    ds_table_pattern = re.compile(r'^s\d+_ds\d+_[a-zA-Z0-9]+$')
    ds_tables = set(filter(lambda x: re.match(ds_table_pattern, x), all_tables))
    known_subscriptions = sub_model.get_id_list()

    # issue collections
    extra_tables = set()
    malformed_datasources = set()

    for sub_id in known_subscriptions:
        ds_model = models.datasources.Datasources(db, {}, sub_id)
        for ds_id in ds_model.ds_ids:
            expected_tables = {tab.format(acct=sub_id, id=ds_id) for tab in template_tables_per_ds}
            if not expected_tables.issubset(ds_tables):
                print("\tERROR: Missing Tables for sub {0}, ds {1}".format(sub_id, ds_id))
                malformed_datasources.add((sub_id, ds_id))
            ds_tables -= expected_tables
    extra_tables |= ds_tables
    if len(extra_tables) > 0:
        print("\tERROR: Unused tables: {0}".format(" ".join(extra_tables)))

    if not malformed_datasources and not extra_tables:
        print("\tData sources confirmed")
        return {}

    return {'malformed': malformed_datasources, 'unused': extra_tables}


def fix_data_sources(db, errors):
    """
    :type db: web.DB
    :type errors: dict[str, list[str]]
    :param errors: a dictionary containing issues identified in the settings. Dictionary may contain keys:
        "unused": a set of all tables without an owner datasource
        "malformed": a set of all datasources that are missing some of their tables
    """
    print("Fixing data sources")
    if 'unused' in errors and len(errors['unused']) > 0:
        print("\tDropping extra tables")
        for table in errors['unused']:
            db.query("DROP TABLE {0};".format(table))

    if 'malformed' in errors and len(errors['malformed']) > 0:
        print("\tRebuilding data source tables")
        for sub_id, ds_id in errors['malformed']:
            print("\tRebuilding malformed tables for subscription {0} datasource {1}".format(sub_id, ds_id))
            ds_model = models.datasources.Datasources(db, {}, sub_id)
            ds_model.create_ds_tables(ds_id)

    if not any(map(len, errors.values())):
        print('\tNo fix needed')
    else:
        print('\tData sources fixed')


def check_sessions_table(db):
    # type: () -> bool
    """
    Check if the session table is missing.
    :type db: web.DB
    :return: True if the session table is missing. False otherwise.
    :rtype: bool
    """
    print("Checking session storage...")
    tables = get_table_names(db)
    is_missing = 'sessions' not in tables
    if is_missing:
        print("\tSession table missing")
    else:
        print("\tSession storage confirmed")
    return is_missing


def fix_sessions_table(db, is_missing):
    print("Fixing session storage...")
    if is_missing:
        common.exec_sql(db, os.path.join(constants.base_path, 'sql/sessions.sql'))
        print("\tFixed sessions.")
    else:
        print("\tNo fix needed.")


def check_integrity(db=default_db):
    # ensure we can access the database
    if db.dbname == 'mysql':
        check_db_access = check_db_access_MySQL
    elif db.dbname == 'sqlite':
        check_db_access = check_db_access_SQLite
    else:
        raise ValueError("Unknown database chosen: {}".format(db.dbname))
    error_code = check_db_access(constants.dbconfig.copy())
    if error_code != 0:
        return False
    # check that all shared tables exist. No regard for contents.
    check_shared_tables(db)
    # check that the default demo subscription exists and is subscription 0
    check_default_subscription(db)
    # make sure the subscription-specific tables exist
    check_subscriptions(db)
    # ensure that each subscription has a settings row to go along with it and at least 1 default data source
    check_settings(db)
    # ensure that each datasource has all the appropriate ds-specific tables
    check_data_sources(db)
    # make sure the sessions table is there!
    check_sessions_table(db)

    return True


def check_and_fix_integrity(db=default_db, params=None):
    if params == None:
        params = constants.dbconfig.copy()
    error_code = check_and_fix_db_access(params)
    if error_code != 0:
        return False

    errors = check_shared_tables(db)
    if errors:
        fix_shared_tables(db, errors)

    if db.dbname == 'mysql':
        fix_UDF_MySQL(db)
    elif db.dbname == 'sqlite':
        fix_UDF_SQLite(db)
    else:
        raise ValueError("Unknown database chosen: {}".format(db.dbname))

    errors = check_default_subscription(db)
    if errors:
        fix_default_subscription(db, errors)

    errors = check_subscriptions(db)
    if errors:
        fix_subscriptions(db, errors)

    errors = check_settings(db)
    if errors:
        fix_settings(db, errors)

    errors = check_data_sources(db)
    if errors:
        fix_data_sources(db, errors)

    errors = check_sessions_table(db)
    if errors:
        fix_sessions_table(db, errors)

    return True
