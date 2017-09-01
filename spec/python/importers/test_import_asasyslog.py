
import datetime
from sam.importers import import_base, import_asasyslog

sample_log = [
    "",
    "<166>%ASA-6-302014: Teardown TCP connection 7765 for outside:216.58.193.69/443 to inside:192.168.1.5/37904 duration 0:02:51 bytes 5670 TCP FINs",
    "%ASA-6-302014: Teardown TCP connection 7769 for outside:31.13.76.107/443 to inside:192.168.1.5/40518 duration 0:02:50 bytes 45939 TCP Reset-O",
    "<166>%ASA-6-302014: Teardown TCP connection 7767 for outside:157.240.2.20/443 to inside:192.168.1.5/45624 duration 0:02:50 bytes 5478 TCP FINs",
    "<166>%ASA-6-302015: Built outbound UDP connection 7776 for outside:192.168.10.254/53 (192.168.10.254/53) to inside:192.168.1.5/41767 (192.168.10.176/10612)",
    "<166>%ASA-6-302013: Built outbound TCP connection 7777 for outside:104.31.70.170/80 (104.31.70.170/80) to inside:192.168.1.5/44292 (192.168.10.176/13840)",
    "<166>%ASA-6-302013: Built outbound TCP connection 7778 for outside:104.31.70.170/80 (104.31.70.170/80) to inside:192.168.1.5/44294 (192.168.10.176/45281)",
    "<166>%ASA-6-302013: Built outbound TCP connection 7779 for outside:104.31.70.170/80 (104.31.70.170/80) to inside:192.168.1.5/44296 (192.168.10.176/13081)",
    "<166>%ASA-6-302014: Teardown TCP connection 7777 for outside :104.31.70.170 /80 (idfw_user1) to inside :192.168.1.5 /44292 (idfw_user2) duration 11:22:33 bytes 767157 TCP FINs",
    "<166>%ASA-6-302014: Teardown TCP connection 7779 for outside:104.31.70.170/80 to inside:192.168.1.5/44296 duration 0:00:46 bytes 816971 TCP FINs",
    "<166>%ASA-6-302014: Teardown TCP connection 7778 for outside:104.31.70.170/80 to inside:192.168.1.5/44294 duration 0:00:46 bytes 957709 TCP FINs",
    "<166>%ASA-6-302015: Built outbound UDP connection 7881 for outside:158.69.125.231/123 (158.69.125.231/123) to inside:192.168.1.8/59776 (192.168.10.176/22202)",
    "<166>%ASA-6-302016: Teardown UDP connection 7881 for outside:158.69.125.231/123 to inside:192.168.1.8/59776 duration 0:02:01 bytes 96",
    "<166>%ASA-6-302016: Teardown UDP connection 7881 for outside :158.69.125.231 /123 (idw_user1) to inside :192.168.1.8 /59776 (idfw_user2) duration 1 :2 :3 bytes 96 (user3)",

    "<166>%ASA-6-302015: Built inbound UDP connection 8179 for inside:192.168.1.6/68 (192.168.1.6/68) to identity:192.168.1.1/67 (192.168.1.1/67)",
    "<166>%ASA-6-302016: Teardown UDP connection 8179 for inside:192.168.1.7/68 to identity:192.168.1.1/67 duration 0:02:01 bytes 601",

    "<166>%ASA-6-302017: Built inbound GRE connection 7951 from inside:192.168.1.5/355 (192.168.1.5/355) (idfw_user1) to inside:192.168.1.1/55443 (192.168.10.176/23456)",
    "<166>%ASA-6-302018: Teardown GRE connection 7951 from inside:192.168.1.5/355 (192.168.1.5/355) (idfw_user1) to inside:192.168.1.1/55443 (192.168.10.176/23456) (idfw_user2) duration 0:02:31 bytes 66429 (user3)",

    "<166>%ASA-6-302020: Built outbound ICMP connection for faddr 216.58.216.174/0 gaddr 192.168.10.176/39510 laddr 192.168.1.5/27819",
    "<166>%ASA-6-302021: Teardown ICMP connection for faddr 216.58.216.174/0 gaddr 192.168.10.176/39510 laddr 192.168.1.5/27819",
    "<166>%ASA-6-302020: Built outbound ICMP connection for faddr 13.107.21.200/0 gaddr 192.168.10.176/9984 laddr 192.168.1.5/27820",
    "<166>%ASA-6-302021: Teardown ICMP connection for faddr 13.107.21.200/0 gaddr 192.168.10.176/9984 laddr 192.168.1.5/27820",
    "<166>%ASA-6-106015: Deny TCP (no connection) from 192.168.1.5/57682 to 192.168.1.1/443 flags FIN ACK  on interface inside",
    "",
    "nonsensical entry",
    "",
    "%ASA-6-106015: Deny TCP (no connection) from 216.58.216.177 /443 to 192.168.10.176/54321 flags ACK on interface eno1.",
    "%ASA-4-106023: Deny protocol src blah blah blah by access_group acl_ID [0x8ed66b60, 0xf8852875]",
    "%ASA-6-106100: access-list acl_ID blah blah blah hash codes",
    "%ASA-6-302013: Built inbound TCP connection_id for eno1 blah blah",
    "%ASA-6-302015: Built outbound UDP connection number for eno1 blah blah",
    "%ASA-6-302017: Built outbound GRE connection id from eno1 blah blah",
    "%ASA-6-302020: Built inbound ICMP connection for blah blah",
    "%ASA-3-313001: Denied ICMP type=number , code=code from IP_address on interface interface_name",
    "%ASA-3-313008: Denied ICMPv6 type=number , code=code from IP_address on interface interface_name",
    "%ASA-3-710003: {TCP|UDP} access denied by ACL from source_IP/source_port to interface_name :dest_IP/service",
    "",
]


