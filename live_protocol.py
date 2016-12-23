class PasswordError(Exception):
    pass


class LiveProtocol(object):
    def __init__(self, sock, password=None, num_len=5):
        self.sock = sock
        self.password = password
        self.num_len = 5

    def validate_password(self, password):
        if self.password:
            return self.password == password
        else:
            return True

    def encode(self, message):
        if self.password is None:
            print("PROTOCOL: adding empty password")
            return "{0}{1}".format("0"*self.num_len, message)

        print("PROTOCOL: adding password")
        pass_len = len(self.password)
        format_string = "{{0:0{0}d}}{{1}}{{2}}".format(self.num_len)
        encoded = format_string.format(pass_len, self.password, message)
        return encoded

    def decode(self, message):
        i = 0
        j = self.num_len
        pass_len = int(message[i:j])
        i = j
        j += pass_len
        password = message[i:j]
        decoded_message = message[j:]

        if self.validate_password(password):
            print("PROTOCOL: Passwords match!")
            return decoded_message
        else:
            print("PROTOCOL: Passwords do not match!")
            raise PasswordError("Password doesn't match.")

    def send(self, message):
        l = len(message) + self.num_len
        format_string = "{{0:0{0}d}}{{1}}".format(self.num_len)
        m = format_string.format(l, message)
        self.sock.sendall(m)

    def receive(self):
        chars = ""
        while len(chars) < self.num_len:
            chars += self.sock.recv(self.num_len)
        transmission_length = int(chars[:self.num_len])

        while len(chars) < transmission_length:
            chars += self.sock.recv(1024)

        return chars[self.num_len:transmission_length]