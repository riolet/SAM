import common
import web
import models.datasources


class Settings:
    SESSION_KEY = "_settings"
    TABLE = "Settings"
    
    def __init__(self, session, subscription):
        self.db = common.db
        self.sub = subscription
        self.where = web.reparam("subscription=$id", {'id': self.sub})
        self.storage = session

    def __getitem__(self, item):
        if not self.storage.get(Settings.SESSION_KEY):
            self.update_cache()
        return self.storage[Settings.SESSION_KEY][item]

    def __setitem__(self, k, value):
        if not self.storage.get(Settings.SESSION_KEY):
            self.update_cache()
        if k not in self.storage[Settings.SESSION_KEY]:
            raise KeyError("Cannot create new keys")
        else:
            # TODO: is there a better way to do this?
            self.set(**{k: value})

    def copy(self):
        if not self.storage.get(Settings.SESSION_KEY):
            self.update_cache()
        return self.storage[Settings.SESSION_KEY].copy()

    def keys(self):
        if not self.storage.get(Settings.SESSION_KEY):
            self.update_cache()
        return self.storage[Settings.SESSION_KEY].keys()

    def update_cache(self):
        rows = self.db.select(Settings.TABLE, where=self.where, limit=1).first()
        if rows is None:
            self.storage[Settings.SESSION_KEY] = {}
        else:
            self.storage[Settings.SESSION_KEY] = dict(rows)

    def clear_cache(self):
        self.storage[Settings.SESSION_KEY] = {}

    def set(self, **kwargs):
        datasources = models.datasources.Datasources(self.storage, self.sub)
        if 'datasource' in kwargs and kwargs['datasource'] not in datasources.datasources:
            raise ValueError("Invalid DS specified")

        common.db.update(Settings.TABLE, self.where, **kwargs)
        self.clear_cache()

    def create(self):
        # add default datasource for subscription
        dsModel = models.datasources.Datasources({}, self.sub)
        ds_id = dsModel.create_datasource()

        self.db.insert(Settings.TABLE, subscription=self.sub, datasource=ds_id)
