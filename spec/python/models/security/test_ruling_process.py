import time
import traceback
from datetime import datetime
from decimal import Decimal
from spec.python import db_connection
from sam import common
from sam.models.security import rule
from sam.models.security import ruling_process as rp
from sam.models.security import alerts

db = db_connection.db
sub_id = db_connection.default_sub
ds_full = db_connection.dsid_default


def reset_state():
    rp.__testing_only_reset_state()


def test_rulejob():
    rule1 = rule.Rule(1, True, 'test_rule1', 'test_rule1_desc', 'compromised.yml')
    rule2 = rule.Rule(2, True, 'test_rule2', 'test_rule2_desc', 'dos.yml')
    job1 = rp.RuleJob(sub_id, ds_full, datetime.fromtimestamp(1), datetime.fromtimestamp(2**32-1), [rule1, rule2])
    job1.id = 1
    j1_params = job1.export()
    j1_rebuilt = rp.RuleJob.rebuild(j1_params)
    assert j1_rebuilt == job1

    rule3 = rule.Rule(3, True, 'test_rule3', 'test_rule3_desc', 'portscan.yml')
    rule4 = rule.Rule(4, True, 'test_rule4', 'test_rule4_desc', 'suspicious.yml')
    job2 = rp.RuleJob(sub_id, ds_full, datetime.fromtimestamp(1), datetime.fromtimestamp(2**32-1), [rule3, rule4])
    job2.id = 2
    j2_params = job2.export()
    j2_rebuilt = rp.RuleJob.rebuild(j2_params)
    assert j2_rebuilt == job2

    assert j2_rebuilt != j1_rebuilt


def test_submit_job():
    old_spawner = rp.spawn_if_not_alive
    rp.spawn_if_not_alive = lambda: 0
    try:
        reset_state()
        job = rp.RuleJob(1,1,1,1,[])
        job_id = rp.submit_job(job)
        assert isinstance(job_id, int)
        new_job_id = rp._QUEUE.get()
        assert new_job_id == job_id
        assert rp._NEXT_ID != job_id
        assert rp._JOBS[new_job_id] is job
    except:
        traceback.print_exc()
    finally:
        rp.spawn_if_not_alive = old_spawner


def test_check_job():
    old_spawner = rp.spawn_if_not_alive
    rp.spawn_if_not_alive = lambda: 0
    try:
        reset_state()
        job = rp.RuleJob(1,1,1,1,[])
        job_id = rp.submit_job(job)
        assert rp.check_job(job.sub_id, job_id) == (job.status, job.completion)
        assert rp.check_job(job.sub_id + 1, job_id) == ("Missing", None)
        assert rp.check_job(job.sub_id, job_id + 1) == ("Missing", None)
    except:
        traceback.print_exc()
    finally:
        rp.spawn_if_not_alive = old_spawner


def test_reset_globals():
    reset_state()
    assert len(rp._JOBS) == 0
    assert rp._QUEUE.empty()
    rp._JOBS[355] = 'abcdef'
    rp._QUEUE.put(355)
    rp._JOBS[358] = 'zyxwvut'
    rp._QUEUE.put(358)
    assert len(rp._JOBS) == 2
    assert not rp._QUEUE.empty()
    rp.reset_globals()
    assert len(rp._JOBS) == 0
    assert rp._QUEUE.empty()


