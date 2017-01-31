import re
import os
import common
import dbaccess


class Datasources:
    CREATE_SQL = os.path.join(common.base_path, 'sql/setup_datasource.sql')
    DROP_SQL = os.path.join(common.base_path, 'sql/drop_datasource.sql')
    def __init__(self):
        self.db = common.db
        self.table = "Datasources"
        # TODO: store in session
        self._datasources = {}
        self.update_cache()

    @property
    def datasources(self):
        if not self._datasources:
            self.update_cache()
        return self._datasources

    @property
    def dses(self):
        return self.datasources.keys()

    def update_cache(self):
        self._datasources = {ds['id']: ds for ds in common.db.select(self.table)}

    def set(self, ds, **kwargs):
        qvars = {
            'dsid': ds
        }
        rows_updated = common.db.update(self.table, "id=$dsid", vars=qvars, **kwargs)
        self.update_cache()
        return rows_updated == 1

    @staticmethod
    def validate_ds_name(name):
        return name == name.strip() and re.match(r'^[a-z][a-z0-9_ ]*$', name, re.I)

    def create_ds_tables(self, dsid):
        replacements = {"id": dsid}
        dbaccess.exec_sql(common.db, self.CREATE_SQL, replacements)
        return 0

    def create_datasource(self, name):
        if not self.validate_ds_name(name):
            return -1
        id = common.db.insert(self.table, name=name)
        r = self.create_ds_tables(id)
        return r

    def remove_datasource(self, id):
        settings = common.settings.settings
        ids = self.dses

        # check id is valid
        if id not in ids:
            raise KeyError("Invalid ID: {0} given; {1} available".format(id, ids))

        # select other data source in Settings
        alt_id = -1
        for n in ids:
            if n != id:
                alt_id = n
                break
        if alt_id == -1:
            raise IndexError("Cannot remove the last data source")
        common.settings.set(datasource=alt_id)

        # remove from live_dest if selected
        if _settings_['live_dest'] == id:
            common.settings.set(live_dest=None)

        # remove from Datasources
        common.db.delete(self.table, "id={0}".format(int(id)))
        # Drop relevant tables
        replacements = {"id": int(id)}
        dbaccess.exec_sql(common.db, self.DROP_SQL, replacements)
