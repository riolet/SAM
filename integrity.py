import os
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

db = common.db_quiet


def check_db_access():
    # type: () -> int
    """
    Attempt to access the database.

    :return: 0 if successful else MySQL error code
    """
    print("Checking database access...")
    params = constants.dbconfig.copy()
    params.pop('db')
    error_code = 0
    try:
        connection = web.database(**params)
        connection.query("USE {0}".format(constants.dbconfig['db']))
        print("\tDatabase access confirmed")
    except OperationalError as e:
        print("\tERROR: Database access error:")
        print("\t\tError {0}: {1}".format(e[0], e[1]))
        error_code = e[0]
    return error_code


def check_and_fix_db_access():
    print("Checking database access...")
    params = constants.dbconfig.copy()
    db_name = params.pop('db')
    error_code = 0
    connection = web.database(**params)
    try:
        connection.query("USE {0}".format(constants.dbconfig['db']))
        print("\tDatabase access confirmed")
    except OperationalError as e:
        error_code = e[0]
        if e[0] == 1049:
            print("\tERROR: Database {0} not found. Creating.".format(db))
            try:
                connection.query("CREATE DATABASE IF NOT EXISTS {0};".format(constants.dbconfig['db']))
                print("\tDatabase access restored.")
                error_code = 0
            except:
                print("\tError creating database: ")
                print("\t\tError {0}: {1}".format(e[0], e[1]))
        elif e[0] == 1045:  # Access Denied for '%s'@'%s' (using password: (YES|NO))
            print("\tERROR: Unable to continue: invalid username or password")
            print("\tCheck your config file: default.cfg")
        else:
            print("\tERROR: Unable to continue: ")
            print("\t\tError {0}: {1}".format(e[0], e[1]))
    return error_code


def check_shared_tables():
    # type: () -> [str]
    """
    Check that all shared tables exist with no regard for contents or structure.

    :return: A list of expected tables that aren't found.
    """
    print("Checking shared tables...")
    tables = [x.values()[0] for x in db.query("SHOW TABLES;")]
    missing_shared_tables = []
    for table in constants.shared_tables:
        if table not in tables:
            missing_shared_tables.append(table)
    if missing_shared_tables:
        print("\tShared tables missing: {0}".format(repr(missing_shared_tables)))
    else:
        print("\tShared tables confirmed")
    return missing_shared_tables


def fix_shared_tables(missing_tables):
    print("Fixing shared tables...")
    if not missing_tables:
        print("\tNo tables to fix")
    else:
        print("\tRestoring missing tables: {0}".format(repr(missing_tables)))
        common.exec_sql(db, os.path.join(constants.base_path, 'sql/setup_shared_tables.sql'))
        if "Ports" in missing_tables:
            print("\tPopulating port reference table with latest data")
            fill_port_table()
        print("\tShared Tables Fixed")


def fill_port_table():
    db.delete("Ports", "1=1")
    with open(os.path.join(constants.base_path, 'sql/default_port_data.json'), 'rb') as f:
        port_data = json.loads("".join(f.readlines()))

    ports = port_data["ports"].values()
    for port in ports:
        if len(port['name']) > 10:
            port['name'] = port['name'][:10]
        if len(port['description']) > 255:
            port['description'] = port['description'][:255]
    db.multiple_insert('Ports', values=ports)


def check_default_subscription():
    """
    :return: 0 if no problems, -1 if default subscription is missing, -2 if default subscription id is taken.
    """
    print("Checking default subscription")
    sub_model = models.subscriptions.Subscriptions()
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


def fix_default_subscription(errors):
    print("Fixing default subscription")
    if errors == 0:
        print("\tNo fix needed")
    elif errors == -1:
        print("\tCreating default subscription")
        sub_model = models.subscriptions.Subscriptions()
        sub_model.create_default_subscription()
    else:
        raise NotImplementedError("Cannot fix bad default subscription")


def check_subscriptions():
    # type: () -> { str: {str} }
    """
    Check that each subscription has appropriate subscription-specific tables.

    :return: a dictionary containing issues identified in the subscriptions. dictionary may contain keys:
        "extra": a set of all extraneous subscription tables
        "malformed": a set of all subscriptions that are missing one or more tables.
    """
    print("Checking subscription tables")
    sub_model = models.subscriptions.Subscriptions()
    sub_ids = sub_model.get_id_list()
    all_sub_tables = [x.values()[0] for x in db.query("SHOW TABLES;")
                      if re.match(r'^s\d+_[a-zA-Z0-9]+$', x.values()[0])]

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