def test_ruling_process():
    # make 2+ jobs, with 2+ rules each
    # preload jobs list: {id: job}
    # preload queue with ids used in jobs list
    # run process
    rule1 = rule.Rule(1, True, 'test_rule1', 'test_rule1_desc', 'compromised.yml')
    rule2 = rule.Rule(2, True, 'test_rule2', 'test_rule2_desc', 'dos.yml')
    job1 = rp.RuleJob(sub_id, ds_full, datetime.fromtimestamp(1), datetime.fromtimestamp(2**32-1), [rule1, rule2])
    rule3 = rule.Rule(3, True, 'test_rule3', 'test_rule3_desc', 'portscan.yml')
    rule4 = rule.Rule(4, True, 'test_rule4', 'test_rule4_desc', 'suspicious.yml')
    job2 = rp.RuleJob(sub_id, ds_full, datetime.fromtimestamp(1), datetime.fromtimestamp(2**32-1), [rule3, rule4])

    old_processor = rp.RulesProcessor
    try:
        reset_state()
        rp.RulesProcessor = db_connection.Mocker
        rp._JOBS = rp._MANAGER.dict()
        rp._JOBS[1] = job1.export()
        rp._JOBS[2] = job2.export()
        rp._QUEUE.put(1)
        rp._QUEUE.put(2)
        time.sleep(0.1) # test fails without this.
        used_engine = rp.ruling_process(rp._QUEUE, db, stayalive=0.1)
        assert rp._QUEUE.empty()
        assert len(rp._JOBS) == 0
        assert len(used_engine.calls) == 2
        assert used_engine.calls[0][1][0].export()[:6] == job1.export()[:6]
        assert used_engine.calls[1][1][0].export()[:6] == job2.export()[:6]
    finally:
        rp.RulesProcessor = old_processor


def test_evaluate_immediate_rule():
    rule1 = rule.Rule(1, True, 'test_rule1', 'test_rule1_desc', 'compromised.yml')
    rule2 = rule.Rule(2, True, 'test_rule2', 'test_rule2_desc', 'suspicious.yml')
    rule2.set_exposed_params({
        'source_ip': '10.24.36.47',
        'dest_ip': '50.64.76.87',
        'port': 96
    })
    job1 = rp.RuleJob(sub_id, ds_full, datetime.fromtimestamp(1), datetime.fromtimestamp(2**31-1), [rule1, rule2])

    processor = rp.RulesProcessor(db)
    r1_alerts = processor.evaluate_immediate_rule(job1, rule1)
    assert len(r1_alerts) == 1
    assert r1_alerts[0]['src'] == 3340576552
    assert r1_alerts[0]['dst'] == 1701008954  # 101.99.86.58 (an IP from compromised.txt)

    r2_alerts = processor.evaluate_immediate_rule(job1, rule2)
    assert len(r2_alerts) == 1
    assert r2_alerts[0]['src'] == 169354287
    assert r2_alerts[0]['dst'] == 843074647
    assert r2_alerts[0]['port'] == 96


def test_evaluate_periodic_rule():
    rule1 = rule.Rule(1, True, 'test_rule1', 'test_rule1_desc', 'dos.yml')
    rule1.set_exposed_params({'threshold': '1'})
    rule2 = rule.Rule(2, True, 'test_rule2', 'test_rule2_desc', 'netscan.yml')
    rule2.set_exposed_params({'threshold': '4'})
    rule3 = rule.Rule(3, True, 'test_rule3', 'test_rule3_desc', 'portscan.yml')
    rule3.set_exposed_params({'threshold': '1'})

    job1 = rp.RuleJob(sub_id, ds_full, datetime.fromtimestamp(1), datetime.fromtimestamp(2**31-1), [rule1, rule2, rule3])
    processor = rp.RulesProcessor(db)

    r1_alerts = processor.evaluate_immediate_rule(job1, rule1)
    assert len(r1_alerts) == 3
    dsts = [row['dst'] for row in r1_alerts]
    assert sorted(dsts) == [842811474, 843074132, 1846812200]

    r2_alerts = processor.evaluate_immediate_rule(job1, rule2)
    assert len(r2_alerts) == 3
    srcs = [row['src'] for row in r2_alerts]
    assert srcs == [1846812200, 1846812200, 1846812200]
    times = [int(time.mktime(row['timestamp'].timetuple())) for row in r2_alerts]
    assert times == [1453065600, 1487456700, 1521498300]

    # curiously, this rule is operating correctly and has the same results as the above rule
    # under the same partial tests in this testing environment.
    r3_alerts = processor.evaluate_immediate_rule(job1, rule3)
    assert len(r3_alerts) == 3
    srcs = [row['src'] for row in r3_alerts]
    assert srcs == [1846812200, 1846812200, 1846812200]
    times = [int(time.mktime(row['timestamp'].timetuple())) for row in r3_alerts]
    assert times == [1453065600, 1487456700, 1521498300]


