import os
import re
import json
import logging
import traceback
from sam import constants
from sam import common
import web
from MySQLdb import OperationalError
from sam.models.subscriptions import Subscriptions
from sam.models.datasources import Datasources
from sam.models.settings import Settings
from sam.models.security.rules import Rules
logger = logging.getLogger(__name__)
template_subscription_tables = map(lambda x: 's{acct}_' + x, constants.subscription_tables)
template_tables_per_ds = map(lambda x: 's{acct}_ds{id}_' + x, constants.datasource_tables)


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

def get_all_subs(db):
    rows = db.select("Subscriptions", what="subscription")
    subs = [row['subscription'] for row in rows]
    return subs

def get_all_dss(db):
    rows = db.select('Datasources', what='subscription, id')
    dss = [{'sub_id': row['subscription'], 'ds_id': row['id']} for row in rows]
    return dss


# ==================  DB Access ====================


def check_db_access_MySQL(params):
    # type: () -> int
    """
    Attempt to access the database.

    :return: 0 if successful else MySQL error code
    """
    logger.debug("Checking database access...")
    db_name = params.pop('db')
    error_code = 0
    try:
        connection = web.database(**params)
        connection.query("USE {0}".format(db_name))
        logger.debug("\tDatabase access confirmed")
    except OperationalError as e:
        logger.warning("\tDatabase access error:")
        logger.warning("\t\t{0}: {1}".format(e[0], e[1]))
        error_code = e[0]
    return error_code


def check_db_access_SQLite(params):
    # type: () -> int
    """
    Attempt to access the database.

    :return: 0 if successful else non-zero error code
    """
    logger.debug("Checking database access...")
    error_code = 0
    try:
        params.pop('host', None)
        params.pop('port', None)
        params.pop('user', None)
        params.pop('pw', None)
        connection = web.database(**params)
        common.sqlite_udf(connection)
        connection.query('SELECT SQLITE_VERSION()')
        logger.debug("\tDatabase access confirmed")
    except Exception as e:
        logger.warning("\tDatabase access error:")
        logger.warning("\t\t{0}: {1}".format(e.args, e.message))
        error_code = 1
    return error_code


def check_and_fix_db_access(params):
    if params['dbn'] == 'sqlite':
        return check_and_fix_db_access_SQLite(params)
    else:
        return check_and_fix_db_access_MySQL(params)


def check_and_fix_db_access_MySQL(params):
    logger.debug("Checking database access...")
    db_name = params.pop('db')
    error_code = 0
    connection = web.database(**params)
    try:
        connection.query("USE {0}".format(db_name))
        logger.debug("\tDatabase access confirmed")
    except OperationalError as e:
        error_code = e[0]
        if e[0] == 1049:
            logger.debug("\tDatabase {0} not found. Creating.".format(db_name))
            try:
                connection.query("CREATE DATABASE IF NOT EXISTS {0};".format(db_name))
                logger.info("\tDatabase access restored.")
                error_code = 0
            except:
                logger.critical("\tError creating database: ")
                logger.critical("\t\tError {0}: {1}".format(e[0], e[1]))
        elif e[0] == 1045:  # Access Denied for '%s'@'%s' (using password: (YES|NO))
            logger.critical("\tUnable to access database: invalid username or password")
            logger.critical("\t  Check your config file or environment variables.")
        else:
            logger.critical("\tUnable to access database: ")
            logger.critical("\t\t{0}: {1}".format(e[0], e[1]))
    return error_code


def check_and_fix_db_access_SQLite(params):
    logger.debug("Checking database access...")
    error_code = 0
    try:
        params.pop('host', None)
        params.pop('port', None)
        params.pop('user', None)
        params.pop('pw', None)
        connection = web.database(**params)
        common.sqlite_udf(connection)
        connection.query('SELECT SQLITE_VERSION()')
        logger.debug("\tDatabase access confirmed")
    except Exception as e:
        logger.critical("\tDatabase access error:")
        logger.critical("\t\t{0}: {1}".format(e.args, e.message))
        error_code = 1
    return error_code


# ==================  Shared Tables  ====================