def fix_subscriptions(errors):
    """
    :param errors: a dictionary containing issues identified in the subscriptions. dictionary may contain keys:
        "extra": a set of all extraneous subscription tables
        "malformed": a set of all subscriptions that are missing one or more tables.
    """
    print("Fixing subscription tables")
    # remove extra tables
    if len(errors['extra']) > 0:
        print("\tRemoving extra tables")
        for table in errors['extra']:
            db.query("DROP TABLE {0};".format(table))
    # create tables for malformed subscriptions
    sub_model = models.subscriptions.Subscriptions()
    if len(errors['malformed']) > 0:
        for sid in errors['malformed']:
            print("\tRebuilding malformed tables for subscription {0}".format(sid))
            sub_model.create_subscription_tables(sid)
    if not any(map(len, errors.values())):
        print("\tNo fix needed")
    else:
        print("\tSubscriptions fixed")


def check_settings():
    # type: () -> { str: {str} }
    """
    Ensure that each subscription has a settings row to go along with it and at least 1 default data source

    :return: a dictionary containing issues identified in the settings. Dictionary may contain keys:
        "extra": a set of all extraneous settings rows
        "missing": a set of all subscriptions that are missing their settings row
    """
    print("Checking settings...")
    sub_model = models.subscriptions.Subscriptions()
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


def fix_settings(errors):
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
            settings_model = models.settings.Settings({}, sub_id)
            settings_model.create()

    if not any(map(len, errors.values())):
        print("\tNo fix needed")
    else:
        print("\tSettings fixed")


def check_data_sources():
    # type: () -> { str: {str} }
    """
    Ensure that each datasource has all the appropriate ds-specific tables

    :return: a dictionary containing issues identified in the settings. Dictionary may contain keys:
        "unused": a set of all tables without an owner datasource
        "malformed": a set of all datasources that are missing some of their tables
    """
    print("Checking data sources...")
    sub_model = models.subscriptions.Subscriptions()
    all_tables = [tab.values()[0] for tab in db.query("SHOW TABLES;")]
    ds_table_pattern = re.compile(r'^s\d+_ds\d+_[a-zA-Z0-9]+$')
    ds_tables = set(filter(lambda x: re.match(ds_table_pattern, x), all_tables))
    known_subscriptions = sub_model.get_id_list()

    # issue collections
    extra_tables = set()
    malformed_datasources = set()

    for sub_id in known_subscriptions:
        ds_model = models.datasources.Datasources({}, sub_id)
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


def fix_data_sources(errors):
    """

    :param errors: a dictionary containing issues identified in the settings. Dictionary may contain keys:
        "unused": a set of all tables without an owner datasource
        "malformed": a set of all datasources that are missing some of their tables
    """
    print("Fixing data sources")
    if len(errors['unused']) > 0:
        print("\tDropping extra tables")
        for table in errors['unused']:
            db.query("DROP TABLE {0};".format(table))

    if len(errors['malformed']) > 0:
        print("\tRebuilding data source tables")
        for sub_id, ds_id in errors['malformed']:
            print("\tRebuilding malformed tables for subscription {0} datasource {1}".format(sub_id, ds_id))
            ds_model = models.datasources.Datasources({}, sub_id)
            ds_model.create_ds_tables(ds_id)

    if len(errors['malformed']) == 0 and len(errors['unused']) == 0:
        print('\tNo fix needed')
    else:
        print('\tData sources fixed')


def check_integrity():
    # ensure we can access the database
    error_code = check_db_access()
    if error_code != 0:
        return
    # check that all shared tables exist. No regard for contents.
    check_shared_tables()
    # check that the default demo subscription exists and is subscription 0
    check_default_subscription()
    # make sure the subscription-specific tables exist
    check_subscriptions()
    # ensure that each subscription has a settings row to go along with it and at least 1 default data source
    check_settings()
    # ensure that each datasource has all the appropriate ds-specific tables
    check_data_sources()


def check_and_fix_integrity():
    error_code = check_and_fix_db_access()
    if error_code != 0:
        return

    errors = check_shared_tables()
    if errors:
        fix_shared_tables(errors)

    errors = check_default_subscription()
    if errors:
        fix_default_subscription(errors)

    errors = check_subscriptions()
    if errors:
        fix_subscriptions(errors)

    errors = check_settings()
    if errors:
        fix_settings(errors)

    errors = check_data_sources()
    if errors:
        fix_data_sources(errors)
