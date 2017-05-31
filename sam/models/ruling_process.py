import re
import time
from datetime import datetime
import multiprocessing
import multiprocessing.queues  # for IDE (pycharm type helper)
import web
from sam import common, constants
from sam.models import rule, rule_parser

_RULES_PROCESS = None
_QUEUE = multiprocessing.Queue()
_JOBS = {}
_NEXT_ID = 1
# get own connection to DB
_DB, _DB_QUIET = common.get_db(constants.dbconfig.copy())


class RuleJob(object):
    def __init__(self, subscription_id, datasource_id, start, end, ruleset):
        """
        For use with the RuleProcessor subprocess
        :param subscription_id: the subscription this job applies to
         :type subscription_id: int
        :param datasource_id: the datasource in which to analyze traffic
         :type datasource_id: int
        :param start: the start of the analysis timerange 
         :type start: int
        :param end: the end of the analysis timerange
         :type end: int
        :param ruleset: a list of rules to check traffic against
         :type ruleset: list[ rule.Rule ]
        """
        self.sub_id = subscription_id
        self.ds_id = datasource_id
        self.time_start = start
        self.time_end = end
        self.rules = ruleset
        self.id = 0  # id to check on this job
        self.status = "Created."  # Created, Queued, Running rule_n / num_rules, Complete
        self.completion = 0  #number from 0 to 1 representing the completion of this job.


def submit_job(job):
    """
    :param job:
     :type job: RuleJob
    :return: 
    """
    global _NEXT_ID, _JOBS, _QUEUE
    # give the job a status (queued)
    job.id = _NEXT_ID
    _NEXT_ID += 1
    # add the job to the job list
    _JOBS[job.id] = job
    # insert the job_id into the queue
    _QUEUE.put(job.id)
    # if the rules process isn't running, start it.
    spawn_if_not_alive()
    # return the job_id
    return job.id


def spawn_if_not_alive():
    global _RULES_PROCESS
    if _RULES_PROCESS is None or not _RULES_PROCESS.is_alive():
        _RULES_PROCESS = multiprocessing.Process(target=ruling_process, args=(_QUEUE,))
        _RULES_PROCESS.start()


def check_job(sub_id, job_id):
    # include sub_id for security purposes
    job = _JOBS.get(job_id, None)
    if job is None or job.sub_id != sub_id:
        return "Missing", None
    return job.status, job.completion


def reset_globals():
    global _JOBS, _QUEUE
    _JOBS = {}
    _QUEUE = multiprocessing.Queue()


def ruling_process(queue):
    """
    :param queue:
     :type queue: multiprocessing.queues.Queue
    :return: 
    """
    global _JOBS
    engine = RulesProcessor(_DB_QUIET)
    while not queue.empty():
        job_id = queue.get()
        engine.process(_JOBS[job_id])
        if queue.empty():
            time.sleep(10)
    reset_globals()


class RulesProcessor(object):
    COND_REGEX = re.compile(r"^(?P<rule>(?:(?P<dir>src|dst|src or dst|src and dst)\s+)(?P<type>host|port))\s+(?P<value>\S+|in \S+)$")
    TABLE_FORMAT = "s{sub_id}_ds{ds_id}_Links"

    def __init__(self, db):
        """
        :param db:
         :type db: web.DB
        """
        self.db = db

    def evaluate_rule(self, job, translations, conditions):
        alerts_discovered = []

        parser = rule_parser.RuleParser(translations, conditions)

        where = parser.sql

        print("    prepared_condition: WHERE {}".format(where))

        table = RulesProcessor.TABLE_FORMAT.format(sub_id=job.sub_id, ds_id=job.ds_id)
        rows = list(self.db.select(table,where=where))
        alerts_discovered.extend(rows)
        return alerts_discovered

    def process(self, job):
        """
        :param job:
         :type job: RuleJob
        :return: 
        """
        # regularly update job status and completion
        # process the rules sequentially
        job.status = 'In Progress'
        print('{}: Starting job on s{}_ds{}, from {} to {}'.format(job.status, job.sub_id, job.ds_id, job.time_start,
                                                                   job.time_end))

        for i, rule in enumerate(job.rules):
            job.status = 'Running rule {} of {}'.format(i+1, len(job.rules))
            if not rule.is_active():
                print('  {}: Skipping rule {} ({})'.format(job.status, rule.get_name(), rule.nice_path()))
                continue

            conditions = rule.get_conditions()
            actions = rule.get_actions()
            translation_table = rule.get_translation_table()
            print('  {}: Working on rule {} ({})'.format(job.status, rule.get_name(), rule.nice_path()))
            print('    Rule conditions: {}'.format(conditions))
            print('    Rule actions:')
            for action in actions:
                print('      {}'.format(repr(action)))

            alert_rows = self.evaluate_rule(job, translation_table, conditions)
            print('    {} alerts discovered,'.format(len(alert_rows)))
            for alert in alert_rows:
                print('      {}: {} -> {}:{} using {}'.format(datetime.fromtimestamp(int(time.mktime(alert.timestamp.timetuple()))), common.IPtoString(alert.src), common.IPtoString(alert.dst), alert.port, alert.protocol))

        job.status = "Complete"
        print('{}: Finished job on s{}_ds{}, from {} to {}'.format(job.status, job.sub_id, job.ds_id, job.time_start,
                                                                   job.time_end))
