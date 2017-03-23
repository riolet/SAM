import constants


class User(object):
    def __init__(self, session):
        self.session = session

    def login(self, email, name, subscription, groups, plan, active):
        self.email = email
        self.name = name
        self.logged_in = True
        self.subscription = subscription
        self.viewing = subscription
        self.groups = groups.split()
        self.plan = plan
        self.plan_active = active

    def logout(self):
        self.email = ""
        self.name = None
        self.logged_in = False
        self.subscription = None
        self.viewing = constants.demo['id']
        self.groups = set()
        self.plan = None
        self.plan_active = False

    @property
    def email(self):
        return self.session.get('user_email', "")

    @email.setter
    def email(self, value):
        self.session['user_email'] = value

    @property
    def name(self):
        return self.session.get('user_name', None)

    @name.setter
    def name(self, value):
        self.session['user_name'] = value

    @property
    def logged_in(self):
        return self.session.get('user_logged_in', False)

    @logged_in.setter
    def logged_in(self, value):
        self.session['user_logged_in'] = bool(value)

    @property
    def plan_active(self):
        return self.session.get('user_plan_active', False)

    @plan_active.setter
    def plan_active(self, value):
        self.session['user_plan_active'] = bool(value)

    @property
    def plan(self):
        return self.session.get('user_plan', None)

    @plan.setter
    def plan(self, value):
        self.session['user_plan'] = value

    @property
    def subscription(self):
        return self.session.get('user_subscription', None)

    @subscription.setter
    def subscription(self, value):
        self.session['user_subscription'] = int(value)

    @property
    def viewing(self):
        return self.session.get('view_subscription', constants.demo['id'])

    @viewing.setter
    def viewing(self, value):
        self.session['view_subscription'] = int(value)

    @property
    def groups(self):
        groups = self.session.get('user_groups', set()).copy()

        if self.logged_in:
            groups.add('login')
        else:
            groups.add('logout')

        if self.may_post():
            groups.add('subscribed')
        else:
            groups.add('unsubscribed')

        if constants.debug:
            groups.add('debug')
        return groups

    @groups.setter
    def groups(self, value):
        saved = set(value).copy()
        saved.discard('login')
        saved.discard('logout')
        saved.discard('unsubscribed')
        saved.discard('subscribed')
        saved.discard('debug')
        self.session['user_groups'] = saved

    def any_group(self, allowed):
        local = set(self.groups)
        foreign = set(allowed)
        return len(local & foreign) > 0

    def all_groups(self, allowed):
        local = set(self.groups)
        foreign = set(allowed)
        return local & foreign == foreign

    def may_post(self):
        exists = self.subscription is not None
        owns = self.subscription == self.viewing
        has_plan = self.plan is not None and self.plan != 'none' and self.plan != ''
        plan_active = self.plan_active is True
        return exists and owns and has_plan and plan_active
