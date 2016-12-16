import common
import dbaccess
import web
import os
import json
import re
from MySQLdb import OperationalError

shared_tables = ["Nodes", "Tags", "Datasources", "Ports", "PortAliases", "Settings"]
tables_per_ds = ["staging_Links", "staging_LinksIn", "staging_LinksOut", "Links", "LinksIn", "LinksOut", "Syslog"]
default_datasource_name = "default"
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
        print("\tDatabase access error:")
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
            print("\tDatabase {0} not found. Creating.".format(db))
            try:
                connection.query("CREATE DATABASE IF NOT EXISTS samapper;")
                print("\tDatabase access restored.")
                errorCode = 0
            except:
                print("\tError creating database: ")
                print("\t\tError {0}: {1}".format(e[0], e[1]))
        elif e[0] == 1045:  # Access Denied for '%s'@'%s' (using password: (YES|NO))
            print("\tUnable to continue: invalid username or password")
            print("\tCheck your config file: dbconfig_local.py")
        else:
            print("\tUnable to continue: ")
            print("\t\tError {0}: {1}".format(e[0], e[1]))
    return errorCode


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
        dbaccess.exec_sql(db, os.path.join(common.base_path, 'sql/setup_shared_tables.sql'))
        if "Ports" in missing_tables:
            print("\tPopulating port reference table with latest data")
            fill_port_table()
        print("\tShared Tables Fixed")


def fix_data_sources(issues):
    print("Fixing data sources")
    for table in issues.get('extra_tables', []):
        print("\tRemoving extra table {0}".format(table))
        db.query("DROP TABLE {0}".format(table))
    for ds in issues.get('known_missing', []):
        print("\tAdding data source (ds_{0}) known to be missing".format(ds))
        # add tables for data source
        dbaccess.create_ds_tables(ds)
    for ds in issues.get('real_unknown', []):
        print("\tRecording existing data source ds_{0}".format(ds))
        # add ds to `Datasources`
        db.insert("Datasources", id=ds, name="ds_{0}".format(ds))
    if "need_to_add" in issues:
        print("\tAdding default data source due to minimum requirement of 1.")
        dsname = issues['need_to_add']
        dbaccess.create_datasource(dsname)
    for ds in issues.get('malformed', []):
        print("\tRestoring tables for data source ds_{0}".format(ds))
        dbaccess.create_ds_tables(ds)

    print("\tData sources fixed")


def check_data_sources():
    print("Checking data sources...")
    issues = {}
    tables = [x.values()[0] for x in db.query("SHOW TABLES;")]
    known_datasources = list(db.query("SELECT * FROM Datasources"))
    known_ds_ids = set([unicode(ds['id']) for ds in known_datasources])
    real_datasources = set(re.findall(r"\bds_(\d+)_\w+", " ".join(tables)))
    known_missing = known_ds_ids.difference(real_datasources)
    real_unknown = real_datasources.difference(known_ds_ids)

    # check each data source to see if it is missing tables
    all_ds_ids = known_ds_ids.union(real_datasources)
    incomplete_datasources = set()
    for id in all_ds_ids:
        expected = ["ds_{0}_{1}".format(id, table) for table in tables_per_ds]
        for table in expected:
            if table not in tables:
                incomplete_datasources.add(id)

    # check for extra data source tables
    extra_tables = []
    for ds in real_datasources:
        prefix = "ds_{0}_".format(ds)
        ds_tables = [table[len(prefix):] for table in tables if table.startswith(prefix)]
        for table in ds_tables:
            if table not in tables_per_ds:
                extra_tables.append("{0}{1}".format(prefix, table))

    if known_missing:
        missing_names = [ds['name'] for ds in known_datasources if ds['id'] in known_missing]
        print("\tData sources missing: {0}".format(missing_names))
        issues['known_missing'] = known_missing
    if real_unknown:
        print("\tUnknown data sources discovered: {0}".format(real_unknown))
        issues['real_unknown'] = real_unknown
    if extra_tables:
        print("\tUnexpected data source tables: {0}".format(repr(extra_tables)))
        issues['extra_tables'] = extra_tables
    if incomplete_datasources:
        print("\tMalformed data source discovered: {0}".format(repr(incomplete_datasources)))
        issues['malformed'] = incomplete_datasources
    if not known_datasources and not real_unknown:
        print("\tNo data sources found. At least 1 required.")
        issues['need_to_add'] = default_datasource_name
    if not issues:
        print("\tData sources verified")
    return issues


def fix_settings(condition):
    print("Fixing settings...")
    if condition == 0:
        print("\tNo fix needed")
    else:
        print("\tCreating settings")
        db.delete("Settings", "1=1")
        id = db.select("Datasources", what="id", limit=1)[0]['id']
        db.insert("Settings", datasource=id)
        print("\tSettings fixed")


def check_settings():
    print("Checking settings...")
    settings = db.select("Settings")
    copies = len(settings)
    errorCode = 0
    if copies == 0:
        print("\tNo settings detected")
        errorCode = -1
    elif copies == 1:
        print("\tSettings validated")
        errorCode = 0
    else:
        print("\tMultiple settings detected")
        errorCode = copies
    return errorCode


def check_integrity():
    check_db_access()
    check_shared_tables()
    check_data_sources()
    check_settings()


def check_and_fix_integrity():
    check_and_fix_db_access()

    errors = check_shared_tables()
    if errors:
        fix_shared_tables(errors)

    errors = check_data_sources()
    if errors:
        fix_data_sources(errors)

    errors = check_settings()
    if errors:
        fix_settings(errors)
