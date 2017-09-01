import sys
import re
from sam.importers.import_base import BaseImporter
import datetime
import time
import traceback

"""
Message types and explanations.
From:
https://www.cisco.com/c/en/us/td/docs/security/asa/syslog/b_syslog.html

not used:
%ASA-6-106015: Deny TCP (no connection) from IP_address /port to IP_address /port flags tcp_flags on interface interface_name.
%ASA-4-106023: Deny protocol src [interface_name :source_address /source_port ] [([idfw_user |FQDN_string ], sg_info )] dst interface_name :dest_address /dest_port [([idfw_user |FQDN_string ], sg_info )] [type {string }, code {code }] by access_group acl_ID [0x8ed66b60, 0xf8852875]
%ASA-6-106100: access-list acl_ID {permitted | denied | est-allowed} protocol interface_name /source_address (source_port ) (idfw_user , sg_info ) interface_name /dest_address (dest_port ) (idfw_user , sg_info ) hit-cnt number ({first hit | number -second interval}) hash codes
%ASA-6-302013: Built {inbound|outbound} TCP connection_id for interface :real-address /real-port (mapped-address/mapped-port ) [(idfw_user )] to interface :real-address /real-port (mapped-address/mapped-port ) [(idfw_user )] [(user )]
%ASA-6-302015: Built {inbound|outbound} UDP connection number for interface_name :real_address /real_port (mapped_address /mapped_port ) [(idfw_user )] to interface_name :real_address /real_port (mapped_address /mapped_port )[(idfw_user )] [(user )]
%ASA-6-302017: Built {inbound|outbound} GRE connection id from interface :real_address (translated_address ) [(idfw_user )] to interface :real_address /real_cid (translated_address /translated_cid ) [(idfw_user )] [(user )
%ASA-6-302020: Built {in | out} bound ICMP connection for faddr {faddr | icmp_seq_num } [(idfw_user )] gaddr {gaddr | cmp_type } laddr laddr [(idfw_user )] type {type } code {code }
%ASA-3-313001: Denied ICMP type=number , code=code from IP_address on interface interface_name
%ASA-3-313008: Denied ICMPv6 type=number , code=code from IP_address on interface interface_name 
%ASA-3-710003: {TCP|UDP} access denied by ACL from source_IP/source_port to interface_name :dest_IP/service

Connections appear twice: once as built, and once as torn down. 
The torn down iteration includes duration/bytes and therefore is more useful. 
used:
%ASA-6-302014: Teardown TCP connection id for interface :real-address /real-port [(idfw_user )] to interface :real-address /real-port [(idfw_user )] duration hh:mm:ss bytes bytes [reason ] [(user )]
%ASA-6-302016: Teardown UDP connection number for interface :real-address /real-port [(idfw_user )] to interface :real-address /real-port [(idfw_user )] duration hh :mm :ss bytes bytes [(user )]
%ASA-6-302018: Teardown GRE connection id from interface :real_address (translated_address ) [(idfw_user )] to interface :real_address /real_cid (translated_address /translated_cid ) [(idfw_user )] duration hh :mm :ss bytes bytes [(user )] 
%ASA-6-302021: Teardown ICMP connection for faddr {faddr | icmp_seq_num } [(idfw_user )] gaddr {gaddr | cmp_type } laddr laddr [(idfw_user )] (981) type {type } code {code }
"""


