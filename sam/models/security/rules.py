import os
import cPickle
import web
from sam.models.security import rule_template, rule


class Rules():
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

    def clear(self):
        return self.db.delete(self.table, where="1")

    def count(self):
        rows = self.db.select(self.table, what="COUNT(0) AS 'count'")
        return rows.first()['count']

    def decode_row(self, row):
        if 'active' in row:
            row['active'] = row['active'] == 1
        if 'params' in row:
            row['params'] = cPickle.loads(str(row['params']))
        return row

    def row_to_rule(self, row):
        rule_obj = rule.Rule(row['id'], row['active'], row['name'], row['description'], row['rule_path'])
        params = row.get('params', {})
        action_params = params.get('actions', {})
        exposed_params = params.get('exposed', {})
        rule_obj.set_action_params(action_params)
        rule_obj.set_exposed_params(exposed_params)
        return rule_obj

    def add_rule(self, path, name, description, params):
        """
        :param path: file name: 'compromised.yml', 'plugin: compromised.yml', 'custom: compromised.yml'
        :type path: str
        :param name: Short rule name
        :type name: str
        :param description: Long description of rule
        :type description: str
        :param params: default parameters to use for rule customization
        :type params: dict
        """
        valid_path = rule_template.abs_rule_path(path)
        if valid_path is None:
            print("Rule definition path cannot be verified. Saving anyway.")

        if not isinstance(name, (str, unicode)) or len(name) == 0:
            raise ValueError("Name cannot be empty.")
        name = name.strip()

        if not isinstance(description, (str, unicode)):
            raise ValueError("Description must be a string.")
        description = description.strip()

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
        if 'actions' in edits or 'exposed' in edits:
            actions = edits.pop('actions', {})
            exposed = edits.pop('exposed', {})
            old_rule = self.get_rule(rule_id)
            old_rule.set_action_params(actions)
            old_rule.set_exposed_params(exposed)
            params = old_rule.export_params()
            edits['params'] = cPickle.dumps(params)
        q = self.db.update(self.table, where='id=$rid', vars=qvars, _test=True, **edits)
        self.db.update(self.table, where='id=$rid', vars=qvars, **edits)