def check_shared_tables(db):
    # type: (web.DB) -> [str]
    """
    Check that all shared tables exist with no regard for contents or structure.

    :return: A list of expected tables that aren't found.
    """
    logger.debug("Checking shared tables...")
    tables = get_table_names(db)
    missing_shared_tables = []
    for table in constants.shared_tables:
        if table not in tables:
            missing_shared_tables.append(table)
    if missing_shared_tables:
        logger.warning("\tShared tables missing: {0}".format(repr(missing_shared_tables)))
    else:
        logger.debug("\tShared tables confirmed")
    return missing_shared_tables


def fix_shared_tables(db, missing_tables):
    logger.debug("Fixing shared tables...")
    if not missing_tables:
        logger.debug("\tNo tables to fix")
    else:
        logger.info("\tRestoring missing tables: {0}".format(repr(missing_tables)))
        with db.transaction():
            if db.dbname == 'sqlite':
                common.exec_sql(db, os.path.join(constants.base_path, 'sql/setup_shared_tables_sqlite.sql'))
            else:
                common.exec_sql(db, os.path.join(constants.base_path, 'sql/setup_shared_tables_mysql.sql'))
            if "Ports" in missing_tables:
                logger.debug("\tPopulating port reference table with latest data")
                fill_port_table(db)
        logger.info("\tShared Tables Fixed")


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


# ==================  Subscription Tables  ====================


def check_default_subscription(db):
    """
    :return: 0 if no problems, -1 if default subscription is missing, -2 if default subscription is broken.
    """
    logger.debug("Checking default subscription")
    sub_model = Subscriptions(db)
    subs = sub_model.get_all()
    errors = -1
    for sub in subs:
        if sub['email'] == constants.subscription['default_email']:
            if sub['plan'] != 'admin' \
                    or sub['name'] != constants.subscription['default_name'] \
                    or sub['active'] != 1:
                errors = -2
                logger.warning("\tDefault subscription malformed")
            else:
                errors = 0
                logger.debug("\tDefault subscription confirmed")
            break
    if errors == -1:
        logger.warning("\tDefault subscription is missing")
    return errors


def fix_default_subscription(db, errors):
    logger.debug("Fixing default subscription")
    if errors == 0:
        logger.debug("\tNo fix needed")
    elif errors == -1:
        logger.info("\tCreating default subscription")
        sub_model = Subscriptions(db)
        sub_model.create_default_subscription()
    elif errors == -2:
        logger.info("\tFixing default subscription")
        sub_model = Subscriptions(db)
        sub = sub_model.get_by_email(constants.subscription['default_email'])
        succeeded = sub_model.set(sub['subscription'], plan='admin', active=1, name=constants.subscription['default_name'])
        if not succeeded:
            raise ValueError("Failed to fix default subscription")
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
    logger.debug("Checking subscription tables")
    sub_model = Subscriptions(db)
    sub_ids = sub_model.get_id_list()
    all_sub_tables = get_table_names(db)
    all_sub_tables = filter(lambda x: re.match(r'^s\d+_[a-zA-Z0-9]+$', x), all_sub_tables)

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
            logger.warning("\tSubscription {sid} missing tables: {tables}"
                  .format(sid=sid, tables=", ".join(missing_tables)))
            subs_missing_tables.add(sid)
        if extra_tables:
            logger.warning("\tSubscription {sid} has extra tables: {tables}"
                  .format(sid=sid, tables=", ".join(extra_tables)))
            all_extra_tables |= extra_tables
    if not all_extra_tables and not subs_missing_tables:
        logger.debug("\tSubscription tables confirmed")
        return {}
    # return {'extra': all_extra_tables, 'malformed': subs_missing_tables}
    # extra tables may belong to a plugin. Do not delete them immediately.
    return {'malformed': subs_missing_tables}


def fix_subscriptions(db, errors):
    """
    :param errors: a dictionary containing issues identified in the subscriptions. dictionary may contain keys:
        "extra": a set of all extraneous subscription tables
        "malformed": a set of all subscriptions that are missing one or more tables.
    """
    logger.debug("Fixing subscription tables")
    # remove extra tables
    if 'extra' in errors and len(errors['extra']) > 0:
        logger.info("\tRemoving extra tables")
        for table in errors['extra']:
            db.query("DROP TABLE {0};".format(table))
    # create tables for malformed subscriptions
    sub_model = Subscriptions(db)
    if 'malformed' in errors and len(errors['malformed']) > 0:
        for sid in errors['malformed']:
            logger.info("\tRebuilding malformed tables for subscription {0}".format(sid))
            sub_model.create_subscription_tables(sid)
    if not any(map(len, errors.values())):
        logger.debug("\tNo fix needed")
    else:
        logger.info("\tSubscriptions fixed")