def test_trigger_actions():
    rule1 = rule.Rule(1, True, 'test_rule1', 'test_rule1_desc', 'compromised.yml')
    rule1.set_action_params({'alert_active': 'true', 'email_active': 'true', 'sms_active': 'true'})

    rule2 = rule.Rule(2, True, 'test_rule2', 'test_rule2_desc', 'suspicious.yml')
    rule2.set_exposed_params({
        'source_ip': '10.24.36.47',
        'dest_ip': '50.64.76.87',
        'port': 96
    })
    rule2.set_action_params({'alert_active': 'true', 'email_active': 'false', 'sms_active': 'true'})

    rule3 = rule.Rule(3, True, 'test_rule3', 'test_rule3_desc', 'dos.yml')
    rule3.set_exposed_params({'threshold': '1'})
    rule3.set_action_params({'alert_active': 'false', 'email_active': 'true', 'sms_active': 'true'})

    rule4 = rule.Rule(4, True, 'test_rule4', 'test_rule4_desc', 'netscan.yml')
    rule4.set_exposed_params({'threshold': '4'})
    rule4.set_action_params({'alert_active': 'true', 'email_active': 'true', 'sms_active': 'false'})

    processor = rp.RulesProcessor(db)
    mock_alert = db_connection.Mocker()
    mock_email = db_connection.Mocker()
    mock_sms = db_connection.Mocker()
    processor.trigger_alert = mock_alert
    processor.trigger_email = mock_email
    processor.trigger_sms = mock_sms

    job1 = rp.RuleJob(sub_id, ds_full, datetime.fromtimestamp(5), datetime.fromtimestamp(2 ** 31 - 5), [rule1])
    job2 = rp.RuleJob(sub_id, ds_full, datetime.fromtimestamp(5), datetime.fromtimestamp(2 ** 31 - 5), [rule2])
    job34 = rp.RuleJob(sub_id, ds_full, datetime.fromtimestamp(5), datetime.fromtimestamp(2 ** 31 - 5), [rule3, rule4])

    processor.process(job1)
    assert len(mock_alert.calls) == 1
    assert len(mock_email.calls) == 1
    assert len(mock_sms.calls) == 1

    processor.process(job2)
    assert len(mock_alert.calls) == 2
    assert len(mock_email.calls) == 1
    assert len(mock_sms.calls) == 2

    processor.process(job34)
    assert len(mock_alert.calls) == 5
    assert len(mock_email.calls) == 3
    assert len(mock_sms.calls) == 3


