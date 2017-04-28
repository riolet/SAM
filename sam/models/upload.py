from sam.importers import import_base
import importlib
from sam import preprocess
import web


class Uploader(object):
    def __init__(self, db, subscription, ds, log_format):
        """
        :type db: web.DB
        :type subscription: int
        :type ds: int
        :type log_format: unicode
        :param db: 
        :param subscription: 
        :param ds: 
        :param log_format: 
        """
        self.db = db
        self.sub = subscription
        self.ds = ds
        self.log_format = log_format.lower()
        self.importer = None
        self.preprocessor = None
        self.importer = import_base.get_importer(self.log_format, self.sub, self.ds)

    def run_import(self, data):
        if self.importer is None:
            print("No importer. Can't run it.")
            return 0

        return self.importer.import_string(data)

    def run_prepro(self):
        print("Running preprocessor")
        processor = preprocess.Preprocessor(self.db, self.sub, self.ds)
        processor.run_all()

    def import_log(self, data):
        print("Running import script")
        self.run_import(data)
        print("Running preprocessing script")
        self.run_prepro()