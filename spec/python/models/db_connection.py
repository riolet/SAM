import constants
TEST_DATABASE = 'samapper_test'
constants.dbconfig['db'] = TEST_DATABASE
import common
import integrity
from MySQLdb import OperationalError
import models.datasources
import models.subscriptions
import web.template
import importers.import_base
import preprocess
import models.links
import models.nodes
from datetime import datetime
import time


def get_test_db_connection():
    db = common.db
    try:
        # dummy query to test db connection
        tables = db.query("SHOW TABLES")
    except OperationalError as e:
        print("Error establishing db connection.")
        print e
        create_test_database()
        try:
            # dummy query to test db connection
            tables = db.query("SHOW TABLES")
        except OperationalError as e:
            print("Error establishing db connection.")
            raise e

    rows = db.query("SELECT DATABASE();")
    row = rows.first()
    if row['DATABASE()'] == TEST_DATABASE:
        return db
    else:
        print("Database name doesn't match")
        raise ValueError("Test Database not available")


def create_test_database():
    # creates all the default tables and profile.
    integrity.check_and_fix_integrity()
    setup_datasources()


def setup_datasources():
    d = models.datasources.Datasources({}, constants.demo['id'])
    sources = d.datasources
    remaining = ['default', 'short', 'live']
    for ds in sources.values():
        if ds.name in remaining:
            remaining.remove(ds.name)
        else:
            d.remove_datasource(ds.id)
    for ds_name in remaining:
        d.create_datasource(ds_name)


def template_sql(path, *args):
    tmpl = web.template.Template(open(path).read())
    commands = common.parse_sql_string(unicode(tmpl(*args)), {})
    return commands


def make_timestamp(ts):
    d = datetime.strptime(ts, "%Y-%m-%d %H:%M")
    ts = time.mktime(d.timetuple())
    return int(ts)


def clear_network(db, sub, ds):
    l_model = models.links.Links(sub, ds)
    l_model.delete_connections()

    n_model = models.nodes.Nodes(sub)
    n_model.delete_custom_tags()
    n_model.delete_custom_envs()
    n_model.delete_custom_hostnames()
    db.query("DELETE FROM {table}".format(table=n_model.table_nodes))


def setup_network_links(db, sub_id, ds_id):
    clear_network(db, sub_id, ds_id)
    loader = importers.import_base.BaseImporter()
    loader.subscription = sub_id
    loader.datasource = ds_id
    processor = preprocess.Preprocessor(db, sub_id, ds_id)

    t = common.IPStringtoInt
    when1 = datetime(2016, 1, 17, 13, 24, 35)
    when2 = datetime(2017, 2, 18, 14, 25, 36)
    when3 = datetime(2018, 3, 19, 15, 26, 37)
    #          FROM        PORT          TO         PORT TIME PROTOCOL out in po pi  duration
    log_lines = [
        [t('10.20.30.40'), 12345, t('10.20.30.40'), 80,  when1, 'TCP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('10.20.30.41'), 80,  when2, 'TCP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('10.20.32.42'), 80,  when3, 'TCP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('10.20.32.43'), 80,  when3, 'TCP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('10.24.34.44'), 443, when1, 'TCP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('10.24.34.45'), 443, when2, 'TCP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('10.24.36.46'), 443, when3, 'TCP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('10.24.36.47'), 443, when3, 'TCP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('50.60.70.80'), 80,  when1, 'UDP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('50.60.70.81'), 80,  when2, 'UDP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('50.60.72.82'), 80,  when2, 'UDP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('50.60.72.83'), 80,  when3, 'UDP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('50.64.74.84'), 443, when1, 'UDP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('50.64.74.85'), 443, when1, 'UDP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('50.64.76.86'), 443, when2, 'UDP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('50.64.76.87'), 443, when3, 'UDP', 100, 0, 1, 0, 5],

        [t('59.69.79.89'), 12345, t('10.20.30.40'), 80,  when1,'ICMP', 100, 0, 1, 0, 5],
        [t('59.69.79.89'), 12345, t('10.20.30.40'), 443, when2,'ICMP', 100, 0, 1, 0, 5],
        [t('59.69.79.89'), 12345, t('10.20.30.40'), 80,  when3,'ICMP', 100, 0, 1, 0, 5],
    ]

    rows = [dict(zip(loader.keys, entry)) for entry in log_lines]
    count = len(rows)
    loader.insert_data(rows, count)
    processor.run_all()


def setup_node_extras():
    sub_id = constants.demo['id']
    commands = template_sql("./sql/test_data.sql", sub_id)
    for command in commands:
        print command


# immediately run, to ensure the test db is present.
get_test_db_connection()
default_sub = constants.demo['id']
ds_model = models.datasources.Datasources({}, default_sub)
dsid_default = 0
dsid_short = 0
dsid_live = 0
for k, v in ds_model.datasources.iteritems():
    if v['name'] == 'default':
        dsid_default = k
    if v['name'] == 'short':
        dsid_short = k
    if v['name'] == 'live':
        dsid_live = k