def fix_default_rules(db):
    # TODO: move this into Subscriptions:new()
    sub_model = Subscriptions(db)
    sub = sub_model.get_by_email(constants.subscription['default_email'])
    sub_id = sub['subscription']
    r_model = Rules(db, sub_id)
    r_model.add_rule('compromised.yml', 'Compromised', 'Flag traffic to known compromised hosts', {})


def check_settings(db):
    """
    Ensure that each subscription has a settings row to go along with it and at least 1 default data source
    :type db: web.DB
    :return: a dictionary containing issues identified in the settings. Dictionary may contain keys:
        "extra": a set of all extraneous settings rows
        "missing": a set of all subscriptions that are missing their settings row
    """
    logger.debug("Checking settings...")
    sub_model = Subscriptions(db)
    expected = set(sub_model.get_id_list())

    settings_rows = list(db.select("Settings"))
    found = set([s['subscription'] for s in settings_rows])

    missing = expected - found
    extra = found - expected

    issues = {}
    if missing:
        logger.warning("\tSettings missing for subscriptions: {0}".format(missing))
        issues['missing'] = missing
    if extra:
        logger.warning("\tSettings discovered for subscriptions that don't exist: {0}".format(extra))
        issues['extra'] = extra
    if not extra and not missing:
        logger.debug("\tSettings confirmed")
    return issues


def fix_settings(db, errors):
    """
    :param errors: a dictionary containing issues identified in the settings. Dictionary may contain keys:
        "extra": a set of all extraneous settings rows
        "missing": a set of all subscriptions that are missing their settings row
    """
    logger.debug("Fixing settings...")
    if 'extra' in errors and len(errors['extra']) > 0:
        logger.info("\tDeleting unused settings")
        for table in errors['extra']:
            db.query("DROP TABLE {0};".format(table))
    if 'missing' in errors and len(errors['missing']) > 0:
        for sub_id in errors['missing']:
            logger.info("\tRepairing settings for {0}".format(sub_id))
            settings_model = Settings(db, {}, sub_id)
            settings_model.create()

    if not any(map(len, errors.values())):
        logger.debug("\tNo fix needed")
    else:
        logger.info("\tSettings fixed")


# ==================  Datasource Tables  ====================


def check_data_sources(db):
    """
    Ensure that each datasource has all the appropriate ds-specific tables
    :type db: web.DB
    :return: a dictionary containing issues identified in the settings. Dictionary may contain keys:
        "unused": a set of all tables without an owner datasource
        "malformed": a set of all datasources that are missing some of their tables
    """
    logger.debug("Checking data sources...")
    sub_model = Subscriptions(db)
    all_tables = get_table_names(db)
    ds_table_pattern = re.compile(r'^s\d+_ds\d+_[a-zA-Z0-9]+$')
    ds_tables = set(filter(lambda x: re.match(ds_table_pattern, x), all_tables))
    known_subscriptions = sub_model.get_id_list()

    # issue collections
    extra_tables = set()
    malformed_datasources = set()

    for sub_id in known_subscriptions:
        ds_model = Datasources(db, {}, sub_id)
        for ds_id in ds_model.ds_ids:
            expected_tables = {tab.format(acct=sub_id, id=ds_id) for tab in template_tables_per_ds}
            if not expected_tables.issubset(ds_tables):
                logger.warning("\tMissing Tables for sub {0}, ds {1}".format(sub_id, ds_id))
                malformed_datasources.add((sub_id, ds_id))
            ds_tables -= expected_tables
    extra_tables |= ds_tables
    if len(extra_tables) > 0:
        logger.warning("\tUnused tables: {0}".format(" ".join(extra_tables)))

    if not malformed_datasources and not extra_tables:
        logger.debug("\tData sources confirmed")
        return {}

    # return {'malformed': malformed_datasources, 'unused': extra_tables}
    # unused tables may belong to a plugin. Do not delete them immediately.
    return {'malformed': malformed_datasources}


