import cPickle


class LiveProtocol(object):
    def __init__(self, sock, num_len=5):
        self.sock = sock
        self.num_len = 5

    def validate_password(self, password):
        if self.password:
            return self.password == password
        else:
            return True

    def send(self, message):
        encoded = cPickle.dumps(message)
        transmission_length = len(encoded) + self.num_len
        format_string = "{{0:0{0}d}}{{1}}".format(self.num_len)
        m = format_string.format(transmission_length, encoded)
        self.sock.sendall(m)

    def receive(self):
        chars = ""
        while len(chars) < self.num_len:
            chars += self.sock.recv(self.num_len)
        transmission_length = int(chars[:self.num_len])

        # TODO: this can hang if a connection is broken uncleanly
        while len(chars) < transmission_length:
            chars += self.sock.recv(1024)

        message = chars[self.num_len:transmission_length]
        return cPickle.loads(message)