import re
import os
import constants
import web
import common
import settings
import livekeys


class Datasources:
    DS_TABLES = ["StagingLinks", "Links", "LinksIn", "LinksOut", "Syslog"]
    DROP_SQL = os.path.join(constants.base_path, 'sql/drop_datasource.sql')
    MIN_INTERVAL = 5
    MAX_INTERVAL = 1800
    SESSION_KEY = "_datasources"
    TABLE = "Datasources"

    def __init__(self, db, session, subscription):
        """
        :type db: web.DB
        :type session: dict
        :type subscription: int
        :param db: 
        :param session: 
        :param subscription: 
        """
        self.db = db
        self.sub = subscription
        self.storage = session
        if self.db.dbname == 'sqlite':
            self.CREATE_SQL = os.path.join(constants.base_path, 'sql/setup_datasource_sqlite.sql')
        else:
            self.CREATE_SQL = os.path.join(constants.base_path, 'sql/setup_datasource_mysql.sql')

    @property
    def datasources(self):
        if not self.storage.get(Datasources.SESSION_KEY):
            self.update_cache()
        return self.storage[Datasources.SESSION_KEY]

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
        rows = self.db.select(Datasources.TABLE, where='subscription=$sub', vars={'sub': self.sub})
        self.storage[Datasources.SESSION_KEY] = {ds['id']: ds for ds in rows}

    def clear_cache(self):
        self.storage[Datasources.SESSION_KEY] = {}

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
        rows_updated = self.db.update(Datasources.TABLE, "subscription=$sub AND id=$dsid", vars=qvars, **kwargs)
        self.clear_cache()
        return rows_updated == 1

    @staticmethod
    def validate_ds_name(name):
        return re.match(r'^(\w[\w ]*\w|\w)$', name)

    @staticmethod
    def validate_ds_interval(interval):
        return 5 <= interval <= 1800

    def create_ds_tables(self, dsid):
        replacements = {'acct': self.sub, 'id': dsid}
        common.exec_sql(self.db, self.CREATE_SQL, replacements)

    def create_datasource(self, name='default'):
        if not self.validate_ds_name(name):
            return -1
        ds_id = self.db.insert(Datasources.TABLE, subscription=self.sub, name=name)
        self.create_ds_tables(ds_id)
        self.clear_cache()
        return ds_id

    def remove_datasource(self, ds_id):
        settings_model = settings.Settings(self.db, self.storage, self.sub)
        livekeys_model = livekeys.LiveKeys(self.db, self.sub)
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
        settings_model['datasource'] = alt_id

        # remove from live_dest if selected
        livekeys_model.delete_ds(ds_id)

        # remove from Datasources
        # Subscription is not needed to be specified in the WHERE clause because `id` is primary key.
        self.db.delete(Datasources.TABLE, "id={0}".format(int(ds_id)))
        # Drop relevant tables
        replacements = {'acct': self.sub, 'id': int(ds_id)}
        common.exec_sql(self.db, Datasources.DROP_SQL, replacements)
        self.clear_cache()

    def remove_all(self):
        # get list of targets for removal
        victims = self.ds_ids

        for dsid in victims:
            # remove all datasource table rows
            self.db.delete(Datasources.TABLE, "id={0}".format(int(dsid)))

            # remove all datasource tables
            replacements = {'acct': self.sub, 'id': int(dsid)}
            common.exec_sql(self.db, Datasources.DROP_SQL, replacements)