def fix_data_sources(db, errors):
    """
    :type db: web.DB
    :type errors: dict[str, list[str]]
    :param errors: a dictionary containing issues identified in the settings. Dictionary may contain keys:
        "unused": a set of all tables without an owner datasource
        "malformed": a set of all datasources that are missing some of their tables
    """
    logger.debug("Fixing data sources")
    if 'unused' in errors and len(errors['unused']) > 0:
        logger.info("\tDropping extra tables")
        for table in errors['unused']:
            db.query("DROP TABLE {0};".format(table))

    if 'malformed' in errors and len(errors['malformed']) > 0:
        logger.debug("\tRebuilding data source tables")
        for sub_id, ds_id in errors['malformed']:
            logger.info("\tRebuilding malformed tables for subscription {0} datasource {1}".format(sub_id, ds_id))
            ds_model = Datasources(db, {}, sub_id)
            ds_model.create_ds_tables(ds_id)

    if not any(map(len, errors.values())):
        logger.debug('\tNo fix needed')
    else:
        logger.info('\tData sources fixed')


# ==================  Session Table  ====================


def check_sessions_table(db):
    """
    Check if the session table is missing.
    :type db: web.DB
    :return: True if the session table is missing. False otherwise.
    :rtype: bool
    """
    logger.debug("Checking session storage...")
    tables = get_table_names(db)
    is_missing = 'sessions' not in tables
    if is_missing:
        logger.warning("\tSession table missing")
    else:
        logger.debug("\tSession storage confirmed")
    return is_missing


def fix_sessions_table(db, is_missing):
    logger.debug("Fixing session storage...")
    if is_missing:
        common.exec_sql(db, os.path.join(constants.base_path, 'sql/sessions.sql'))
        logger.info("\tFixed sessions.")
    else:
        logger.debug("\tNo fix needed.")


# ==================  Plugin Tables  ====================


def check_plugins(db):
    plugins = constants.plugin_models
    # assume each plugin is type sam.models.base.DBPlugin
    any_issues = False
    logger.debug("Checking plugin models...")
    for plugin in plugins:
        if bool(plugin.checkIntegrity(db)) is False:
            logger.debug("\tplugin {} verified.".format(plugin))
        else:
            logger.warning("\tplugin {} has errors.".format(plugin))
            any_issues = True
    return any_issues


def fix_plugins(db, errors):
    plugins = constants.plugin_models
    any_issues = False
    logger.debug("Fixing plugin models...")
    for plugin in plugins:
        errors = plugin.checkIntegrity(db)
        if errors:
            logger.info("\tfixing {}".format(plugin))
            try:
                success = plugin.fixIntegrity(db, errors)
                if not success:
                    any_issues = True
                    logger.error("\tunable to fix {}".format(plugin))
            except Exception as e:
                logger.error(e)
                any_issues = True
                logger.error("\tunable to fix {}".format(plugin))
    return any_issues


# ==================  Suite  ====================


def check_integrity(db=None):
    healthy = True
    if db is None:
        db = common.db_quiet
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
    healthy = healthy and bool(check_shared_tables(db) == [])
    if not healthy:
        return healthy
    # check that the default demo subscription exists and is subscription 0
    healthy = healthy and bool(check_default_subscription(db) == 0)
    # make sure the subscription-specific tables exist
    healthy = healthy and all([len(x) == 0 for x in check_subscriptions(db).values()])
    # ensure that each subscription has a settings row to go along with it and at least 1 default data source
    healthy = healthy and check_settings(db) == {}
    # ensure that each datasource has all the appropriate ds-specific tables
    healthy = healthy and all([len(x) == 0 for x in check_data_sources(db).values()])
    # make sure the sessions table is there!
    healthy = healthy and check_sessions_table(db) is False
    # make sure all plugin models are setup
    healthy = healthy and check_plugins(db) is False

    return healthy


def check_and_fix_integrity(db=None, params=None):
    if db is None:
        db = common.db_quiet
    if params is None:
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

    try:
        errors = check_default_subscription(db)
        if errors:
            fix_default_subscription(db, errors)
        new_sub = bool(errors)
        errors = check_subscriptions(db)
        if errors:
            fix_subscriptions(db, errors)
        if new_sub:
            fix_default_rules(db)

        errors = check_settings(db)
        if errors:
            fix_settings(db, errors)
    except:
        traceback.print_exc()
        raise

    errors = check_data_sources(db)
    if errors:
        fix_data_sources(db, errors)

    errors = check_sessions_table(db)
    if errors:
        fix_sessions_table(db, errors)

    errors = check_plugins(db)
    if errors:
        fix_plugins(db, errors)

    return True
