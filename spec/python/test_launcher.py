import sys
from spec.python import db_connection
from sam import constants, launcher, preprocess
from sam import server_webserver, server_collector, server_aggregator
from sam.importers import import_base
from sam.models.livekeys import LiveKeys
from sam.models.datasources import Datasources
from sam.models import nodes

db = db_connection.db
sub_id = db_connection.default_sub


def test_main():
    argv = ['launcher.py', '--target=test_dummy', '--badopt']
    assert launcher.main(argv) == 1

    argv = ['launcher.py', '--target=bad_target']
    assert launcher.main(argv) == 2

    argv = ['launcher.py', '--target=test_dummy']
    assert launcher.main(argv) == 3

    argv = ['launcher.py', '--target=import']
    assert launcher.main(argv) == 0


def test_parse_args():
    argv = 'launcher.py'.split()
    parsed, args = launcher.parse_args(argv)
    assert parsed == {
        'format': None,
        'port': None,
        'target': 'webserver',
        'whois': False,
        'wsgi': False,
        'dest': 'default',
        'sub': None
    }
    assert args == []

    argv = 'launcher.py --target=collector'.split()
    parsed, args = launcher.parse_args(argv)
    assert parsed == {
        'format': None,
        'port': None,
        'target': 'collector',
        'whois': False,
        'wsgi': False,
        'dest': 'default',
        'sub': None
    }
    assert args == []

    argv = 'launcher.py --target=webserver --wsgi'.split()
    parsed, args = launcher.parse_args(argv)
    assert parsed == {
        'format': None,
        'port': None,
        'target': 'webserver',
        'whois': False,
        'wsgi': True,
        'dest': 'default',
        'sub': None
    }
    assert args == []

    argv = 'launcher.py --target=aggregator wsgi'.split()
    parsed, args = launcher.parse_args(argv)
    assert parsed == {
        'format': None,
        'port': None,
        'target': 'aggregator',
        'whois': False,
        'wsgi': False,
        'dest': 'default',
        'sub': None
    }
    assert args == ['wsgi']

    argv = 'launcher.py --target=local --whois --format=asasyslog'.split()
    parsed, args = launcher.parse_args(argv)
    assert parsed == {
        'format': 'asasyslog',
        'port': None,
        'target': 'local',
        'whois': True,
        'wsgi': False,
        'dest': 'default',
        'sub': None
    }
    assert args == []

    argv = 'launcher.py --local --port=8421'.split()
    parsed, args = launcher.parse_args(argv)
    assert parsed == {
        'format': None,
        'port': '8421',
        'target': 'local',
        'whois': False,
        'wsgi': False,
        'dest': 'default',
        'sub': None
    }
    assert args == []

    argv = 'launcher.py --target=import --dest=newds --sub=4'.split()
    parsed, args = launcher.parse_args(argv)
    assert parsed == {
        'format': None,
        'port': None,
        'target': 'import',
        'whois': False,
        'wsgi': False,
        'dest': 'newds',
        'sub': '4'
    }
    assert args == []

    argv = 'launcher.py --target=collector_stream'.split()
    parsed, args = launcher.parse_args(argv)
    assert parsed == {
        'format': None,
        'port': None,
        'target': 'collector_stream',
        'whois': False,
        'wsgi': False,
        'dest': 'default',
        'sub': None
    }
    assert args == []

    argv = 'launcher.py --target=import ../data/syslog'.split()
    parsed, args = launcher.parse_args(argv)
    assert parsed == {
        'format': None,
        'port': None,
        'target': 'import',
        'whois': False,
        'wsgi': False,
        'dest': 'default',
        'sub': None
    }
    assert args == ['../data/syslog']


