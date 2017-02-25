import os
import math
import base64
import common


class LiveKeys:
    def __init__(self, subscription):
        self.db = common.db
        self.sub = subscription
        self.table_livekeys = "LiveKeys"
        self.table_ds = "Datasources"

    @staticmethod
    def b64_url_encode(bytes_string):
        return base64.b64encode(bytes_string, "-_")

    @staticmethod
    def generate_salt(length):
        """
        Generate a cryptographically secure random base64 code of the desired length
        :param length: The desired output string length
        :return: A base64 encoded salt
        """
        # base64 stores 6 bits per symbol but os.urandom gives 8 bits per symbol
        bytes_needed = int(math.ceil(length * 6.0 / 8.0))
        random_bytes = os.urandom(bytes_needed)
        encoded = LiveKeys.b64_url_encode(random_bytes)
        return encoded[:length]

    def create(self, datasource):
        key = LiveKeys.generate_salt(24)
        self.db.insert(self.table_livekeys, subscription=self.sub, datasource=datasource, access_key=key)
    
    def read(self):
        qvars = {
            'sub': self.sub,
        }
        query = """SELECT L.access_key, D.id AS 'ds_id', D.name AS 'datasource', L.subscription
        FROM {table_livekeys} AS `L`
        JOIN {table_datasources} AS `D`
            ON L.subscription = D.subscription AND L.datasource = D.id
        WHERE L.subscription=$sub""".format(table_livekeys=self.table_livekeys, table_datasources=self.table_ds)
        rows = self.db.query(query, vars=qvars)
        return list(map(dict, rows))

    def validate(self, key):
        qvars = {
            'key': key
        }
        rows = self.db.select(self.table_livekeys, where="access_key = $key", vars=qvars)
        return rows.first()

    def delete(self, key):
        qvars = {
            'sub': self.sub,
            'key': key
        }
        num_deleted = self.db.delete(self.table_livekeys, where='subscription=$sub AND access_key=$key', vars=qvars)
        return num_deleted

    def delete_ds(self, ds_id):
        qvars = {
            'id': ds_id
        }
        num_deleted = self.db.delete(self.table_livekeys, where='datasource = $id', vars = qvars)
        return num_deleted