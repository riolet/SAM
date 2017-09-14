import re
import time
import logging
import traceback
import multiprocessing
import multiprocessing.queues  # for IDE (pycharm type helper)
import web
from datetime import datetime
from sam import common, constants, errors
from sam.models.security import rule, rule_parser, alerts

logger = logging.getLogger(__name__)
_RULES_PROCESS = None
_QUEUE = multiprocessing.Queue()
_MANAGER = multiprocessing.Manager()
_JOBS = _MANAGER.dict()
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
    _JOBS = _MANAGER.dict()
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
         :type start: datetime
        :param end: the end of the analysis timerange
         :type end: datetime
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
        self.completion = 0  # number from 0 to 1 representing the completion of this job.

    @staticmethod
    def rebuild(parameters):
        assert len(parameters) == 8
        sub_id = parameters[0]
        ds_id = parameters[1]
        start = parameters[2]
        end = parameters[3]
        rules = parameters[4]
        id_ = parameters[5]
        status = parameters[6]
        completion = parameters[7]
        self = RuleJob(sub_id, ds_id, start, end, rules)
        self.id = id_
        self.status = status
        self.completion = completion
        return self

    def export(self):
        return self.sub_id, self.ds_id, self.time_start, self.time_end, self.rules, self.id, self.status, self.completion

    def __eq__(self, other):
        if not isinstance(other, RuleJob):
            return False
        match = (self.id == other.id
                 and self.sub_id == other.sub_id
                 and self.ds_id == other.ds_id
                 and self.time_end == other.time_end
                 and self.time_start == other.time_start
                 and self.rules == other.rules
                 )
        return match


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
    _JOBS[job.id] = job.export()
    # insert the job_id into the queue
    _QUEUE.put(job.id)
    # if the RulesProcessor process isn't running, start it.
    spawn_if_not_alive()
    # return the job_id
    return job.id


def spawn_if_not_alive():
    global _RULES_PROCESS
    if _RULES_PROCESS is None or not _RULES_PROCESS.is_alive():
        _RULES_PROCESS = multiprocessing.Process(target=ruling_process, args=(_QUEUE,_DB_QUIET))
        _RULES_PROCESS.daemon = True
        _RULES_PROCESS.start()


def check_job(sub_id, job_id):
    # include sub_id for security purposes
    job_params = _JOBS.get(job_id, None)
    try:
        job = RuleJob.rebuild(job_params)
    except:
        job = None

    if job is None or job.sub_id != sub_id:
        return "Missing", None
    return job.status, job.completion


def reset_globals():
    global _JOBS, _QUEUE
    _JOBS = _MANAGER.dict()
    _QUEUE = multiprocessing.Queue()


def ruling_process(queue, db, stayalive=_PROCESSOR_STAYALIVE):
    """
    :param queue: job queue. contains ids that reference the _JOBS global.
     :type queue: multiprocessing.queues.Queue
    :param stayalive: How long to keep the process running if it runs out of jobs before shutdown.
     :type stayalive: float
    :return: 
    """
    global _JOBS, _PROCESSOR_STAYALIVE
    # print("Queue: {}".format(queue))
    # print("Stayalive: {}".format(stayalive))
    # print("_JOBS: {}".format(_JOBS))
    engine = RulesProcessor(db)
    while not queue.empty():
        try:
            job_id = queue.get()
            try:
                job_params = _JOBS[job_id]
                job = RuleJob.rebuild(job_params)
                engine.process(job)
            except:
                traceback.print_exc()
                logger.warn("error processing job {}.".format(job_id))
                logger.warn("JOBS: {}".format(_JOBS))
            if queue.empty():
                time.sleep(stayalive)
        except KeyboardInterrupt:
            break
        except Exception as e:
            traceback.print_exc()
    reset_globals()
    return engine


