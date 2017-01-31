import common


class Settings:
    def __init__(self):
        self.db = common.db
        self.table = "Settings"
        # TODO: store in session
        self._settings = {}
        self.update_cache()

    def __getitem__(self, item):
        return self._settings[item]

    def __len__(self):
        return len(self._settings)

    def __setitem__(self, k, value):
        if k not in self._settings:
            raise KeyError("Cannot create new keys")
        else:
            self.set(k=value)

    def __contains__(self, item):
        return item in self._settings

    def __delitem__(self, k):
        raise KeyError("Cannot delete keys")

    def __iter__(self):
        return iter(self._settings)

    def copy(self):
        return self._settings.copy()

    def keys(self):
        return self._settings.keys()

    def update_cache(self):
        self._settings.update(dict(self.db.select(self.table, limit=1).first()))

    def set(self, **kwargs):
        common.db.update(self.table, "1", **kwargs)
        self.update_cache()