def test_class():
    assert import_asasyslog.class_ == import_asasyslog.ASASyslogImporter


def test_get_message_id():
    asa = import_asasyslog.ASASyslogImporter()

    line = "<166>%ASA-6-302020: Built"
    assert asa.get_message_id(line) == (302020, "Built")

    line = '<166>:%ASA-session-6-302015: Built'
    assert asa.get_message_id(line) == (302015, "Built")


def test_timestring_to_seconds():
    asa = import_asasyslog.ASASyslogImporter()

    assert asa.timestring_to_seconds("50") == 50
    assert asa.timestring_to_seconds("1:30") == 90
    assert asa.timestring_to_seconds("01:30") == 90
    assert asa.timestring_to_seconds("00:01:30") == 90
    assert asa.timestring_to_seconds("00:50:00") == 50*60
    assert asa.timestring_to_seconds("01:00:00") == 1*60*60
    assert asa.timestring_to_seconds("10:10:10") == 10*60*60 + 10*60 + 10


def test_decode_tcp():
    asa = import_asasyslog.ASASyslogImporter()

    msg = "Teardown TCP connection 7765 for outside:216.58.193.69/443 to inside:192.168.1.5/37904 duration 0:02:51 bytes 5670 TCP FINs"
    decoded = asa.decode_tcp(msg)
    expected = {
        'dst': '216.58.193.69',
        'dstport': '443',
        'src': '192.168.1.5',
        'srcport': '37904',
        'duration': 171,
        'bytes_received': '5670',
        'protocol': 'TCP'
    }
    assert decoded == expected

    msg = "Teardown TCP connection 7777 for outside :104.31.70.170 /80 (idfw_user1) to inside :192.168.1.5 /44292 (idfw_user2) duration 11:22:33 bytes 767157 TCP FINs"
    decoded = asa.decode_tcp(msg)
    expected = {
        'dst': '104.31.70.170',
        'dstport': '80',
        'src': '192.168.1.5',
        'srcport': '44292',
        'duration': 40953,
        'bytes_received': '767157',
        'protocol': 'TCP'
    }
    assert decoded == expected


def test_decode_udp():
    asa = import_asasyslog.ASASyslogImporter()

    msg = "Teardown TCP connection 7765 for outside:216.58.193.69/443 to inside:192.168.1.5/37904 duration 0:02:51 bytes 5670 TCP FINs"
    decoded = asa.decode_tcp(msg)
    expected = {
        'dst': '216.58.193.69',
        'dstport': '443',
        'src': '192.168.1.5',
        'srcport': '37904',
        'duration': 171,
        'bytes_received': '5670',
        'protocol': 'TCP'
    }
    assert decoded == expected

    msg = "Teardown TCP connection 7777 for outside :104.31.70.170 /80 (idfw_user1) to inside :192.168.1.5 /44292 (idfw_user2) duration 11:22:33 bytes 767157 TCP FINs"
    decoded = asa.decode_tcp(msg)
    expected = {
        'dst': '104.31.70.170',
        'dstport': '80',
        'src': '192.168.1.5',
        'srcport': '44292',
        'duration': 40953,
        'bytes_received': '767157',
        'protocol': 'TCP'
    }
    assert decoded == expected