def test_trigger_email():
    r1_matches = [
        {'src': 3340576552L, 'protocol': u'TCP', 'links': 1L, 'timestamp': datetime(2016, 1, 17, 13, 20),
         'dst': 1701008954L, 'packets_received': 0L, 'bytes_sent': 100L, 'duration': 5L, 'packets_sent': 1L,
         'bytes_received': 0L, 'port': 80L}
    ]
    r2_matches = [
        {'src': 3340576552L, 'protocol': u'TCP', 'links': 1L, 'timestamp': datetime(2016, 1, 17, 13, 20),
         'dst': 1701008954L, 'packets_received': 0L, 'bytes_sent': 100L, 'duration': 5L, 'packets_sent': 1L,
         'bytes_received': 0L, 'port': 80L}
    ]
    r3_matches = [
        {'src[hosts]': 1L, 'conn[links]': Decimal('2'), 'conn[ports]': 1L, 'conn[protocol]': 2L,
         'timestamp': datetime(2016, 1, 17, 13, 20), 'dst': 1846812200L},
        {'src[hosts]': 1L, 'conn[links]': Decimal('2'), 'conn[ports]': 2L, 'conn[protocol]': 2L,
         'timestamp': datetime(2017, 3, 24, 1, 55), 'dst': 843074132L},
        {'src[hosts]': 1L, 'conn[links]': Decimal('2'), 'conn[ports]': 2L, 'conn[protocol]': 2L,
         'timestamp': datetime(2017, 3, 24, 6, 0), 'dst': 842811474L},
    ]
    r4_matches = [
        {'src': 1846812200L, 'dst[hosts]': 5L, 'conn[links]': Decimal('5'), 'conn[ports]': 2L,
         'conn[protocol]': 2L, 'timestamp': datetime(2016, 1, 17, 13, 20)},
        {'src': 1846812200L, 'dst[hosts]': 5L, 'conn[links]': Decimal('5'), 'conn[ports]': 2L,
         'conn[protocol]': 2L, 'timestamp': datetime(2017, 2, 18, 14, 25)},
        {'src': 1846812200L, 'dst[hosts]': 6L, 'conn[links]': Decimal('6'), 'conn[ports]': 2L,
         'conn[protocol]': 2L, 'timestamp': datetime(2018, 3, 19, 15, 25)}
    ]
    rule1 = rule.Rule(1, True, 'test_rule1', 'test_rule1_desc', 'compromised.yml')
    rule1.set_action_params({'alert_active': 'true', 'email_active': 'true', 'sms_active': 'true'})

    rule2 = rule.Rule(2, True, 'test_rule2', 'test_rule2_desc', 'suspicious.yml')
    rule2.set_exposed_params({
        'source_ip': '10.24.36.47',
        'dest_ip': '50.64.76.87',
        'port': 96
    })
    rule2.set_action_params({'alert_active': 'true', 'email_active': 'false', 'sms_active': 'true'})

    rule3 = rule.Rule(3, True, 'test_rule3', 'test_rule3_desc', 'dos.yml')
    rule3.set_exposed_params({'threshold': '1'})
    rule3.set_action_params({'alert_active': 'false', 'email_active': 'true', 'sms_active': 'true'})

    rule4 = rule.Rule(4, True, 'test_rule4', 'test_rule4_desc', 'netscan.yml')
    rule4.set_exposed_params({'threshold': '4'})
    rule4.set_action_params({'alert_active': 'true', 'email_active': 'true', 'sms_active': 'false'})
    job1 = rp.RuleJob(sub_id, ds_full, datetime.fromtimestamp(5), datetime.fromtimestamp(2 ** 31 - 5), [rule1])
    job2 = rp.RuleJob(sub_id, ds_full, datetime.fromtimestamp(5), datetime.fromtimestamp(2 ** 31 - 5), [rule2])
    job34 = rp.RuleJob(sub_id, ds_full, datetime.fromtimestamp(5), datetime.fromtimestamp(2 ** 31 - 5), [rule3, rule4])

    processor = rp.RulesProcessor(db)
    old_sendmail = common.sendmail
    try:
        common.sendmail = db_connection.Mocker()
        action_email = {'type': 'email', 'address': 'abc@zyx.com', 'subject': '[SAM] Special Email Subject'}
        processor.trigger_email(job1, rule1, action_email, r1_matches, rule1.get_translation_table())
        action_email = {'type': 'email', 'address': 'email2', 'subject': 'sub2'}
        processor.trigger_email(job2, rule2, action_email, r2_matches, rule2.get_translation_table())
        action_email = {'type': 'email', 'address': 'email3', 'subject': 'sub3'}
        processor.trigger_email(job34, rule3, action_email, r3_matches, rule3.get_translation_table())
        action_email = {'type': 'email', 'address': 'email4', 'subject': 'sub4'}
        processor.trigger_email(job34, rule4, action_email, r4_matches, rule4.get_translation_table())
        assert len(common.sendmail.calls) == 4
        assert common.sendmail.calls[0][1][0] == 'abc@zyx.com'
        assert common.sendmail.calls[0][1][1] == '[SAM] Special Email Subject'
        assert common.sendmail.calls[1][1][0] == 'email2'
        assert common.sendmail.calls[1][1][1] == 'sub2'
        assert common.sendmail.calls[2][1][0] == 'email3'
        assert common.sendmail.calls[2][1][1] == 'sub3'
        assert common.sendmail.calls[3][1][0] == 'email4'
        assert common.sendmail.calls[3][1][1] == 'sub4'
    except:
        traceback.print_exc()
        assert False
    finally:
        common.sendmail = old_sendmail


