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
        self.get_importer()

    def get_importer(self):
        try:
            try:
                m_importer = importlib.import_module("sam.importers." + self.log_format)
            except ImportError:
                m_importer = importlib.import_module("sam.importers.import_" + self.log_format)
            classes = filter(lambda x: x.endswith("Importer") and x != "BaseImporter", dir(m_importer))
            class_ = getattr(m_importer, classes[0])
            self.importer = class_()
            self.importer.subscription = self.sub
            self.importer.datasource = self.ds
        except Exception as e:
            print("Error acquiring importer.")
            print(e.message)
            self.importer = None

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