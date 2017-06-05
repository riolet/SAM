import re
import time
from datetime import datetime
import multiprocessing
import multiprocessing.queues  # for IDE (pycharm type helper)
import web
from sam import common, constants
from sam.models import rule, rule_parser, alerts

_RULES_PROCESS = None
_QUEUE = multiprocessing.Queue()
_JOBS = {}
_NEXT_ID = 1
# get own connection to DB
_DB, _DB_QUIET = common.get_db(constants.dbconfig.copy())
# keep processor alive for xx seconds between jobs (to reduce shutdown/startup overhead
_PROCESSOR_STAYALIVE = 10

def __testing_only_reset_state():
    global _RULES_PROCESS, _QUEUE, _JOBS, _NEXT_ID
    if _RULES_PROCESS and _RULES_PROCESS.is_alive():
        _RULES_PROCESS.terminate()
    _RULES_PROCESS = None
    _QUEUE = multiprocessing.Queue()
    _JOBS = {}
    _NEXT_ID = 1


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
    # if the RulesProcessor process isn't running, start it.
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


def ruling_process(queue, stayalive=_PROCESSOR_STAYALIVE):
    """
    :param queue: job queue. contains ids that reference the _JOBS global.
     :type queue: multiprocessing.queues.Queue
    :param stayalive: How long to keep the process running if it runs out of jobs before shutdown.
     :type stayalive: int
    :return: 
    """
    global _JOBS, _PROCESSOR_STAYALIVE
    #print("Queue: {}".format(queue))
    #print("Stayalive: {}".format(stayalive))
    #print("_JOBS: {}".format(_JOBS))
    engine = RulesProcessor(_DB_QUIET)
    while not queue.empty():
        job_id = queue.get()
        engine.process(_JOBS[job_id])
        if queue.empty():
            time.sleep(stayalive)
    reset_globals()
    return engine


def translate_symbols(self, s, tr):
    result = re.sub(r'\$(\S+)',
                    lambda match: tr[match.group(1)] if match.group(1) in tr else match.group(1),
                    unicode(s))
    return result


class RulesProcessor(object):
    COND_REGEX = re.compile(r"^(?P<rule>(?:(?P<dir>src|dst|src or dst|src and dst)\s+)(?P<type>host|port))\s+(?P<value>\S+|in \S+)$")
    TABLE_FORMAT = "s{sub_id}_ds{ds_id}_Links"

    def __init__(self, db):
        """
        :param db:
         :type db: web.DB
        """
        self.db = db

    def evaluate_immediate_rule(self, job, rule_):
        translations = rule_.get_translation_table()
        conditions = rule_.get_conditions()
        subject = rule_.definition.subject
        table = RulesProcessor.TABLE_FORMAT.format(sub_id=job.sub_id, ds_id=job.ds_id)

        parser = rule_parser.RuleParser(translations, subject, conditions)
        parser.sql.set_timerange(job.time_start, job.time_end)
        query = parser.sql.get_query(table)
        # print(" QUERY ".center(80, '='))
        # print(query)
        # print(" END QUERY ".center(80, '='))
        alerts_discovered = list(self.db.query(query))

        return alerts_discovered

    def evaluate_periodic_rule(self, job, rule_):
        translations = rule_.get_translation_table()
        conditions = rule_.get_conditions()
        subject = rule_.definition.subject
        table = RulesProcessor.TABLE_FORMAT.format(sub_id=job.sub_id, ds_id=job.ds_id)

        parser = rule_parser.RuleParser(translations, subject, conditions)
        query = parser.sql.get_query(table)
        alerts_discovered = list(self.db.query(query))

        return alerts_discovered

    def trigger_alert(self, sub_id, rule_, severity, label, subject, match):
        """

        sql debugging:
        # SELECT id, decodeIP(ipstart), FROM_UNIXTIME(timestamp), severity, viewed, label, rule_id FROM s1_Alerts;

        :param sub_id:
         :type sub_id: int
        :param rule_:
         :type rule_: rule.Rule
        :param severity:
         :type severity: int or str
        :param label:
         :type label: str
        :param subject:
         :type subject: str
        :param match:
         :type match: dict[basestring, Any]
        :return:
         :rtype: None
        """

        m_alerts = alerts.Alerts(self.db, sub_id)
        ip = match.get(subject, 0)
        m_alerts.add_alert(ip, ip, severity, rule_.id, rule_.get_name(), label, match)
        print("  Triggering alert: {} ({}): {}".format(common.IPtoString(ip), severity, label))

    def trigger_email(self, address, email_subject, subject, matches, translations):
        print("  Triggering email to {}: re: {}".format(address, email_subject))
        print('    WARNING: email alerts are not implemented yet.')

    def trigger_sms(self, number, message, subject, matches, translations):
        print("  Triggering sms to {} ({}/160 chars):".format(number, len(message)))
        print("    {}".format(message))
        print('    WARNING: sms alerts are not implemented yet.')

    def trigger_actions(self, job, rule_, matches):
        """
        Trigger/Create/Send any appropriate actions for all matches found.
        :param job:
         :type job: RuleJob
        :param rule_:
         :type rule_: rule.Rule
        :param matches:
         :type matches: list[ dict[basestring, Any] ]
        :return:
         :rtype: None
        """
        actions = rule_.get_actions()
        print('    Rule actions:')
        for action in actions:
            print('      {}'.format(repr(action)))

        for action in actions:
            if action['type'] == 'alert':
                for match in matches:
                    self.trigger_alert(job.sub_id, rule_, action['severity'], action['label'], rule_.definition.subject, match)
            elif action['type'] == 'email':
                self.trigger_email(action['address'], action['subject'], rule_.definition.subject, matches)
            elif action['type'] == 'sms':
                self.trigger_sms(action['number'], action['message'], rule_.definition.subject, matches)
            else:
                print('WARNING: action "{}" not supported'.format(action['type']))
                continue

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

        for i, rule_ in enumerate(job.rules):
            job.status = 'Running rule {} of {}'.format(i+1, len(job.rules))
            if not rule_.is_active():
                print('  {}: Skipping rule {} ({})'.format(job.status, rule_.get_name(), rule_.nice_path()))
                continue

            print('  {}: Working on rule {} ({})'.format(job.status, rule_.get_name(), rule_.nice_path()))

            rule_type = rule_.get_type()
            if rule_type == 'immediate':
                matches = self.evaluate_immediate_rule(job, rule_)
            elif rule_type == 'periodic':
                matches = self.evaluate_periodic_rule(job, rule_)
            else:
                print('  {}: Skipping rule {}. Type {} is not "immediate" nor "periodic"'.format(job.status, rule_.get_name(), rule_type))
                continue
            print('    {} alerts discovered,'.format(len(matches)))
            for match in matches:
                print('      {}: {} -> {}:{} x{} using {}'.format(
                    datetime.fromtimestamp(int(time.mktime(match.timestamp.timetuple()))),
                    common.IPtoString(match.src),
                    common.IPtoString(match.dst),
                    match.port,
                    match.links,
                    match.protocol))
            self.trigger_actions(job, rule_, matches)

        job.status = "Complete"
        print('{}: Finished job on s{}_ds{}, from {} to {}'.format(job.status, job.sub_id, job.ds_id, job.time_start,
                                                                   job.time_end))
