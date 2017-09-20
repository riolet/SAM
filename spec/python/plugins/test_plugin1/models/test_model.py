import os
import time
import web
from sam.models import base

base_path = os.path.dirname(__file__)
sql_path = os.path.join(base_path, os.pardir, 'sql')


class TestModel(base.DBPlugin):
    TEST_TABLE = 's{acct}_test_table'

    checkIntegrity = base.DBPlugin.simple_sub_table_check(
        TEST_TABLE
    )

    fixIntegrity = base.DBPlugin.simple_sub_table_fix(
        sqlite=os.path.join(sql_path, 'create_test_table.sql'),
        mysql=os.path.join(sql_path, 'create_test_table.sql')
    )
