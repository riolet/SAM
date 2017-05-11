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
