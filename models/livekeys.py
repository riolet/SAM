import os
import math
import base64
import common


class LiveKeys:
    def __init__(self, subscription=None):
        self.db = common.db
        self.sub = subscription or common.get_subscription()
        self.table = "LiveKeys"

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
        key = LiveKeys.generate_salt(64)
        self.db.insert(self.table, subscription=self.sub, datasource=datasource, access_key=key)
    
    def read(self):
        qvars = {
            'sub': self.sub,
        }
        rows = self.db.select(self.table, where='subscription=$sub', vars=qvars)
        return list(rows)
        
    def delete(self, key):
        qvars = {
            'sub': self.sub,
            'key': key
        }
        num_deleted = self.db.delete(self.table, where='subscription=$sub AND access_key=$key', vars=qvars)
        return num_deleted