def test_launch_webserver():
    old_start_wsgi = server_webserver.start_wsgi
    old_start_server = server_webserver.start_server
    try:
        server_webserver.start_wsgi = db_connection.Mocker()
        server_webserver.start_server = db_connection.Mocker()

        parsed = {'port': '8040', 'wsgi': False}
        launcher.launch_webserver(parsed, None)
        assert len(server_webserver.start_wsgi.calls) == 0
        assert len(server_webserver.start_server.calls) == 1
        assert server_webserver.start_server.calls[0][2] == {'port': '8040'}

        parsed = {'port': None, 'wsgi': False}
        launcher.launch_webserver(parsed, None)
        assert len(server_webserver.start_wsgi.calls) == 0
        assert len(server_webserver.start_server.calls) == 2
        assert server_webserver.start_server.calls[1][2] == {'port': constants.webserver['listen_port']}

        parsed = {'port': None, 'wsgi': True}
        launcher.launch_webserver(parsed, None)
        assert len(server_webserver.start_wsgi.calls) == 1
        assert len(server_webserver.start_server.calls) == 2
    finally:
        server_webserver.start_wsgi = old_start_wsgi
        server_webserver.start_server = old_start_server


def test_launch_collector():
    old_collector = server_collector.Collector
    try:
        server_collector.Collector = db_connection.Mocker

        parsed = {'port': '8040', 'format': 'aws'}
        mocker = launcher.launch_collector(parsed, None)
        assert len(mocker.calls) == 1
        assert mocker.calls[0] == ('run', (), {'port': '8040', 'format': 'aws'})

        parsed = {'port': None, 'format': 'tcpdump'}
        mocker = launcher.launch_collector(parsed, None)
        assert len(mocker.calls) == 1
        assert mocker.calls[0] == ('run', (), {'port': constants.collector['listen_port'], 'format': 'tcpdump'})
    finally:
        server_collector.Collector = old_collector


def test_launch_collector_stream():
    old_collector = server_collector.Collector
    try:
        server_collector.Collector = db_connection.Mocker

        parsed = {'port': '8040', 'format': 'paloalto'}
        mocker = launcher.launch_collector_stream(parsed, None)
        assert len(mocker.calls) == 1
        assert mocker.calls[0][0] == 'run_streamreader'
        assert mocker.calls[0][1][0] is sys.stdin
        assert mocker.calls[0][2] == {'format': 'paloalto'}
    finally:
        server_collector.Collector = old_collector


def test_launch_aggregator():
    old_start_wsgi = server_aggregator.start_wsgi
    old_start_server = server_aggregator.start_server
    try:
        server_aggregator.start_wsgi = db_connection.Mocker()
        server_aggregator.start_server = db_connection.Mocker()

        parsed = {'port': '8040', 'wsgi': False}
        launcher.launch_aggregator(parsed, None)
        assert len(server_aggregator.start_wsgi.calls) == 0
        assert len(server_aggregator.start_server.calls) == 1
        assert server_aggregator.start_server.calls[0][2] == {'port': '8040'}

        parsed = {'port': None, 'wsgi': False}
        launcher.launch_aggregator(parsed, None)
        assert len(server_aggregator.start_wsgi.calls) == 0
        assert len(server_aggregator.start_server.calls) == 2
        assert server_aggregator.start_server.calls[1][2] == {'port': constants.aggregator['listen_port']}

        parsed = {'port': None, 'wsgi': True}
        launcher.launch_aggregator(parsed, None)
        assert len(server_aggregator.start_wsgi.calls) == 1
        assert len(server_aggregator.start_server.calls) == 2
    finally:
        server_aggregator.start_wsgi = old_start_wsgi
        server_aggregator.start_server = old_start_server


