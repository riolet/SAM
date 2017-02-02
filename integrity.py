import common
import web
import os
import json
import re
from MySQLdb import OperationalError
import models.subscriptions
import models.datasources

shared_tables = ['Settings', 'Ports', 'Datasources']
subscription_tables = ['Nodes', 'Tags', 'PortAliases']
datasource_tables = ['StagingLinks', 'Links', 'LinksIn', 'LinksOut', 'Syslog']
template_subscription_tables = map(lambda x: 's{acct}_' + x, subscription_tables)
template_tables_per_ds = map(lambda x: 's{acct}_ds{id}_' + x, datasource_tables)

db = common.db_quiet


def check_db_access():
    print("Checking database access...")
    params = common.dbconfig.params.copy()
    params.pop('db')
    errorCode = 0
    try:
        connection = web.database(**params)
        connection.query("USE samapper")
        print("\tDatabase access confirmed")
    except OperationalError as e:
        print("\tERROR: Database access error:")
        print("\t\tError {0}: {1}".format(e[0], e[1]))
        errorCode = e[0]
    return errorCode
def check_and_fix_db_access():
    print("Checking database access...")
    params = common.dbconfig.params.copy()
    db = params.pop('db')
    errorCode = 0
    connection = web.database(**params)
    try:
        connection.query("USE {0}".format(db))
        print("\tDatabase access confirmed")
    except OperationalError as e:
        errorCode = e[0]
        if e[0] == 1049:
            print("\tERROR: Database {0} not found. Creating.".format(db))
            try:
                connection.query("CREATE DATABASE IF NOT EXISTS samapper;")
                print("\tDatabase access restored.")
                errorCode = 0
            except:
                print("\tError creating database: ")
                print("\t\tError {0}: {1}".format(e[0], e[1]))
        elif e[0] == 1045:  # Access Denied for '%s'@'%s' (using password: (YES|NO))
            print("\tERROR: Unable to continue: invalid username or password")
            print("\tCheck your config file: dbconfig_local.py")
        else:
            print("\tERROR: Unable to continue: ")
            print("\t\tError {0}: {1}".format(e[0], e[1]))
    return errorCode


def check_shared_tables():
    print("Checking shared tables...")
    tables = [x.values()[0] for x in db.query("SHOW TABLES;")]
    missing_shared_tables = []
    for table in shared_tables:
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
        common.exec_sql(db, os.path.join(common.base_path, 'sql/setup_shared_tables.sql'))
        if "Ports" in missing_tables:
            print("\tPopulating port reference table with latest data")
            fill_port_table()
        print("\tShared Tables Fixed")
def fill_port_table():
    db.delete("Ports", "1=1")
    with open(os.path.join(common.base_path, 'sql/default_port_data.json'), 'rb') as f:
        port_data = json.loads("".join(f.readlines()))

    ports = port_data["ports"].values()
    for port in ports:
        if len(port['name']) > 10:
            port['name'] = port['name'][:10]
        if len(port['description']) > 255:
            port['description'] = port['description'][:255]
    db.multiple_insert('Ports', values=ports)


def check_settings():
    print("Checking settings...")
    settings = db.select("Settings")
    copies = len(settings)
    if copies == 0:
        print("\tERROR: No settings detected")
        errorCode = -1
    else:
        print("\tSettings exist")
        errorCode = 0
    return errorCode
def fix_settings(errorCode):
    print("Fixing settings...")
    if errorCode == 0:
        print("\tNo fix needed")
    elif errorCode == -1:
        print("\tCreating default demo profile.")
        subModel = models.subscriptions.Subscriptions()
        subModel.add_subscription(common.demo_subscription_id)
        print("\tDefault demo profile created.")
    else:
        print("ERROR: Cannot fix.")
        raise NotImplementedError()


