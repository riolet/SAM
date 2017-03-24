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


def get_test_db_connection():
    db = common.db
    try:
        # dummy query to test db connection
        tables = db.query("SHOW TABLES")
    except OperationalError as e:
        print("Error establishing db connection.")
        print e
        integrity.check_and_fix_integrity()
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


def populate_test_database():
    # 3 data sources in base profile: "default", "short", "live"
    setup_datasources()

    setup_subscriptions()


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


def setup_subscriptions():
    s_model = models.subscriptions.Subscriptions()
    if not s_model.get_by_email('test@example.com'):
        s_model.create_subscription('test@example.com', 'Test Sub', 'Test Plan')


def template_sql(path, *args):
    tmpl = web.template.Template(open(path).read())
    commands = common.parse_sql_string(unicode(tmpl(*args)), {})
    return commands


def clear_network(db, sub, ds):
    l_model = models.links.Links(sub, ds)
    l_model.delete_connections()

    n_model = models.nodes.Nodes(sub)
    n_model.delete_custom_tags()
    n_model.delete_custom_envs()
    n_model.delete_custom_hostnames()
    db.query("DELETE FROM {table}".format(table=n_model.table_nodes))


def setup_network():
    sub_id = constants.demo['id']
    db = get_test_db_connection()
    ds_model = models.datasources.Datasources({}, sub_id)
    ds = ds_model.sorted_list()[0]
    ds_id = int(ds['id'])
    clear_network(db, sub_id, ds_id)
    loader = importers.import_base.BaseImporter()
    loader.subscription = sub_id
    loader.datasource = ds_id
    processor = preprocess.Preprocessor(db, sub_id, ds_id)

    # keys = [
    #    "src",
    #    "srcport",
    #    "dst",
    #    "dstport",
    #    "timestamp",
    #    "protocol",
    #    "bytes_sent",
    #    "bytes_received",
    #    "packets_sent",
    #    "packets_received",
    #    "duration",
    # ]
    t = common.IPStringtoInt
    when1 = datetime(2016, 1, 17, 13, 24, 35)
    when2 = datetime(2017, 2, 18, 14, 25, 36)
    when3 = datetime(2018, 3, 19, 15, 26, 37)
    log_lines = [
        [t('10.20.30.40'), 12345, t('10.20.30.40'), 80, when2, 'TCP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('10.20.30.41'), 80, when2, 'TCP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('10.20.32.42'), 80, when2, 'TCP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('10.20.32.43'), 80, when2, 'TCP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('10.24.34.44'), 80, when2, 'TCP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('10.24.34.45'), 80, when2, 'TCP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('10.24.36.46'), 80, when2, 'TCP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('10.24.36.47'), 80, when2, 'TCP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('50.60.70.80'), 80, when2, 'UDP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('50.60.70.81'), 80, when2, 'UDP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('50.60.72.82'), 80, when2, 'UDP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('50.60.72.83'), 80, when2, 'UDP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('50.64.74.84'), 80, when2, 'UDP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('50.64.74.85'), 80, when2, 'UDP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('50.64.76.86'), 80, when2, 'UDP', 100, 0, 1, 0, 5],
        [t('10.20.30.40'), 12345, t('50.64.76.87'), 80, when2, 'UDP', 100, 0, 1, 0, 5],
        [t('59.69.79.89'), 12345, t('10.20.30.40'), 80, when1, 'ICMP', 100, 0, 1, 0, 5],
        [t('59.69.79.89'), 12345, t('10.20.30.40'), 80, when2, 'ICMP', 100, 0, 1, 0, 5],
        [t('59.69.79.89'), 12345, t('10.20.30.40'), 80, when3, 'ICMP', 100, 0, 1, 0, 5],
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

