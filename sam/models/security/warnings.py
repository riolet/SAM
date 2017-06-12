import os
import cPickle
import web
from sam import integrity, common
from sam.models import base
base_path = os.path.dirname(__file__)


class Warnings(base.DBPlugin):
    TABLE_FORMAT = 's{acct}_ADWarnings'

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
        rows = self.db.select(self.table, what="MAX(id) AS 'latest'")
        row = rows.first()
        if row is None:
            return 0
        else:
            return row['latest']

    def get_warnings(self, show_all=False):
        what = "id, host, log_time, reason, status"
        if show_all:
            warnings = self.db.select(self.table, what=what, order="id DESC", limit=50)
        else:
            warnings = self.db.select(self.table, what=what, where="status not in ('Accepted', 'Rejected', 'Ignored')", order="id DESC", limit=50)
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
            return 'Rejected'
        elif status.lower() == 'accepted':
            return "Accepted"
        elif status.lower() == 'ignored':
            return "Ignored"
        else:
            return "Undetermined"

    def insert_warnings(self, wlist):
        transformed = []
        for warning in wlist:
            transformed.append({
                'id': warning['id'],
                'host': warning['host'],
                'log_time': warning['log_time'],
                'reason': warning['reason'],
                'status': self._warning_status(warning.get('status', 'unknown')),
                'details': cPickle.dumps(warning['details'])
            })
        self.db.multiple_insert(self.table, transformed)

    def update_status(self, warning_id, status):
        qvars = {
            'wid': warning_id,
        }
        if status.lower() == 'accepted':
            num_rows_updated = self.db.update(self.table, where="id=$wid", vars=qvars, status='Accepted')
        elif status.lower() == 'rejected':
            num_rows_updated = self.db.update(self.table, where="id=$wid", vars=qvars, status='Rejected')
        elif status.lower() == 'ignored':
            num_rows_updated = self.db.update(self.table, where="id=$wid", vars=qvars, status='Ignored')
        else:
            raise ValueError("invalid status")
        return num_rows_updated

    @staticmethod
    def checkIntegrity(db):
        all_tables = set(integrity.get_table_names(db))
        subs = integrity.get_all_subs(db)
        missing = []
        for sub_id in subs:
            if Warnings.TABLE_FORMAT.format(acct=sub_id) not in all_tables:
                missing.append(sub_id)
        if not missing:
            return {}
        return {'missing': missing}

    @staticmethod
    def fixIntegrity(db, errors):
        missing_table_subs = errors['missing']
        for sub_id in missing_table_subs:
            replacements = {
                'acct': sub_id
            }
            with db.transaction():
                if db.dbname == 'sqlite':
                    common.exec_sql(db, os.path.join(base_path, '../sql/create_warnings_sqlite.sql'), replacements)
                else:
                    common.exec_sql(db, os.path.join(base_path, '../sql/create_warnings_mysql.sql'), replacements)
        return True