import constants


class User(object):
    def __init__(self, session=None):
        pass

    @property
    def email(self):
        return "demo@example.com"

    @email.setter
    def email(self, value):
        pass

    @property
    def name(self):
        return "SAM"

    @name.setter
    def name(self, value):
        pass

    @property
    def logged_in(self):
        return True

    @logged_in.setter
    def logged_in(self, value):
        pass

    @property
    def plan_active(self):
        return True

    @plan_active.setter
    def plan_active(self, value):
        pass

    @property
    def plan(self):
        return 'admin'

    @plan.setter
    def plan(self, value):
        pass

    @property
    def subscription(self):
        return constants.demo['id']

    @subscription.setter
    def subscription(self, value):
        pass

    @property
    def viewing(self):
        return constants.demo['id']

    @viewing.setter
    def viewing(self, value):
        pass

    @property
    def groups(self):
        return None

    @groups.setter
    def groups(self, value):
        pass

    def any_group(self, allowed):
        return True

    def all_groups(self, allowed):
        return True

    def may_post(self):
        return True
