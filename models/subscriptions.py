import os
import common
import models.datasources


class Subscriptions:
    CREATE_SQL = os.path.join(common.base_path, 'sql/setup_subscription_tables.sql')
    default_datasource_name = 'default'

    def __init__(self):
        self.db = common.db
        self.table = "Settings"

    def get_list(self):
        rows = self.db.select(self.table, what="subscription")
        return [row['subscription'] for row in rows]

    def create_subscription_tables(self, sub_id):
        replacements = {"acct": sub_id}
        common.exec_sql(self.db, self.CREATE_SQL, replacements)

    def add_subscription(self, sub_id):
        # add subscription tables
        self.create_subscription_tables(sub_id)

        # add default datasource for subscription
        dsModel = models.datasources.Datasources(sub_id)
        ds_id = dsModel.create_datasource(self.default_datasource_name)

        # add settings entry
        self.db.insert(self.table, subscription=sub_id, datasource=ds_id)
