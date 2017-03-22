import os
from datetime import datetime
import constants
import common
import models.datasources
import models.ports
import models.settings
import models.livekeys
from models.user import User


class Subscriptions:
    CREATE_SQL = os.path.join(constants.base_path, 'sql/setup_subscription_tables.sql')
    DROP_SQL = os.path.join(constants.base_path, 'sql/drop_subscription.sql')
    table = "Subscriptions"

    def __init__(self):
        self.db = common.db

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
        portsModel = models.ports.Ports(sub_id)
        portsModel.reset()

    def create_default_subscription(self):
        user = User()
        email = user.email
        name = user.name
        plan = user.plan
        active = user.plan_active
        self.db.insert(self.table, email=email, name=name, plan=plan, active=active)
