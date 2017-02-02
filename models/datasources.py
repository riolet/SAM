import os
import common
import settings


class Datasources:
    DS_TABLES = ["staging_Links", "Links", "LinksIn", "LinksOut", "Syslog"]
    CREATE_SQL = os.path.join(common.base_path, 'sql/setup_datasource.sql')
    DROP_SQL = os.path.join(common.base_path, 'sql/drop_datasource.sql')
    MIN_INTERVAL = 5
    MAX_INTERVAL = 1800

    def __init__(self, subscription=None):
        self.db = common.db
        self.sub = subscription or common.get_subscription()
        self.table = "Datasources"
        # TODO: store in session
        self._datasources = {}

    @property
    def datasources(self):
        if not self._datasources:
            self.update_cache()
        return self._datasources

    @property
    def ds_ids(self):
        return sorted(self.datasources.keys())

    def sorted_list(self):
        dss = self.datasources.values()
        dss.sort(key=lambda x: x['id'])
        return dss

    def priority_list(self, ds):
        dss = self.datasources.copy()
        first = dss.pop(ds)
        rest = dss.values()
        rest.sort(key=lambda x: x['id'])
        return [first] + rest

    def update_cache(self):
        rows = self.db.select(self.table, where='subscription=$sub', vars={'sub': self.sub})
        self._datasources = {ds['id']: ds for ds in rows}

    def clear_cache(self):
        self._datasources = {}

    def set(self, ds, **kwargs):
        qvars = {
            'sub': self.sub,
            'dsid': ds
        }
        if 'name' in kwargs:
            if not self.validate_ds_name(kwargs['name']):
                raise ValueError("Invalid Name")
        if 'ar_interval' in kwargs:
            if not self.validate_ds_interval(kwargs['ar_interval']):
                raise ValueError("Invalid Interval. Must be between ({0} and {1})"
                                 .format(self.MIN_INTERVAL, self.MAX_INTERVAL))
        rows_updated = self.db.update(self.table, "subscription=$sub AND id=$dsid", vars=qvars, **kwargs)
        self.clear_cache()
        return rows_updated == 1

    @staticmethod
    def validate_ds_name(name):
        return name == name.strip() and name[0].isalpha() and name.isalnum()

    @staticmethod
    def validate_ds_interval(interval):
        return 5 <= interval <= 1800

    def create_ds_tables(self, dsid):
        replacements = {'acct': self.sub, 'id': dsid}
        common.exec_sql(self.db, self.CREATE_SQL, replacements)

    def create_datasource(self, name):
        if not self.validate_ds_name(name):
            return -1
        ds_id = self.db.insert(self.table, subscription=self.sub, name=name)
        self.create_ds_tables(ds_id)
        self.clear_cache()
        return ds_id

    def remove_datasource(self, ds_id):
        settingsModel = settings.Settings(self.sub)
        ids = self.ds_ids

        # check id is valid
        if ds_id not in ids:
            raise KeyError("Invalid ID: {0} given; {1} available".format(id, ids))

        # select other data source in Settings
        alt_id = -1
        for n in ids:
            if n != ds_id:
                alt_id = n
                break
        if alt_id == -1:
            raise IndexError("Cannot remove the last data source")
        settingsModel['datasource'] = alt_id

        # remove from live_dest if selected
        if settingsModel['live_dest'] == ds_id:
            settingsModel['live_dest'] = None

        # remove from Datasources
        # Subscription is not needed to be specified in the WHERE clause because `id` is primary key.
        self.db.delete(self.table, "id={0}".format(int(ds_id)))
        # Drop relevant tables
        replacements = {'acct': self.sub, 'id': int(ds_id)}
        common.exec_sql(self.db, self.DROP_SQL, replacements)
        self.clear_cache()