def test_decode_gre():
    asa = import_asasyslog.ASASyslogImporter()

    msg = "Teardown GRE connection 7951 from inside:192.168.1.5/3316 (192.168.1.5/3316) to inside:192.168.1.1/55443 (192.168.10.176/23456) duration 0:02:31 bytes 66429"
    decoded = asa.decode_gre(msg)
    expected = {
        'dst': '192.168.1.1',
        'dstport': '55443',
        'src': '192.168.1.5',
        'srcport': '3316',
        'duration': 151,
        'bytes_received': '66429',
        'protocol': 'GRE'
    }
    assert decoded == expected

    msg = "Teardown GRE connection 7951 from inside:192.168.1.5/3316 (192.168.1.5/3316) (idfw_user1) to inside:192.168.1.1/55443 (192.168.10.176/23456) (idfw_user2) duration 0:02:31 bytes 66429 (user3)"
    decoded = asa.decode_gre(msg)
    expected = {
        'dst': '192.168.1.1',
        'dstport': '55443',
        'src': '192.168.1.5',
        'srcport': '3316',
        'duration': 151,
        'bytes_received': '66429',
        'protocol': 'GRE'
    }
    assert decoded == expected


def test_decode_icmp():
    asa = import_asasyslog.ASASyslogImporter()

    msg = "Teardown ICMP connection for faddr 216.58.216.174/0 gaddr 192.168.10.176/39510 laddr 192.168.1.5/27819"
    decoded = asa.decode_icmp(msg)
    expected = {
        'dst': '216.58.216.174',
        'dstport': '0',
        'src': '192.168.1.5',
        'srcport': '27819',
        'duration': 1,
        'bytes_received': '1',
        'protocol': 'ICMP'
    }
    assert decoded == expected

    msg = "Teardown ICMP connection for faddr 216.58.216.174 /0 (you) gaddr 192.168.10.176 /39510 laddr 192.168.1.5 /27819 (you) (981) type something code 44"
    decoded = asa.decode_icmp(msg)
    expected = {
        'dst': '216.58.216.174',
        'dstport': '0',
        'src': '192.168.1.5',
        'srcport': '27819',
        'duration': 1,
        'bytes_received': '1',
        'protocol': 'ICMP'
    }
    assert decoded == expected


def test_translate():
    asa = import_asasyslog.ASASyslogImporter()

    translated_lines = []
    for i, line in enumerate(sample_log):
        d = {}
        r = asa.translate(line, i+1, d)
        print("Line {}: returned {}.  msg: {}...".format(i, r, line[:32]))
        if r == 0:
            assert set(d.keys()) == set(import_base.BaseImporter.keys)
            translated_lines.append(d)

    assert len(translated_lines) == 12

    err1 = "<166>%ASA-6-302015: Built outbound UDP connection 7881 for outside:158.69.125.231/123 (158.69.125.231/123) to inside:192.168.1.8/59776 (192.168.10.176/22202)"
    assert asa.translate(err1, 1, {}) == 1
    err3 = "<166>%ASA-6-302021: Teardown ICMP connection for CORRUPT faddr 13.107.21.200/0 gaddr 192.168.10.176/9984 laddr 192.168.1.5/27820"
    assert asa.translate(err3, 1, {}) == 3
    err4 = "<166>%ASA-6-302016: Teardown UDP connection 7881 for outside:158.69.125.231/123 to inside:192.168.1.8/59776 duration 0:02:01 bytes 96"
    old_dt = datetime.datetime
    try:
        def bad_dt():
            raise AssertionError
        datetime.datetime = bad_dt
        assert asa.translate(err4, 1, {}) == 4
    except:
        assert False
    finally:
        datetime.datetime = old_dt