def translate_symbols(s, tr):
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

        parser = rule_parser.RuleParser(translations, subject, conditions, (job.time_start, job.time_end))
        query = parser.sql.get_query(table)
        alerts_discovered = list(self.db.query(query))

        return alerts_discovered

    @staticmethod
    def send_email_alert(email, subject, rule_, matches):

        matches_string = "\n".join(["{}: {}".format(m['timestamp'], common.IPtoString(m[rule_.definition.subject])) for m in matches])

        body = """
This is an email alert from System Architecture Mapper to let you know that one of your security rules ({rule_name}) has been triggered.
The complete list of hosts that triggered the rule is:

{match_traffic}

Thanks,
SAM
""".format(rule_name=rule_.get_name(), match_traffic=matches_string)

        try:
            common.sendmail(email, subject, body)
        except Exception as e:
            raise errors.AuthenticationError(str(e))

    def trigger_alert(self, job, rule_, action, match, tr_table):
        """
        sql debugging:
        # SELECT id, decodeIP(ipstart), FROM_UNIXTIME(timestamp), severity, viewed, label, rule_id FROM s1_Alerts;
        :param job:
         :type job: RuleJob
        :param rule_:
         :type rule_: rule.Rule
        :param action:
         :type action: dict[basestring, Any]
        :param match:
         :type match: dict[basestring, Any]
        :param tr_table:
         :type tr_table: dict[basestring, Any]
        :return:
         :rtype: None
        """
        m_alerts = alerts.Alerts(self.db, job.sub_id)
        ip = match.get(rule_.definition.subject, 0)
        severity = action['severity']
        label = translate_symbols(action['label'], tr_table)

        m_alerts.add_alert(ip, ip, severity, rule_.id, rule_.get_name(), label, match, match['timestamp'])
        # print("  Triggering alert: {} ({}): {}".format(common.IPtoString(ip), severity, label))

    def trigger_email(self, job, rule_, action, matches, tr_table):
        address = action['address']
        subject_fstring = action['subject']
        subject = translate_symbols(subject_fstring, tr_table)
        self.send_email_alert(address, subject, rule_, matches)
        # print("  Triggering email to {}: re: {}".format(address, subject))

    def trigger_sms(self, job, rule_, action, matches, tr_table):
        number = action['number']
        message_fstring = action['message']
        message = translate_symbols(message_fstring, tr_table)

        try:
            common.sendsms(number, message)
        except Exception as e:
            logger.error("SMS Alerts are not available yet.")
            raise errors.AuthenticationError(str(e))

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
        tr_table = rule_.get_translation_table()
        # print('    Rule actions:')
        # for action in actions:
        #     print('      {}'.format(repr(action)))

        for action in actions:
            if action['type'] == 'alert':
                for match in matches:
                    self.trigger_alert(job, rule_, action, match, tr_table)
            elif action['type'] == 'email':
                try:
                    self.trigger_email(job, rule_, action, matches, tr_table)
                except errors.AuthenticationError:
                    logger.exception("Could not send email")
            elif action['type'] == 'sms':
                try:
                    self.trigger_sms(job, rule_, action, matches, tr_table)
                except errors.AuthenticationError:
                    logger.exception("Could not send sms")
            else:
                logger.warning('action "{}" not supported'.format(action['type']))
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
        logger.info('{}: Starting job on s{}_ds{}, from {} to {}'.format(job.status, job.sub_id, job.ds_id, job.time_start,
                                                                   job.time_end))

        for i, rule_ in enumerate(job.rules):
            job.status = 'Running rule {} of {}'.format(i+1, len(job.rules))
            if not rule_.is_active():
                logger.info('  {}: Skipping rule {} ({})'.format(job.status, rule_.get_name(), rule_.nice_path(rule_.path)))
                continue

            logger.info('  {}: Working on rule {} ({})'.format(job.status, rule_.get_name(), rule_.nice_path(rule_.path)))

            rule_type = rule_.get_type()
            if rule_type == 'immediate':
                matches = self.evaluate_immediate_rule(job, rule_)
            elif rule_type == 'periodic':
                matches = self.evaluate_periodic_rule(job, rule_)
            else:
                logger.info('  {}: Skipping rule {}. Type {} is not "immediate" nor "periodic"'
                      .format(job.status, rule_.get_name(), rule_type))
                continue
            logger.info('    {} alerts discovered,'.format(len(matches)))
            # for match in matches:
            #     print('      {}: {} -> {}:{} x{} using {}'.format(
            #         datetime.fromtimestamp(int(time.mktime(match.timestamp.timetuple()))),
            #         common.IPtoString(match.get('src', 0)),
            #         common.IPtoString(match.get('dst', 0)),
            #         match.get('port', 0),
            #         match.get('links', 0),
            #         match.get('protocol', 0)))
            self.trigger_actions(job, rule_, matches)

        job.status = "Complete"
        logger.info('{}: Finished job on s{}_ds{}, from {} to {}'.format(job.status, job.sub_id, job.ds_id,
                                                                   job.time_start, job.time_end))
