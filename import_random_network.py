"""Generate a random network"""

import random
import math
import sys
import common
import dbaccess
import traceback
from import_base import BaseImporter
from datetime import datetime
from time import time


class Node:
    def __init__(self, parent, ip, alias=""):
        self.alias = alias
        if parent is not None:
            self.address = "{0}.{1:d}".format(parent.address, ip)
        else:
            self.address = "{0:d}".format(ip)
        self.number = ip
        self.parent = parent
        self.client = False
        self.server = False
        self.children = {}
        self.ports = []
        self.init_ports()

    def init_ports(self):
        count = int(round(math.fabs(random.gauss(0, 5)) + 1))
        for i in range(count):
            self.ports.append(randomPort())

    def set_client(self, is_client):
        self.client = is_client

    def set_server(self, is_server):
        self.server = is_server

    def add_child(self, child):
        self.children[child.number] = child

    def random_host(self):
        if len(self.children) == 0:
            return self
        return random.choice(self.children.values()).random_host()

    def random_port(self):
        return random.choice(self.ports)

    def get_as_int(self):
        if self.parent is not None:
            return (self.parent.get_as_int() << 8) + self.number
        return self.number

    def can_add_source(self, source):
        return True

    def add_source(self, source):
        pass

    def can_add_dest(self, dest):
        return True

    def add_dest(self, dest):
        pass

    def __str__(self):
        return self.address

    def __repr__(self):
        return self.address

    def __eq__(self, other):
        return type(self) == type(other) and self.number == other.number and self.parent == other.parent

    def __ne__(self, other):
        return not self.__eq__(other)


# Generates a stream of numbers in range [1, 254].
def gen_ips(numerator):
    denominator = 254
    if numerator > denominator:
        raise Exception("Cannot yield more than " + str(denominator) + "ips")
    while numerator > 0:
        if random.randint(0, denominator) <= numerator:
            yield denominator
            numerator -= 1
        denominator -= 1
    return


def randomPort():
    rand = random.random()
    if rand < 0.07:
        return 80
    elif rand < 0.2:
        return 443
    elif random.random() < 0.8:
        return int(math.fabs(random.gauss(300, 300)))
    else:
        return random.randint(1024, 65535)


def generate_nodes():
    gen = gen_ips(3)
    c_cluster = gen.next()
    cs_cluster = gen.next()
    s_cluster = gen.next()

    # clients
    clients8 = Node(None, c_cluster, "clients")
    gen16 = gen_ips(random.randint(2, 5))  # 12.xx
    for ip16 in gen16:
        node16 = Node(clients8, ip16)
        gen24 = gen_ips(random.randint(1, 8))  # 12.34.xx
        for ip24 in gen24:
            node24 = Node(node16, ip24)
            gen32 = gen_ips(random.randint(1, 2))  # 12.34.56.xx
            for ip32 in gen32:
                node32 = Node(node24, ip32)
                node24.add_child(node32)
            node16.add_child(node24)
        clients8.add_child(node16)

    # clients and servers
    clients_and_servers8 = Node(None, cs_cluster, "clients and servers")
    gen16 = gen_ips(random.randint(2, 4))  # 12.xx
    for ip16 in gen16:
        node16 = Node(clients_and_servers8, ip16)
        gen24 = gen_ips(random.randint(1, 5))  # 12.34.xx
        for ip24 in gen24:
            node24 = Node(node16, ip24)
            gen32 = gen_ips(random.randint(1, 8))  # 12.34.56.xx
            for ip32 in gen32:
                node32 = Node(node24, ip32)
                node24.add_child(node32)
            node16.add_child(node24)
        clients_and_servers8.add_child(node16)

    # servers
    servers8 = Node(None, s_cluster, "servers")
    gen16 = gen_ips(random.randint(1, 2))  # 12.xx
    for ip16 in gen16:
        node16 = Node(servers8, ip16)
        gen24 = gen_ips(random.randint(8, 16))  # 12.34.xx
        for ip24 in gen24:
            node24 = Node(node16, ip24)
            gen32 = gen_ips(random.randint(1, 2))  # 12.34.56.xx
            for ip32 in gen32:
                node32 = Node(node24, ip32)
                node24.add_child(node32)
            node16.add_child(node24)
        servers8.add_child(node16)

    return clients8, clients_and_servers8, servers8