def test_trigger_sms():
    r1_matches = [
        {'src': 3340576552L, 'protocol': u'TCP', 'links': 1L, 'timestamp': datetime(2016, 1, 17, 13, 20),
         'dst': 1701008954L, 'packets_received': 0L, 'bytes_sent': 100L, 'duration': 5L, 'packets_sent': 1L,
         'bytes_received': 0L, 'port': 80L}
    ]
    r2_matches = [
        {'src': 3340576552L, 'protocol': u'TCP', 'links': 1L, 'timestamp': datetime(2016, 1, 17, 13, 20),
         'dst': 1701008954L, 'packets_received': 0L, 'bytes_sent': 100L, 'duration': 5L, 'packets_sent': 1L,
         'bytes_received': 0L, 'port': 80L}
    ]
    r3_matches = [
        {'src[hosts]': 1L, 'conn[links]': Decimal('2'), 'conn[ports]': 1L, 'conn[protocol]': 2L,
         'timestamp': datetime(2016, 1, 17, 13, 20), 'dst': 1846812200L},
        {'src[hosts]': 1L, 'conn[links]': Decimal('2'), 'conn[ports]': 2L, 'conn[protocol]': 2L,
         'timestamp': datetime(2017, 3, 24, 1, 55), 'dst': 843074132L},
        {'src[hosts]': 1L, 'conn[links]': Decimal('2'), 'conn[ports]': 2L, 'conn[protocol]': 2L,
         'timestamp': datetime(2017, 3, 24, 6, 0), 'dst': 842811474L},
    ]
    r4_matches = [
        {'src': 1846812200L, 'dst[hosts]': 5L, 'conn[links]': Decimal('5'), 'conn[ports]': 2L,
         'conn[protocol]': 2L, 'timestamp': datetime(2016, 1, 17, 13, 20)},
        {'src': 1846812200L, 'dst[hosts]': 5L, 'conn[links]': Decimal('5'), 'conn[ports]': 2L,
         'conn[protocol]': 2L, 'timestamp': datetime(2017, 2, 18, 14, 25)},
        {'src': 1846812200L, 'dst[hosts]': 6L, 'conn[links]': Decimal('6'), 'conn[ports]': 2L,
         'conn[protocol]': 2L, 'timestamp': datetime(2018, 3, 19, 15, 25)}
    ]
    rule1 = rule.Rule(1, True, 'test_rule1', 'test_rule1_desc', 'compromised.yml')
    rule1.set_action_params({'alert_active': 'true', 'email_active': 'true', 'sms_active': 'true'})

    rule2 = rule.Rule(2, True, 'test_rule2', 'test_rule2_desc', 'suspicious.yml')
    rule2.set_exposed_params({
        'source_ip': '10.24.36.47',
        'dest_ip': '50.64.76.87',
        'port': 96
    })
    rule2.set_action_params({'alert_active': 'true', 'email_active': 'false', 'sms_active': 'true'})

    rule3 = rule.Rule(3, True, 'test_rule3', 'test_rule3_desc', 'dos.yml')
    rule3.set_exposed_params({'threshold': '1'})
    rule3.set_action_params({'alert_active': 'false', 'email_active': 'true', 'sms_active': 'true'})

    rule4 = rule.Rule(4, True, 'test_rule4', 'test_rule4_desc', 'netscan.yml')
    rule4.set_exposed_params({'threshold': '4'})
    rule4.set_action_params({'alert_active': 'true', 'email_active': 'true', 'sms_active': 'false'})
    job1 = rp.RuleJob(sub_id, ds_full, datetime.fromtimestamp(5), datetime.fromtimestamp(2 ** 31 - 5), [rule1])
    job23 = rp.RuleJob(sub_id, ds_full, datetime.fromtimestamp(5), datetime.fromtimestamp(2 ** 31 - 5), [rule2, rule3])
    job4 = rp.RuleJob(sub_id, ds_full, datetime.fromtimestamp(5), datetime.fromtimestamp(2 ** 31 - 5), [rule4])

    processor = rp.RulesProcessor(db)
    old_sendsms = common.sendsms
    try:
        common.sendsms = db_connection.Mocker()
        action_sms = {'type': 'sms', 'number': '1 123 456 7890', 'message': '[SAM] Special SMS Message'}
        processor.trigger_sms(job1, rule1, action_sms, r1_matches, rule1.get_translation_table())
        action_sms = {'type': 'sms', 'number': 'num2', 'message': 'msg2'}
        processor.trigger_sms(job23, rule2, action_sms, r2_matches, rule2.get_translation_table())
        action_sms = {'type': 'sms', 'number': 'num3', 'message': 'msg3'}
        processor.trigger_sms(job23, rule3, action_sms, r3_matches, rule3.get_translation_table())
        action_sms = {'type': 'sms', 'number': 'num4', 'message': 'msg4'}
        processor.trigger_sms(job4, rule4, action_sms, r4_matches, rule4.get_translation_table())
        assert len(common.sendsms.calls) == 4
        assert common.sendsms.calls[0][1][0] == '1 123 456 7890'
        assert common.sendsms.calls[0][1][1] == '[SAM] Special SMS Message'
        assert common.sendsms.calls[1][1][0] == 'num2'
        assert common.sendsms.calls[1][1][1] == 'msg2'
        assert common.sendsms.calls[2][1][0] == 'num3'
        assert common.sendsms.calls[2][1][1] == 'msg3'
        assert common.sendsms.calls[3][1][0] == 'num4'
        assert common.sendsms.calls[3][1][1] == 'msg4'
    finally:
        common.sendsms = old_sendsms


