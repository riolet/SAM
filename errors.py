class SubscriptionMissingError(Exception): pass


class LoggedOutError(Exception): pass


class MalformedRequest(Exception): pass


class RequiredKey(MalformedRequest):
    def __init__(self, name, key, *args, **kwargs):
        MalformedRequest.__init__(self, args, kwargs)
        self.message = "Missing key: {name} ('{key}') not specified.".format(name=name, key=key)
