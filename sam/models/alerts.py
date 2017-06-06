import os
import datetime
import time
import cPickle
import web
from sam import common, integrity
from sam.models.base import DBPlugin

base_path = os.path.dirname(__file__)


class AlertFilter():
    def __init__(self, min_severity=0, limit=20, age_limit=None, sort="id", order="DESC"):
        """
        :param min_severity: minimum severity (inclusive) to get.
         :type min_severity: int
        :param limit: maximum number of results to get.
         :type limit: int
        :param age_limit: maximum age in seconds to get.
         :type age_limit: int
        :param sort: column to sort results by
         :type sort: unicode
        :param order: order to sort in, one of "DESC" or "ASC"
         :type order: unicode
        """
        self.limit = int(limit)
        self.age_limit = age_limit
        self.min_severity = int(min_severity)
        self.sort = sort
        self.order = u"ASC" if order.lower() == u"asc" else u"DESC"

    def get_where(self, preexisting=None):
        if self.age_limit:
            age = int(time.time()) - int(self.age_limit)
            where = "severity >= {sev} AND report_time > {age}".format(sev=self.min_severity, age=age)
        else:
            where = "severity >= {sev}".format(sev=self.min_severity)

        if preexisting:
            where = "{} AND {}".format(preexisting, where)

        return where

    def get_orderby(self):
        return "{} {}".format(self.sort, self.order)


class Alerts():
    TABLE_FORMAT = "s{}_Alerts"

    def __init__(self, db, sub_id):
        """
        :param db: database connection
         :type db: web.DB
        """
        self.db = db
        self.sub_id = sub_id
        self.table = Alerts.TABLE_FORMAT.format(sub_id)

    def add_alert(self, ipstart, ipend, severity, rule_id, rule_name, label, details, timestamp):
        """
        :param ipstart: integer ip address. 32-bit unsigned integer.
         :type ipstart: int
        :param ipend: integer, end of the ip subnet range. For individual hosts, this is the same as ipstart
         :type ipend: int
        :param severity: How significant is the event? higher number is more severe.
         :type severity: int
        :param rule_id: The id of the rule that spawned this alert
         :type rule_id: int
        :param rule_name: The name of the rule that spawned this alert
         :type rule_name: str
        :param event_type: A generic type by which one might categorize events
         :type event_type: unicode
        :param details: Any extra details. Native python formats supported. Will be pickled and stored. 
         :type details: Any
        :param timestamp: timestamp (syslog time) to attach to the alert
         :type timestamp: datetime.datetime
        :return: event id.
         :rtype: int
        """
        columns = {
            'ipstart': ipstart,
            'ipend': ipend,
            'severity': severity,
            'label': label,
            'log_time': int(time.mktime(timestamp.timetuple())),
            'report_time': int(time.time()),
            'rule_id': rule_id,
            'rule_name': rule_name,
            'details': cPickle.dumps(details)
        }

        new_id = self.db.insert(self.table, **columns)
        return new_id

    @staticmethod
    def decode_details(rowlist):
        for row in rowlist:
            row['details'] = cPickle.loads(str(row['details']))

    def get_recent(self, filters):
        """
        :param filters: standard filters for alert events
         :type filters: AlertFilter
        :return: list of alert events.
        """

        where = filters.get_where()
        what = 'id, ipstart, ipend, log_time, report_time, severity, label, rule_name, rule_id'

        rows = self.db.select(self.table, where=where, what=what, order=filters.get_orderby(), limit=filters.limit)
        rows = list(rows)
        return rows

    def get_by_host(self, filters, ipstart, ipend):
        """
        :param filters: standard filters for alert events
         :type filters: AlertFilter
        :param ipstart: 
         :type ipstart: int
        :param ipend:
         :type ipend: int 
        :return: 
        """
        qvars = {
            'ips': ipstart,
            'ipe': ipend
        }
        where = filters.get_where("ipstart>=$ips AND ipend<=$ipe")
        what = 'id, ipstart, ipend, log_time, report_time, severity, label, rule_name, rule_id'
        rows = self.db.select(self.table, where=where, what=what, vars=qvars, order=filters.get_orderby(), limit=filters.limit)
        rows = list(rows)
        return rows

    def get_details(self, alert_id):
        rows = list(self.db.select(self.table, where='id={}'.format(int(alert_id))))
        self.decode_details(rows)
        if len(rows) > 0:
            return rows[0]
        return None

    def set_label(self, alert_id, label):
        qvars = {
            'aid': alert_id
        }
        where = 'id=$aid'
        if not label or len(label) > 32:
            print('Failed to update alert event status. Status text was "{}".'.format(repr(label)))
            return None
        return self.db.update(self.table, where=where, vars=qvars, label=label)

    def clear(self):
        return self.db.delete(self.table, where="1")