def print_node(node):
    print("{0:3d} - {1:s}".format(node.number, node.alias))
    for k16, client16 in node.children.items():
        print("{0:d}.{1:d}.".format(node.number, k16))
        for k24, client24 in client16.children.items():
            print("{0:d}.{1:d}.{2:d}.".format(node.number, k16, k24))
            for k32, client32 in client24.children.items():
                print("{0:d}.{1:d}.{2:d}.{3:d}".format(node.number, k16, k24, k32))


def count_leaves(node):
    if len(node.children) == 0:
        return 1
    count = 0
    for n in node.children.values():
        count += count_leaves(n)
    return count


def gen_links(c, cs, s):
    while True:
        # choose source
        rand = random.random()
        if rand < 0.7:
            source = c.random_host()
        elif rand < 0.995:
            source = cs.random_host()
        elif rand < 0.999:
            source = s.random_host()
        else:
            ip = random.randint(1, 254)
            ip = (ip << 8) | random.randint(1, 254)
            ip = (ip << 8) | random.randint(1, 254)
            ip = (ip << 8) | random.randint(1, 254)
            source = Node(None, ip)

        # choose dest
        rand = random.random()
        if rand < 0.6:
            dest = s.random_host()
        elif rand < 0.99:
            dest = cs.random_host()
        else:
            dest = c.random_host()

        if source == dest:
            continue

        if dest.can_add_source(source) and source.can_add_dest(dest):
            dest.add_source(source)
            source.add_dest(dest)
            occurences = int(math.fabs(random.gauss(0, 100))) + 1
            destPort = dest.random_port()
            for i in range(occurences):
                yield (source.get_as_int(), random.randint(16384, 65535), dest.get_as_int(), destPort)


def generate_time():
    one_week_in_seconds = 60 * 60 * 24 * 7
    now = time()
    then = now - random.random() * one_week_in_seconds
    return datetime.fromtimestamp(then).strftime("%Y-%m-%d %H:%M:%S")


class RandomImporter(BaseImporter):
    def __init__(self):
        BaseImporter.__init__(self)
        self.lines_to_import = 10000

    def main(self, argv):
        self.import_file(None)

    def import_file(self, path_in):
        line_num = 0
        lines_inserted = 0
        counter = 0
        row = {"SourceIP": "", "SourcePort": "", "DestinationIP": "", "DestinationPort": ""}
        rows = [row.copy() for i in range(1000)]
        c, cs, s = generate_nodes()
        gen = gen_links(c, cs, s)
        for i in range(self.lines_to_import):
            line_num += 1

            a, b, c, d = gen.next()
            rows[counter]["SourceIP"] = str(a)
            rows[counter]["SourcePort"] = str(b)
            rows[counter]["DestinationIP"] = str(c)
            rows[counter]["DestinationPort"] = str(d)
            rows[counter]["Timestamp"] = generate_time()

            counter += 1

            # Perform the actual insertion in batches of 1000
            if counter == 1000:
                insert_data(rows, counter)
                lines_inserted += counter
                counter = 0
        if counter != 0:
            insert_data(rows, counter)
            lines_inserted += counter
        print("Done. {0} lines processed, {1} rows inserted".format(line_num, lines_inserted))


def insert_data(rows, count):
    """
    Attempt to insert the first 'count' items in 'rows' into the database table `samapper`.`Syslog`.
    Exits script on critical failure.
    Args:
        rows: The iterable containing dictionaries to insert
            (dictionaries must all have the same keys, matching column names)
        count: The number of items from rows to insert

    Returns:
        None
    """
    try:
        truncated_rows = rows[:count]
        # >>> values = [{"name": "foo", "email": "foo@example.com"}, {"name": "bar", "email": "bar@example.com"}]
        # >>> db.multiple_insert('person', values=values, _test=True)
        common.db.multiple_insert('Syslog', values=truncated_rows)
    except Exception as e:
        # see http://dev.mysql.com/doc/refman/5.7/en/error-messages-server.html for codes
        if e[0] == 1049:  # Unknown database 'samapper'
            dbaccess.create_database()
            insert_data(rows, count)
        elif e[0] == 1045:  # Access Denied for '%s'@'%s' (using password: (YES|NO))
            print(e[1])
            print("Check your username / password? (dbconfig_local.py)")
            sys.exit(1)
        else:
            print("Critical failure.")
            print(e.message)
            print '-' * 60
            traceback.print_exc(file=sys.stdout)
            print '-' * 60
            sys.exit(2)


# If running as a script, begin by executing main.
if __name__ == "__main__":
    importer = RandomImporter()
    importer.main(sys.argv)
