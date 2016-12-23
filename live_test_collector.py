import socket
import time
import signal
import random
import ssl
import live_protocol


SERVER = ("localhost", 8081)
PASSCODE = b'not-so-secret-passcode'


ALIVE = True


def rand_word():
    scrabble_dist = 'e'*12 + 'a'*9 + 'i'*9 + 'o'*8 + 'n'*6 + 'r'*6 \
                    + 't'*6 + 'l'*4 + 's'*4 + 'u'*4 + 'd'*4 + 'g'*3 \
                    + 'b'*2 + 'c'*2 + 'm'*2 + 'p'*2 + 'f'*2 + 'h'*2 \
                    + 'v'*2 + 'w'*2 + 'y'*2 + 'kjxqz'
    vowels = 'e'*12 + 'a'*9 + 'i'*9 + 'o'*8 + 'u'*4 + 'y'
    consonants = 'n'*6 + 'r'*6 \
                    + 't'*6 + 'l'*4 + 's'*4 + 'd'*4 + 'g'*3 \
                    + 'b'*2 + 'c'*2 + 'm'*2 + 'p'*2 + 'f'*2 + 'h'*2 \
                    + 'v'*2 + 'w'*2 + 'y'*2 + 'kjxqz'
    consonant_length = '111111111111111111122222334'
    vowel_length = '11111111111111112222223'
    num_syllables = '11112222223334'
    words_length = '11222334'

    # build word
    words = []
    for word in range(int(random.choice(words_length))):
        first = random.choice(scrabble_dist)
        syls = int(random.choice(num_syllables))
        if first in vowels:
            word_pieces = [first]
            word_pieces.extend([rand_syl(vowels, consonants, consonant_length, vowel_length, '0') for s in range(syls)])
        else:
            word_pieces = [first]
            word_pieces.extend([rand_syl(vowels, consonants, '0', vowel_length, consonant_length) for s in range(syls)])
        words.append("".join(word_pieces))
    return " ".join(words)


def rand_syl(vowels, consonants, c_len1, v_len, c_len2):
    cl_1 = int(random.choice(c_len1))
    cl_2 = int(random.choice(c_len2))
    vl = int(random.choice(v_len))
    word = []
    for c in range(cl_1):
        word.append(random.choice(consonants))
    for v in range(vl):
        word.append(random.choice(vowels))
    for c in range(cl_2):
        word.append(random.choice(consonants))
    return "".join(word)


def signal_handler(sig, frame):
    print("\nInterrupt received")
    global ALIVE
    ALIVE = False


def transact(address, message):
    global ALIVE
    global PASSCODE
    plain_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ssl_sock = ssl.wrap_socket(plain_sock,
                               ca_certs="cert.pem",
                               cert_reqs=ssl.CERT_REQUIRED,
                               ssl_version=ssl.PROTOCOL_TLSv1_2)

    if random.random() < 0.5:
        translator = live_protocol.LiveProtocol(ssl_sock, PASSCODE)
    else:
        translator = live_protocol.LiveProtocol(ssl_sock)
    try:
        print("SOCKET: Opening...")
        ssl_sock.connect(address)
        print("SOCKET: SSL Version is: {0}".format(ssl_sock.version()))

        print("SOCKET: Sending {0} chars. {1}...".format(len(message), repr(message[:50])))
        encoded = translator.encode(message)
        translator.send(encoded)

        response = translator.receive()
        print("SOCKET: Receiving: {0} chars. {1}...".format(len(response), repr(response[:50])))
        ssl_sock.close()
    except socket.error as e:
        print("SOCKET: Could not connect to socket {0}:{1}".format(*address))
        print("SOCKET: Error {0}: {1}".format(e.errno, e.strerror))


def client_loop():
    global ALIVE
    buffer = []
    print("buffer:")
    while ALIVE:
        new_word = rand_word()
        buffer.append(new_word)
        print(" + {0}".format(new_word))
        if len(buffer) >= 5:
            print("{0} messages. Sending!".format(len(buffer)))
            transact(SERVER, "\n".join(buffer))
            buffer = []
            print("buffer cleared.")
            print("buffer:")
        time.sleep(1)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    client_loop()