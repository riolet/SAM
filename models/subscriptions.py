import os
import constants
import web
import common
import models.ports


class Subscriptions:
    CREATE_SQL = os.path.join(constants.base_path, 'sql/setup_subscription_tables.sql')
    DROP_SQL = os.path.join(constants.base_path, 'sql/drop_subscription.sql')
    table = "Subscriptions"

    def __init__(self, db):
        """
        :type db: web.DB
        """
        self.db = db

    def get_all(self):
        rows = self.db.select(Subscriptions.table)
        return list(rows)

    def get_id_list(self):
        rows = self.db.select(Subscriptions.table, what="subscription")
        return [row['subscription'] for row in rows]

    def get_by_email(self, email):
        qvars = {
            'email': email
        }
        rows = self.db.select(Subscriptions.table, where='email=$email', vars=qvars)
        return rows.first()

    def get(self, sub_id):
        qvars = {
            'sid': sub_id
        }
        rows = self.db.select(Subscriptions.table, where='subscription=$sid', vars=qvars)
        return rows.first()

    def create_subscription_tables(self, sub_id):
        replacements = {"acct": sub_id}
        common.exec_sql(self.db, self.CREATE_SQL, replacements)

        # replicate port data
        portsModel = models.ports.Ports(self.db, sub_id)
        portsModel.reset()

    def create_default_subscription(self):
        email = constants.demo['email']
        name = constants.demo['name']
        plan = 'admin'
        active = True
        self.db.insert(self.table, email=email, name=name, plan=plan, groups='read write admin', active=active)
