from sam import common, integrity


class DBPlugin(object):
    @staticmethod
    def checkIntegrity(db):
        """
        Checks if the database is correct and returns the equivalent to false if db is consistent.
        if db is healthy, return False, 
            examples: False, 0, [] or {}
        if db is unhealthy return something useful for the fixIntegrity function, such as a list of missing tables
            example: {'missing': ['s1_mytable', 's3_mytable'], 'malformed': ['s2_mytable']} 
        
        :param db: database connection
        :return: False or equivalent iff consistent.
        """
        raise NotImplementedError

    @staticmethod
    def fixIntegrity(db, errors):
        """
        
        :param db: database connection 
        :param errors: the result of checkIntegrity function, ideally with helpful info on what to fix.
        :return: True if fixed, False if failed to fix.
        """
        raise NotImplementedError

    @staticmethod
    def simple_sub_table_check(*table_format_strings):
        @staticmethod
        def check(db):
            all_tables = set(integrity.get_table_names(db))
            subs = integrity.get_all_subs(db)
            missing = []
            for sub_id in subs:
                for fstring in table_format_strings:
                    if fstring.format(acct=sub_id) not in all_tables:
                        missing.append(sub_id)

            if not missing:
                return {}
            return {'missing': missing}
        return check

    @staticmethod
    def simple_sub_table_fix(**sql_scripts):
        @staticmethod
        def fix(db, errors):
            missing_table_subs = errors['missing']
            for sub_id in missing_table_subs:
                replacements = {
                    'acct': sub_id
                }
                with db.transaction():
                    if db.dbname in sql_scripts:
                        common.exec_sql(db, sql_scripts[db.dbname], replacements)
            return True
        return fix