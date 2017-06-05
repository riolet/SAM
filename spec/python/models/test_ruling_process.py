from spec.python import db_connection
from sam import common
import time
from sam.models import ruling_process as rp, rule

db = db_connection.db
sub_id = db_connection.default_sub
ds_full = db_connection.dsid_default


def reset_state():
    rp.__testing_only_reset_state()


def test_submit_job():
    old_spawner = rp.spawn_if_not_alive
    rp.spawn_if_not_alive = lambda: 0
    try:
        job = rp.RuleJob(1,1,1,1,[])
        job_id = rp.submit_job(job)
        assert isinstance(job_id, int)
        new_job_id = rp._QUEUE.get()
        assert new_job_id == job_id
        assert rp._NEXT_ID != job_id
        assert rp._JOBS[new_job_id] is job
    finally:
        rp.spawn_if_not_alive = old_spawner
        reset_state()


def test_check_job():
    old_spawner = rp.spawn_if_not_alive
    rp.spawn_if_not_alive = lambda: 0
    try:
        job = rp.RuleJob(1,1,1,1,[])
        job_id = rp.submit_job(job)
        assert rp.check_job(job.sub_id, job_id) == (job.status, job.completion)
        assert rp.check_job(job.sub_id + 1, job_id) == ("Missing", None)
        assert rp.check_job(job.sub_id, job_id + 1) == ("Missing", None)
    finally:
        rp.spawn_if_not_alive = old_spawner
        reset_state()


# This test should work, but fails unless there's a print statement in rp.ruling_process's while loop.
# I do not know why that makes a difference.
# Frequently getting:
#   Traceback (most recent call last):
#     File "/usr/lib/python2.7/multiprocessing/queues.py", line 268, in _feed
#       send(obj)
#   IOError: [Errno 32] Broken pipe
def xtest_ruling_process():
    # make 2+ jobs, with 2+ rules each
    # preload jobs list: {id: job}
    # preload queue with ids used in jobs list
    # run process
    rule1 = rule.Rule(1, True, 'test_rule1', 'test_rule1_desc', 'compromised.yml')
    rule2 = rule.Rule(2, True, 'test_rule2', 'test_rule2_desc', 'dos.yml')
    job1 = rp.RuleJob(sub_id, ds_full, 1, 2**32-1, [rule1, rule2])
    rule3 = rule.Rule(3, True, 'test_rule3', 'test_rule3_desc', 'portscan.yml')
    rule4 = rule.Rule(4, True, 'test_rule4', 'test_rule4_desc', 'suspicious.yml')
    job2 = rp.RuleJob(sub_id, ds_full, 1, 2**32-1, [rule3, rule4])

    old_processor = rp.RulesProcessor
    try:
        rp.RulesProcessor = db_connection.Mocker
        rp._JOBS = {1: job1, 2: job2}
        rp._QUEUE.put(1)
        rp._QUEUE.put(2)
        used_engine = rp.ruling_process(rp._QUEUE, stayalive=1)
        assert rp._QUEUE.empty()
        assert rp._JOBS == {}
        expected_calls = [
            ('process', (job1,), {}),
            ('process', (job2,), {}),
        ]
        assert used_engine.calls == expected_calls
    finally:
        rp.RulesProcessor = old_processor
        reset_state()


def test_evaluate_immediate_rule():
    rule1 = rule.Rule(1, True, 'test_rule1', 'test_rule1_desc', 'compromised.yml')
    rule2 = rule.Rule(2, True, 'test_rule2', 'test_rule2_desc', 'suspicious.yml')
    rule2.set_params({}, {
        'source_ip': '10.24.36.47',
        'dest_ip': '50.64.76.87',
        'port': 96
    })
    job1 = rp.RuleJob(sub_id, ds_full, 1, 2**32-1, [rule1, rule2])

    processor = rp.RulesProcessor(db)
    r1_alerts = processor.evaluate_immediate_rule(job1, rule1)
    assert len(r1_alerts) == 1
    assert r1_alerts[0]['src'] == 3340576552
    assert r1_alerts[0]['dst'] == 1701008954  # 101.99.86.58 (an IP from compromised.txt)

    r2_alerts = processor.evaluate_immediate_rule(job1, rule2)
    print(r2_alerts)
    assert len(r2_alerts) == 1
    assert r2_alerts[0]['src'] == 169354287
    assert r2_alerts[0]['dst'] == 843074647
    assert r2_alerts[0]['port'] == 96


def test_evaluate_periodic_rule():
    rule1 = rule.Rule(1, True, 'test_rule1', 'test_rule1_desc', 'dos.yml')
    rule1.set_params({}, {'threshold': '1'})
    rule2 = rule.Rule(2, True, 'test_rule2', 'test_rule2_desc', 'netscan.yml')
    rule2.set_params({}, {'threshold': '4'})
    rule3 = rule.Rule(3, True, 'test_rule3', 'test_rule3_desc', 'portscan.yml')
    rule3.set_params({}, {'threshold': '1'})

    job1 = rp.RuleJob(sub_id, ds_full, 1, 2**32-1, [rule1, rule2, rule3])
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


