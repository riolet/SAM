from sam import common
import web
import sam.models.datasources
import numbers


class Settings:
    SESSION_KEY = "_settings"
    TABLE = "Settings"
    
    def __init__(self, db, session, subscription):
        """
        :type db: web.DB
        :type session: dict
        :type subscription: numbers.Integral
        :param db: 
        :param session: 
        :param subscription: 
        """
        self.db = db
        self.sub = subscription
        self.where = web.reparam("subscription=$id", {'id': self.sub})
        self.storage = session

    def __getitem__(self, item):
        if not self.storage.get(Settings.SESSION_KEY) or not self.storage[Settings.SESSION_KEY].get(self.sub):
            self.update_cache()
        return self.storage[Settings.SESSION_KEY][self.sub][item]

    def __setitem__(self, k, value):
        if not self.storage.get(Settings.SESSION_KEY) or not self.storage[Settings.SESSION_KEY].get(self.sub):
            self.update_cache()
        if k not in self.storage[Settings.SESSION_KEY][self.sub]:
            raise KeyError("Cannot create new keys")
        else:
            # TODO: is there a better way to do this?
            self.set(**{k: value})

    def copy(self):
        if not self.storage.get(Settings.SESSION_KEY) or not self.storage[Settings.SESSION_KEY].get(self.sub):
            self.update_cache()
        return self.storage[Settings.SESSION_KEY][self.sub].copy()

    def keys(self):
        if not self.storage.get(Settings.SESSION_KEY) or not self.storage[Settings.SESSION_KEY].get(self.sub):
            self.update_cache()
        return self.storage[Settings.SESSION_KEY][self.sub].keys()

    def update_cache(self):
        rows = self.db.select(Settings.TABLE, where=self.where, limit=1).first()
        if Settings.SESSION_KEY not in self.storage:
            self.storage[Settings.SESSION_KEY] = {}
        if rows is None:
            self.storage[Settings.SESSION_KEY][self.sub] = {}
        else:
            self.storage[Settings.SESSION_KEY][self.sub] = dict(rows)

    def clear_cache(self):
        self.storage[Settings.SESSION_KEY] = {}

    def set(self, **kwargs):
        datasources = sam.models.datasources.Datasources(self.db, self.storage, self.sub)
        if 'datasource' in kwargs and kwargs['datasource'] not in datasources.datasources:
            raise ValueError("Invalid DS specified")

        common.db.update(Settings.TABLE, self.where, **kwargs)
        self.clear_cache()

    def create(self):
        # add default datasource for subscription
        dsModel = sam.models.datasources.Datasources(self.db, {}, self.sub)
        ds_id = dsModel.create_datasource()

        self.db.insert(Settings.TABLE, subscription=self.sub, datasource=ds_id)

    def delete_subscription(self):
        qvars = {
            'sid': self.sub
        }
        num_deleted = self.db.delete(Settings.TABLE, where='subscription=$sid', vars=qvars)
        return num_deleted
