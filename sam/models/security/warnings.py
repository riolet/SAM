import os
import cPickle
import web
from sam import constants, integrity, common
from sam.models import base
base_path = os.path.dirname(__file__)

# warning status should be one of "accepted", "rejected", "ignored", "uncategorized"


class Warnings(base.DBPlugin):
    TABLE_FORMAT = 's{acct}_ADWarnings'
    VALID_STATUSES = ("accepted", "rejected", "ignored", "uncategorized")

    checkIntegrity = base.DBPlugin.simple_sub_table_check(TABLE_FORMAT)

    fixIntegrity = base.DBPlugin.simple_sub_table_fix(
        sqlite=os.path.join(constants.base_path, 'sql/create_warnings_sqlite.sql'),
        mysql=os.path.join(constants.base_path, 'sql/create_warnings_mysql.sql'),
    )

    def __init__(self, db, sub_id):
        """
        :param db: Database connection
         :type db: web.DB
        :param sub_id: subscription id
         :type sub_id: int
        """
        self.db = db
        self.sub_id = sub_id
        self.table = Warnings.TABLE_FORMAT.format(acct=self.sub_id)

    def get_latest_warning_id(self):
        """
        :return: The id of the latest (newest) warning known in this database. If db is empty, gives 0.
         :rtype: int
        """
        rows = self.db.select(self.table, what="MAX(warning_id) AS 'latest'")
        row = rows.first()
        if row is None or row['latest'] is None:
            return 0
        else:
            return row['latest']

    def get_warnings(self, show_all=False):
        what = "id, warning_id, host, log_time, reason, status"
        if show_all:
            warnings = self.db.select(self.table, what=what, order="id DESC", limit=50)
        else:
            warnings = self.db.select(self.table, what=what, where="status='uncategorized'", order="id DESC", limit=50)
        return list(warnings)

    def get_warning(self, warning_id):
        rows = self.db.select(self.table, where="id=$wid", vars={'wid': warning_id})
        row = rows.first()
        if row is None:
            return None
        if 'details' in row:
            row['details'] = cPickle.loads(str(row['details']))
        return row

    def _warning_status(self, status):
        if status.lower() == 'rejected':
            return 'rejected'
        elif status.lower() == 'accepted':
            return "accepted"
        elif status.lower() == 'ignored':
            return "ignored"
        else:
            return "uncategorized"

    def insert_warnings(self, wlist):
        transformed = []
        for warning in wlist:
            transformed.append({
                'warning_id': warning['id'],
                'host': warning['host'],
                'log_time': warning['log_time'],
                'reason': warning['reason'],
                'status': self._warning_status(warning.get('status', 'uncategorized')),
                'details': cPickle.dumps(warning['details'])
            })
        # insert in chunks of at most 1000
        n = 0
        high = len(transformed)
        while n < high:
            self.db.multiple_insert(self.table, transformed[n:n+1000])
            n += 1000

    def update_status(self, warning_id, status):
        qvars = {'wid': warning_id}
        if status.lower() in Warnings.VALID_STATUSES:
            num_rows_updated = self.db.update(self.table, where="id=$wid", vars=qvars, status=status.lower())
        else:
            raise ValueError("invalid status")
        if num_rows_updated == 0:
            raise ValueError("Warning # doesn't match any warning.")
        return num_rows_updated