def test_trigger_alert():
    r1_matches = [
        {'src': 3340576552L, 'protocol': u'TCP', 'links': 1L, 'timestamp': datetime(2016, 1, 17, 13, 20),
         'dst': 1701008954L, 'packets_received': 0L, 'bytes_sent': 100L, 'duration': 5L, 'packets_sent': 1L,
         'bytes_received': 0L, 'port': 80L}
    ]
    r2_matches = [
        {'src': 3340576552L, 'protocol': u'TCP', 'links': 1L, 'timestamp': datetime(2016, 1, 17, 13, 20),
         'dst': 1701008954L, 'packets_received': 0L, 'bytes_sent': 100L, 'duration': 5L, 'packets_sent': 1L,
         'bytes_received': 0L, 'port': 80L}
    ]
    r3_matches = [
        {'src[hosts]': 1L, 'conn[links]': Decimal('2'), 'conn[ports]': 1L, 'conn[protocol]': 2L,
         'timestamp': datetime(2016, 1, 17, 13, 20), 'dst': 1846812200L},
        {'src[hosts]': 1L, 'conn[links]': Decimal('2'), 'conn[ports]': 2L, 'conn[protocol]': 2L,
         'timestamp': datetime(2017, 3, 24, 1, 55), 'dst': 843074132L},
        {'src[hosts]': 1L, 'conn[links]': Decimal('2'), 'conn[ports]': 2L, 'conn[protocol]': 2L,
         'timestamp': datetime(2017, 3, 24, 6, 0), 'dst': 842811474L},
    ]
    r4_matches = [
        {'src': 1846812200L, 'dst[hosts]': 5L, 'conn[links]': Decimal('5'), 'conn[ports]': 2L,
         'conn[protocol]': 2L, 'timestamp': datetime(2016, 1, 17, 13, 20)},
        {'src': 1846812200L, 'dst[hosts]': 5L, 'conn[links]': Decimal('5'), 'conn[ports]': 2L,
         'conn[protocol]': 2L, 'timestamp': datetime(2017, 2, 18, 14, 25)},
        {'src': 1846812200L, 'dst[hosts]': 6L, 'conn[links]': Decimal('6'), 'conn[ports]': 2L,
         'conn[protocol]': 2L, 'timestamp': datetime(2018, 3, 19, 15, 25)}
    ]
    rule1 = rule.Rule(1, True, 'test_rule1', 'test_rule1_desc', 'compromised.yml')
    rule1.set_action_params({'alert_active': 'true', 'email_active': 'true', 'sms_active': 'true'})

    rule2 = rule.Rule(2, True, 'test_rule2', 'test_rule2_desc', 'suspicious.yml')
    rule2.set_exposed_params({
        'source_ip': '10.24.36.47',
        'dest_ip': '50.64.76.87',
        'port': 96
    })
    rule2.set_action_params({'alert_active': 'true', 'email_active': 'false', 'sms_active': 'true'})

    rule3 = rule.Rule(3, True, 'test_rule3', 'test_rule3_desc', 'dos.yml')
    rule3.set_exposed_params({'threshold': '1'})
    rule3.set_action_params({'alert_active': 'false', 'email_active': 'true', 'sms_active': 'true'})

    rule4 = rule.Rule(4, True, 'test_rule4', 'test_rule4_desc', 'netscan.yml')
    rule4.set_exposed_params({'threshold': '4'})
    rule4.set_action_params({'alert_active': 'true', 'email_active': 'true', 'sms_active': 'false'})
    job1 = rp.RuleJob(sub_id, ds_full, datetime.fromtimestamp(5), datetime.fromtimestamp(2 ** 31 - 5), [rule1])
    job23 = rp.RuleJob(sub_id, ds_full, datetime.fromtimestamp(5), datetime.fromtimestamp(2 ** 31 - 5), [rule2, rule3])
    job4 = rp.RuleJob(sub_id, ds_full, datetime.fromtimestamp(5), datetime.fromtimestamp(2 ** 31 - 5), [rule4])

    processor = rp.RulesProcessor(db)
    m_alert = alerts.Alerts(db, sub_id)
    m_alert.clear()
    assert m_alert.count() == 0

    action_alert = {'type': 'alert', 'severity': '8', 'label': 'Special Label'}
    processor.trigger_alert(job1, rule1, action_alert, r1_matches[0], rule1.get_translation_table())
    action_alert = {'type': 'alert', 'severity': '7', 'label': 'label2'}
    processor.trigger_alert(job23, rule2, action_alert, r2_matches[0], rule2.get_translation_table())
    action_alert = {'type': 'alert', 'severity': '6', 'label': 'label3'}
    processor.trigger_alert(job23, rule3, action_alert, r3_matches[0], rule3.get_translation_table())
    processor.trigger_alert(job23, rule3, action_alert, r3_matches[1], rule3.get_translation_table())
    processor.trigger_alert(job23, rule3, action_alert, r3_matches[2], rule3.get_translation_table())
    action_alert = {'type': 'alert', 'severity': '5', 'label': 'label4'}
    processor.trigger_alert(job4, rule4, action_alert, r4_matches[0], rule4.get_translation_table())
    processor.trigger_alert(job4, rule4, action_alert, r4_matches[1], rule4.get_translation_table())
    processor.trigger_alert(job4, rule4, action_alert, r4_matches[2], rule4.get_translation_table())
    assert m_alert.count() == 8
    new_alerts = m_alert.get(alerts.AlertFilter(order="asc", sort="id"))
    alert_severities = [al['severity'] for al in new_alerts]
    assert alert_severities == [8, 7, 6, 6, 6, 5, 5, 5]
    m_alert.clear()