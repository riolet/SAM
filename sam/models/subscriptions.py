import os
import cPickle
import logging
from sam import constants
import web
from sam import common
import sam.models.ports

logger = logging.getLogger(__name__)


class Subscriptions:
    CREATE_MYSQL = os.path.join(constants.base_path, 'sql/setup_subscription_tables_mysql.sql')
    CREATE_SQLITE = os.path.join(constants.base_path, 'sql/setup_subscription_tables_sqlite.sql')
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

    def set(self, sub_id, **kwargs):
        qvars = {
            'sub': sub_id,
        }
        rows_updated = self.db.update(Subscriptions.table, "subscription=$sub", vars=qvars, **kwargs)
        return rows_updated == 1

    def create_subscription_tables(self, sub_id):
        replacements = {"acct": sub_id}
        if self.db.dbname == 'mysql':
            common.exec_sql(self.db, self.CREATE_MYSQL, replacements)
        else:
            common.exec_sql(self.db, self.CREATE_SQLITE, replacements)

        # replicate port data
        portsModel = sam.models.ports.Ports(self.db, sub_id)
        portsModel.reset()

    def create_default_subscription(self):
        email = constants.subscription['default_email']
        name = constants.subscription['default_name']
        plan = 'admin'
        active = True
        self.db.insert(self.table, email=email, name=name, plan=plan, groups='read write admin', active=active)

    def decode_sub(self, key):
        """
        :param key: a subscription id (string or int) or an email address that identify a subscription
        :type key: int or unicode
        :return: Subscription id (integer) or None on failure
        :rtype: int or None
        """
        subs = self.get_all()
        numbers = {sub['subscription'] for sub in subs}

        response = None
        sub_num = -1
        try:
            sub_num = int(key)
        except:
            sought_sub = None
            for sub in subs:
                if sub['email'] == key:
                    sought_sub = sub
                    break
            if sought_sub:
                sub_num = sought_sub['subscription']

        if sub_num in numbers:
            response = sub_num
        elif constants.access_control['active'] is False:
            sought_sub = None
            for sub in subs:
                if sub['email'] == constants.subscription['default_email']:
                    sought_sub = sub
                    break
            if sought_sub:
                response = sought_sub['subscription']

        return response

    def get_plugin_data(self, sub_id, plugin_name):
        qvars = {'sid': sub_id}
        rows = self.db.select(self.table, what="plugins", where="subscription=$sid", vars=qvars)
        row = rows.first()
        if not row:
            raise ValueError("invalid subscription id")
        try:
            plugins = cPickle.loads(str(row['plugins']))
        except:
            logger.warning("error decoding plugins: plugins was {}".format(repr(row['plugins'])))
            plugins = {}
        data = plugins.get(plugin_name, {})
        return data

    def set_plugin_data(self, sub_id, plugin_name, data):
        qvars = {'sid': int(sub_id)}
        rows = self.db.select(self.table, what="plugins", where="subscription=$sid", vars=qvars)
        row = rows.first()
        if not row:
            raise ValueError("invalid subscription id")
        try:
            plugins = cPickle.loads(str(row['plugins']))
        except:
            plugins = {}

        try:
            plugins[plugin_name] = data
            self.db.update(self.table, where="subscription=$sid", vars=qvars, plugins=cPickle.dumps(plugins))
        except:
            logger.error("cannot encode data")
            raise
