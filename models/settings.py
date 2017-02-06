import common
import web
import models.datasources


class Settings:
    def __init__(self, subscription=None):
        self.db = common.db
        self.sub = subscription or common.get_subscription()
        self.table = "Settings"
        self.where = web.reparam("subscription=$id", {'id': self.sub})
        # TODO: store in session
        self._settings = {}

    def __getitem__(self, item):
        if not self._settings:
            self.update_cache()
        return self._settings[item]

    def __setitem__(self, k, value):
        if not self._settings:
            self.update_cache()
        if k not in self._settings:
            raise KeyError("Cannot create new keys")
        else:
            # TODO: is there a better way to do this?
            self.set(**{k: value})

    def copy(self):
        if not self._settings:
            self.update_cache()
        return self._settings.copy()

    def keys(self):
        if not self._settings:
            self.update_cache()
        return self._settings.keys()

    def update_cache(self):
        self._settings = dict(self.db.select(self.table, where=self.where, limit=1).first())

    def clear_cache(self):
        self._settings = {}

    def set(self, **kwargs):
        datasources = models.datasources.Datasources(self.sub)
        if 'datasource' in kwargs and kwargs['datasource'] not in datasources.datasources:
            raise ValueError("Invalid DS specified")

        common.db.update(self.table, self.where, **kwargs)
        self.clear_cache()