def test_launch_importer():
    # uses parsed_args: dest, sub, format
    # uses args for data file path
    old_get_importer = import_base.get_importer
    old_preprocess = preprocess.Preprocessor
    mocker = db_connection.Mocker()
    mocker._retval = True
    try:
        def gi_none(*args, **kwargs):
            return None
        def gi(*args, **kwargs):
            return mocker
        import_base.get_importer = gi
        preprocess.Preprocessor = db_connection.Mocker

        parsed = {
            'format': 'tcpdump',
            'dest': 'default',
            'sub': None
        }
        args = []
        assert launcher.launch_importer(parsed, args) == 4

        parsed = {
            'format': 'tcpdump',
            'dest': 'garbage',
            'sub': None
        }
        args = ['../data/syslog']
        assert launcher.launch_importer(parsed, args) == 6

        parsed = {
            'format': 'tcpdump',
            'dest': '0',
            'sub': None
        }
        args = ['../data/syslog']
        assert launcher.launch_importer(parsed, args) == 6

        parsed = {
            'format': 'unicorn',
            'dest': 'default',
            'sub': None
        }
        args = ['../data/syslog']
        import_base.get_importer = gi_none
        assert launcher.launch_importer(parsed, args) == 7
        import_base.get_importer = gi

        parsed = {
            'format': 'tcpdump',
            'dest': 'default',
            'sub': None
        }
        args = ['../data/syslog']

        proc_mock = launcher.launch_importer(parsed, args)
        assert len(mocker.calls) == 2
        assert mocker.calls[0][0] == 'validate_file'
        assert mocker.calls[1][0] == 'import_file'
        assert proc_mock.calls == [('run_all', (), {})]
    finally:
        import_base.get_importer = old_get_importer
        preprocess.Preprocessor = old_preprocess


def test_create_local_settings():
    dsid_rows = db.query("SELECT datasource FROM Settings WHERE subscription={}".format(sub_id))
    dsid = dsid_rows.first()['datasource']
    livekeys = db.query("SELECT * FROM {} WHERE datasource={} AND subscription={} ".format(LiveKeys.table_livekeys, dsid, sub_id))
    livekeys = list(livekeys)
    assert len(livekeys) == 0

    settings_rows = db.query("SELECT flat, ar_active, ar_interval FROM {} WHERE id={} AND subscription={}".format(Datasources.TABLE, dsid, sub_id))
    settings = settings_rows.first()
    assert settings.flat == 0
    assert settings.ar_active == 0
    assert settings.ar_interval != 30

    try:
        k = launcher.create_local_settings(db, sub_id)
        livekeys = db.query("SELECT * FROM {} WHERE datasource={} AND subscription={} ".format(LiveKeys.table_livekeys, dsid, sub_id))
        livekeys = list(livekeys)
        assert len(livekeys) == 1
        assert livekeys[0]['access_key'] == constants.collector['upload_key']
        assert k == constants.collector['upload_key']

        settings_rows = db.query("SELECT flat, ar_active, ar_interval FROM {} WHERE id={} AND subscription={}".format(Datasources.TABLE, dsid, sub_id))
        settings = settings_rows.first()
        assert settings.flat == 1
        assert settings.ar_active == 1
        assert settings.ar_interval == 30
    finally:
        db.query("UPDATE {} SET flat=0, ar_active=0, ar_interval=300 WHERE id={} AND subscription={}".format(Datasources.TABLE, dsid, sub_id))
        db.query("DELETE FROM {}".format(LiveKeys.table_livekeys))


def test_check_database():
    pass


def test_launch_whois_service():
    pass


def xtest_launch_localmode():
    # parsed_args used: format, whois, sub, port (webserver)
    # should run launch_aggregator as a process
    # should run collector.run_streamreader in a new process
    # should run whois (if specified)
    # should launch webserver
    # I don't know how to test this.

    old_la = launcher.launch_aggregator
    old_crs = server_collector.Collector
    old_who = nodes.WhoisService
    old_web = launcher.launch_webserver
    w_mocker = db_connection.Mocker()
    sc_mocker = db_connection.Mocker()
    try:
        def m_who(*args, **kwargs):
            return w_mocker
        def m_sc(*args, **kwargs):
            return sc_mocker
        launcher.launch_aggregator = db_connection.Mocker()
        server_collector.Collector = m_sc
        nodes.WhoisService = m_who
        launcher.launch_webserver = db_connection.Mocker()

        parsed_args = {'format': 'tcpdump', 'whois': True, 'sub': None, 'port': None}
        args = []
        launcher.launch_localmode(parsed_args, args)

        assert len(launcher.launch_aggregator.calls) == 1
        assert len(sc_mocker.calls) == 1
        assert len(w_mocker.calls) == 1
        assert len(launcher.launch_webserver.calls) == 1
    finally:
        launcher.launch_aggregator = old_la
        server_collector.Collector = old_crs
        nodes.WhoisService = old_who
        launcher.launch_webserver = old_web