def check_subscriptions():
    print("Checking subcription tables")
    subModel = models.subscriptions.Subscriptions()
    sub_ids = subModel.get_list()
    tables = [x.values()[0] for x in db.query("SHOW TABLES;") if re.match(r'^s\d+_[a-zA-Z0-9]+$', x.values()[0])]

    # TODO: catch tables that belong to subscriptions that don't exist any more.
    all_extra_tables = set()
    subs_missing_tables = set()

    for sid in sub_ids:
        # find all tables starting s#_*
        found_tables = set(filter(lambda x: re.match(r'^s{0}_[a-zA-Z0-9]+$'.format(sid), x), tables))
        expected_tables = set([x.format(acct=sid) for x in template_subscription_tables])
        missing_tables = expected_tables - found_tables
        extra_tables = found_tables - expected_tables
        if missing_tables:
            print("\tERROR: Subscription {sid} missing tables: {tables}".format(sid=sid, tables=", ".join(missing_tables)))
            subs_missing_tables.add(sid)
        if extra_tables:
            print("\tERROR: Subscription {sid} has extra tables: {tables}".format(sid=sid, tables=", ".join(extra_tables)))
            all_extra_tables |= extra_tables
    if not all_extra_tables and not subs_missing_tables:
        print("\tSubscription tables confirmed")
    return {'extra': all_extra_tables, 'malformed': subs_missing_tables}
def fix_subscriptions(errors):
    print("Fixing subscription tables")
    # remove extra tables
    if len(errors['extra']) > 0:
        print("\tRemoving extra tables")
        for table in errors['extra']:
            db.query("DROP TABLE {0};".format(table))
    # create tables for malformed subscriptions
    subModel = models.subscriptions.Subscriptions()
    if len(errors['malformed']) > 0:
        for id in errors['malformed']:
            print("\tRebuilding malformed tables for subscription {0}".format(id))
            subModel.create_subscription_tables(id)
    if not errors['extra'] and not errors['malformed']:
        print("\tNo fix needed")


def check_data_sources():
    print("Checking data sources...")
    subModel = models.subscriptions.Subscriptions()
    issues = {}
    all_tables = [tab.values()[0] for tab in db.query("SHOW TABLES;")]
    ds_table_pattern = re.compile(r'^s\d+_ds\d+_[a-zA-Z0-9]+$')
    ds_tables = set(filter(lambda x: re.match(ds_table_pattern, x), all_tables))
    known_subscriptions = subModel.get_list()

    # issue collections
    extra_tables = set()
    malformed_datasources = set()

    for sub_id in known_subscriptions:
        dsModel = models.datasources.Datasources(sub_id)
        for ds_id in dsModel.ds_ids:
            expected_tables = {tab.format(acct=sub_id, id=ds_id) for tab in template_tables_per_ds}
            if not expected_tables.issubset(ds_tables):
                print("\tERROR: Missing Tables for sub {0}, ds {1}".format(sub_id, ds_id))
                malformed_datasources.add((sub_id, ds_id))
            ds_tables -= expected_tables
    extra_tables |= ds_tables
    if len(extra_tables) > 0:
        print("\tERROR: Unused tables: {0}".format(" ".join(extra_tables)))

    if not malformed_datasources and not extra_tables:
        print("\tData sources verified")

    return {'malformed': malformed_datasources, 'unused': extra_tables}
def fix_data_sources(errors):
    print("Fixing data sources")
    if len(errors['unused']) > 0:
        print("\tDropping extra tables")
        for table in errors['unused']:
            db.query("DROP TABLE {0};".format(table))

    if len(errors['malformed']) > 0:
        print("\tRebuilding data source tables")
        for sub_id, ds_id in errors['malformed']:
            print("\tRebuilding malformed tables for subscription {0} datasource {1}".format(sub_id, ds_id))
            dsModel = models.datasources.Datasources(sub_id)
            dsModel.create_ds_tables(ds_id)

    if len(errors['malformed']) == 0 and len(errors['unused']) == 0:
        print('\tNo fix needed')
    else:
        print('\tData sources fixed')


def check_integrity():
    check_db_access()
    check_shared_tables()
    check_settings()
    check_subscriptions()
    check_data_sources()


def check_and_fix_integrity():
    errorCode = check_and_fix_db_access()
    if errorCode != 0:
        return

    errors = check_shared_tables()
    if errors:
        fix_shared_tables(errors)

    errors = check_settings()
    if errors:
        fix_settings(errors)

    errors = check_subscriptions()
    if errors:
        fix_subscriptions(errors)

    errors = check_data_sources()
    if errors:
        fix_data_sources(errors)
