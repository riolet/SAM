class SubscriptionMissingError(Exception): pass


class LoggedOutError(Exception): pass


class MalformedRequest(Exception):
    def __init__(self, message=None):
        if message:
            Exception.__init__(self, message)
        else:
            Exception.__init__(self)


class RequiredKey(MalformedRequest):
    def __init__(self, name, key, *args, **kwargs):
        self.message = "Missing key: {name} ('{key}') not specified.".format(name=name, key=key)
        MalformedRequest.__init__(self, self.message)


class AuthenticationError(Exception): pass
