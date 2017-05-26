import os
import cPickle
import web
from sam.models.base import DBPlugin
from sam import integrity, common
from sam.models import rule_template, rule

BASE_PATH = os.path.dirname(__file__)
# db: RULES(id, rule_path, active, name, description, params)


class Rules(DBPlugin):
    TABLE_FORMAT = "s{}_Rules"

    def __init__(self, db, sub_id):
        """
        :param db: database connection
         :type db: web.DB
        :param sub_id: subscription id
         :type sub_id: int
        """
        self.db = db
        self.sub = sub_id
        self.table = Rules.TABLE_FORMAT.format(self.sub)
        self.rules = []

    def decode_row(self, row):
        if 'active' in row:
            row['active'] = row['active'] == 1
        if 'params' in row:
            row['params'] = cPickle.loads(str(row['params']))
        return row

    def row_to_rule(self, row):
        rule_obj = rule.Rule(row.id, row.active, row.name, row.description, row.rule_path)
        if 'params' in row:
            rule_obj.set_params(row.params)
        return rule_obj

    def add_rule(self, path, name, description, params):
        valid_path = rule_template.abs_rule_path(path)
        if valid_path is None:
            print("Rule definition path cannot be verified. Saving anyway.")

        name = name.strip()
        if not isinstance(name, (str, unicode)) or len(name) == 0:
            raise ValueError("Name cannot be empty.")

        description = description.strip()
        if not isinstance(description, (str, unicode)):
            raise ValueError("Description must be a string.")

        self.db.insert(self.table, active=True, rule_path=path,
                       name=name, description=description,
                       params=cPickle.dumps(params))

    def get_all_rules(self):
        """
        :return: All the security rules, briefly
         :rtype: list[ rule.Rule ]
        """
        rows = list(self.db.select(self.table, what="id, rule_path, active, name, description"))
        decoded = map(self.decode_row, rows)
        rule_objs = list(map(self.row_to_rule, decoded))
        return rule_objs

    def get_ruleset(self):
        """
        :return: All the active security rules, fully
         :rtype: list[ rule.Rule ]
        """
        rows = list(self.db.select(self.table, where="active=1"))
        decoded = map(self.decode_row, rows)
        rule_objs = list(map(self.row_to_rule, decoded))
        return rule_objs

    def get_rule(self, rule_id):
        qvars = {
            'rid': rule_id
        }
        rows = self.db.select(self.table, where='id=$rid', vars=qvars, limit=1)
        row = rows.first()
        if row is None:
            return None
        self.decode_row(row)
        rule_obj = self.row_to_rule(row)
        return rule_obj

    def delete_rule(self, rule_id):
        qvars = {
            'rid': rule_id
        }
        num_rows_deleted = self.db.delete(self.table, where='id=$rid', vars=qvars)
        return num_rows_deleted

    def edit_rule(self, rule_id, edits):
        qvars = {
            'rid': rule_id
        }
        if 'params' in edits:
            old_rule = self.get_rule(rule_id)
            old_rule.set_params(edits['params'])
            params = old_rule.export_params()
            edits['params'] = cPickle.dumps(params)
        self.db.update(self.table, where='id=$rid', vars=qvars, **edits)

    def validate_params(self, rule_id, params):
        old = self.get_rule(rule_id)


    @staticmethod
    def checkIntegrity(db):
        all_tables = set(integrity.get_table_names(db))
        subs = integrity.get_all_subs(db)
        missing = []
        for sub_id in subs:
            if Rules.TABLE_FORMAT.format(sub_id) not in all_tables:
                missing.append(sub_id)

        if not missing:
            return {}
        return {'missing': missing}

    @staticmethod
    def fixIntegrity(db, errors):
        missing_table_subs = errors['missing']
        for sub_id in missing_table_subs:
            replacements = {
                'acct': sub_id
            }
            with db.transaction():
                if db.dbname == 'sqlite':
                    common.exec_sql(db, os.path.join(BASE_PATH, '../sql/create_rules_sqlite.sql'), replacements)
                else:
                    common.exec_sql(db, os.path.join(BASE_PATH, '../sql/create_rules_mysql.sql'), replacements)
        return True