class ASASyslogImporter(BaseImporter):
    TRAFFIC_SYSLOG_CODES = {
        '106015', '106023', '106100', '302013', '302014',
        '302015', '302016', '302017', '302018', '302020',
        '302021', '313001', '313008', '710003'
    }
    ACCEPTED_CODES = {302014, 302016, 302018, 302021}

    message_regex = re.compile(r"^[<>:%\w\-]+-(\d+):\s+(.+)$")
    tcp_regex = re.compile(r"^Teardown TCP connection (?P<connection>\d+) for (?P<dst_interface>\w+)\s*:(?P<dst>[\d\.]+)\s*\/(?P<dstport>\d+) (?:\(\w+\)\s)?to (?P<src_interface>\w+)\s*:(?P<src>[\d\.]+)\s*\/(?P<srcport>\d+) (?:\(\w+\)\s)?duration (?P<duration>[\d:\s]+) bytes (?P<bytes>\d+).*$")
    udp_regex = re.compile(r"^Teardown UDP connection (?P<connection>\d+) for (?P<dst_interface>\w+)\s*:(?P<dst>[\d\.]+)\s*\/(?P<dstport>\d+) (?:\(\w+\)\s)?to (?P<src_interface>\w+)\s*:(?P<src>[\d\.]+)\s*\/(?P<srcport>\d+) (?:\(\w+\)\s)?duration (?P<duration>[\d:\s]+) bytes (?P<bytes>\d+).*$")
    icmp_regex = re.compile(r"^Teardown ICMP connection for faddr (?P<faddr>[\d.]+)\s*\/(?P<faddrport>\d+) (?P<idw_user1>\(\w+\)\s)?gaddr (?P<gaddr>[\d.]+)\s*\/(?P<gaddrport>\d+) laddr (?P<laddr>[\d.]+)\s*\/(?P<laddrport>\d+)(?P<idw_user2>\s?\(\w+\)\s)?.*$")
    gre_regex = re.compile(r"^Teardown GRE connection (?P<connection>\d+) from (?P<src_iface>\w+):(?P<src>[\d.]+)\s*\/(?P<srcport>\d+) \([\d./]*\) (?P<idw_user1>\(\w+\)\s)?to (?P<dst_iface>\w+):(?P<dst>[\d.]+)\s*\/(?P<dstport>\d+) \([\d./]*\) (?P<idw_user2>\(\w+\)\s)?duration (?P<duration>[\d:\s]+) bytes (?P<bytes>\d+).*$")

    def get_message_id(self, line):
        """
        :param line: syslog line
        :type line: str
        :return: the message id and the rest of the syslog line
        :rtype: tuple [ int, str ]
        """
        # line may start:
        #    <166>:%ASA-session-6-302015: ...
        #       or
        #    <166>%ASA-6-302015: ...
        match = ASASyslogImporter.message_regex.match(line)
        if match:
            return int(match.group(1)), match.group(2)
        else:
            return None, line

    def timestring_to_seconds(self, ts):
        seconds = 0
        for num in ts.split(":"):
            try:
                s = int(num)
                seconds *= 60
                seconds += s
            except:
                pass
        return seconds

    def decode_tcp(self, msg):
        # Teardown TCP connection id for interface :real-address /real-port [(idfw_user )] to interface :real-address /real-port [(idfw_user )] duration hh:mm:ss bytes bytes [reason ] [(user )]
        # Teardown TCP connection 7779 for outside:104.31.70.170/80 to inside:192.168.1.5/44296 duration 0:00:46 bytes 816971 TCP FINs
        match = ASASyslogImporter.tcp_regex.match(msg)
        if not match:
            return None
        regexed = match.groupdict()

        decoded = {
            'dst': regexed['dst'],
            'dstport': regexed['dstport'],
            'src': regexed['src'],
            'srcport': regexed['srcport'],
            'bytes_received': regexed['bytes'],
            'duration': self.timestring_to_seconds(regexed['duration']),
            'protocol': 'TCP',
        }

        return decoded

    def decode_udp(self, msg):
        # Teardown UDP connection number for interface :real-address /real-port [(idfw_user )] to interface :real-address /real-port [(idfw_user )] duration hh :mm :ss bytes bytes [(user )]
        # Teardown UDP connection 7881 for outside:158.69.125.231/123 to inside:192.168.1.8/59776 duration 0:02:01 bytes 96
        match = ASASyslogImporter.udp_regex.match(msg)
        if not match:
            return None
        regexed = match.groupdict()

        decoded = {
            'dst': regexed['dst'],
            'dstport': regexed['dstport'],
            'src': regexed['src'],
            'srcport': regexed['srcport'],
            'bytes_received': regexed['bytes'],
            'duration': self.timestring_to_seconds(regexed['duration']),
            'protocol': 'UDP',
        }

        return decoded

    def decode_gre(self, msg):
        # TODO: developed from specification not observation. May not be exact.
        # Teardown GRE connection id from interface :real_address (translated_address ) [(idfw_user )] to interface :real_address /real_cid (translated_address /translated_cid ) [(idfw_user )] duration hh :mm :ss bytes bytes [(user )]
        # Teardown GRE connection 7951 from outside:158.69.125.231/123 (158.69.125.231/123) [(idfw_user )] to inside:192.168.1.1/55443 (192.168.10.176/23456) duration 0:02:31 bytes 66429
        match = ASASyslogImporter.gre_regex.match(msg)
        if not match:
            return None
        regexed = match.groupdict()

        decoded = {
            'dst': regexed['dst'],
            'dstport': regexed['dstport'],
            'src': regexed['src'],
            'srcport': regexed['srcport'],
            'bytes_received': regexed['bytes'],
            'duration': self.timestring_to_seconds(regexed['duration']),
            'protocol': 'GRE',
        }

        return decoded

    def decode_icmp(self, msg):
        # Teardown ICMP connection for faddr {faddr | icmp_seq_num } [(idfw_user )] gaddr {gaddr | cmp_type } laddr laddr [(idfw_user )] (981) type {type } code {code }
        # Teardown ICMP connection for faddr 13.107.21.200/0 gaddr 192.168.10.176/9984 laddr 192.168.1.5/27820
        match = ASASyslogImporter.icmp_regex.match(msg)
        if not match:
            return None
        regexed = match.groupdict()

        decoded = {
            'dst': regexed['faddr'],
            'dstport': regexed['faddrport'],
            'src': regexed['laddr'],
            'srcport': regexed['laddrport'],
            'bytes_received': '1',
            'duration': 1,
            'protocol': 'ICMP',
        }

        return decoded

    def translate(self, line, line_num, dictionary):
        """
        Converts a given syslog line into a dictionary of (ip, port, ip, port)
        Args:
            line: The syslog line to parse
            line_num: The line number, for error printouts
            dictionary: The dictionary to write key/values pairs into

        Returns:
            0 on success and non-zero on error.
            1 => The message_id isn't useful.
            2 => message_id not handled
            3 => could not decode message
            4 => other error putting keys in dictionary
        """
        # determine message_id:
        message_id, message = self.get_message_id(line)

        # only accept particular messages
        if message_id not in ASASyslogImporter.ACCEPTED_CODES:
            return 1

        # extract the relevant information out of the traffic log
        if message_id == 302014:
            decoded = self.decode_tcp(message)
        elif message_id == 302016:
            decoded = self.decode_udp(message)
        elif message_id == 302018:
            decoded = self.decode_gre(message)
        elif message_id == 302021:
            decoded = self.decode_icmp(message)
        else:
            return 2

        if decoded is None:
            return 3

        try:
            # decoded has keys: src, srcport, dst, dstport, duration, bytes_received, protocol
            dictionary['src'] = self.ip_to_int(*(decoded['src'].split(".")))
            dictionary['srcport'] = int(decoded['srcport'])
            dictionary['dst'] = self.ip_to_int(*(decoded['dst'].split(".")))
            dictionary['dstport'] = int(decoded['dstport'])
            dictionary['protocol'] = decoded['protocol']
            dictionary['duration'] = int(decoded['duration'])
            dictionary['bytes_received'] = int(decoded['bytes_received'])
            # missing keys: bytes_sent, packets_sent/received, timestamp
            dictionary['bytes_sent'] = 0
            dictionary['packets_received'] = 1
            dictionary['packets_sent'] = 0
            dictionary['timestamp'] = datetime.datetime.fromtimestamp(time.time())
        except:
            traceback.print_exc()
            return 4
        return 0


class_ = ASASyslogImporter

# If running as a script, begin by executing main.
if __name__ == "__main__":
    sys.stderr.write("Warning: This importer is incomplete and uses empty data for some fields.")
    importer = class_()
    importer.main(sys.argv)
