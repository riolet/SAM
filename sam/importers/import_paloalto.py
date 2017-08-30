import json
import sys
from sam.importers.import_base import BaseImporter
from datetime import datetime


class PaloAltoImporter(BaseImporter):
    # Message pieces are as follows.
    # header_title = "FUTURE_USE, Receive Time, Serial Number, Type, Subtype, FUTURE_USE, Generated Time, Source IP, Destination IP, NAT Source IP, NAT Destination IP, Rule Name, Source User, Destination User, Application, Virtual System, Source Zone, Destination Zone, Ingress Interface, Egress Interface, Log Forwarding Profile, FUTURE_USE, Session ID, Repeat Count, Source Port, Destination Port, NAT Source Port, NAT Destination Port, Flags, Protocol, Action, Bytes, Bytes Sent, Bytes Received, Packets, Start Time, Elapsed Time, Category, FUTURE_USE, Sequence Number, Action Flags, Source Location, Destination Location, FUTURE_USE, Packets Sent, Packets Received, Session End Reason"
    # header_string = "FUTURE_USE, receive_time, serial, type, subtype, FUTURE_USE, time_generated, src, dst, natsrc, natdst, rule, srcuser, dstuser, app, vsys, from, to, inbound_if, outbound_if, logset, FUTURE_USE, sessionid, repeatcnt, sport, dport, natsport, natdport, flags, proto, action, bytes, bytes_sent, bytes_received, packets, start, elapsed, category, FUTURE_USE, seqno, actionflags, srcloc, dstloc, FUTURE_USE, pkts_sent, pkts_received, session_end_reason"
    # indexes derived from above:
    Timestamp = 1
    Type = 3
    SourceIP = 7
    DestIP = 8
    SourcePort = 24
    DestPort = 25
    Protocol = 29
    BytesTotal = 31
    BytesSent = 32  # *
    BytesReceived = 33  # *
    TotalPackets = 34
    TimeElapsed = 36
    PacketsSent = 44  # *
    PacketsReceived = 45  # *
    #
    # *bytes/packets sent/received not always supported.
    #     In that case store total in received and None in sent

    def translate(self, line, line_num, dictionary):
        """
        Converts a given syslog line into a dictionary of (ip, port, ip, port, timestamp)
        Args:
            line: The syslog line to parse
            line_num: The line number, for error printouts
            dictionary: The dictionary to write key/values pairs into

        Returns:
            0 on success and non-zero on error.
            1 => ignoring a message that isn't network "TRAFFIC"
            2 => error in parsing the line.
            4 => Could not JSON decode the line.
        """
        try:
            data = json.loads(line)['message']
        except:
            return 4
        # TODO: this assumes the data will not have any commas embedded in strings.
        #       Faster than csv parsing. Has been safe so far!
        split_data = data.split(',')

        if split_data[PaloAltoImporter.Type] != "TRAFFIC":
            print("Line {0}: Ignoring non-TRAFFIC entry (was {1})".format(line_num, split_data[3]))
            return 1

        try:
            # srcIP, srcPort, dstIP, dstPort
            dictionary['src'] = self.ip_to_int(*(split_data[PaloAltoImporter.SourceIP].split(".")))
            dictionary['srcport'] = split_data[PaloAltoImporter.SourcePort]
            dictionary['dst'] = self.ip_to_int(*(split_data[PaloAltoImporter.DestIP].split(".")))
            dictionary['dstport'] = split_data[PaloAltoImporter.DestPort]
            dictionary['timestamp'] = datetime.strptime(
                split_data[PaloAltoImporter.Timestamp], "%Y/%m/%d %H:%M:%S").strftime(self.mysql_time_format)
            dictionary['protocol'] = split_data[PaloAltoImporter.Protocol].upper()
            if split_data[PaloAltoImporter.BytesSent] and split_data[PaloAltoImporter.BytesReceived] and int(
                    split_data[PaloAltoImporter.BytesSent]) + int(split_data[PaloAltoImporter.BytesReceived]) == int(
                    split_data[PaloAltoImporter.BytesTotal]):
                dictionary['bytes_sent'] = split_data[PaloAltoImporter.BytesSent]
                dictionary['bytes_received'] = split_data[PaloAltoImporter.BytesReceived]
            else:
                dictionary['bytes_sent'] = None
                dictionary['bytes_received'] = split_data[PaloAltoImporter.BytesTotal]

            if split_data[PaloAltoImporter.PacketsSent] and split_data[PaloAltoImporter.PacketsReceived] and int(
                    split_data[PaloAltoImporter.PacketsSent]) + int(split_data[PaloAltoImporter.PacketsReceived]) == int(
                    split_data[PaloAltoImporter.TotalPackets]):
                dictionary['packets_sent'] = split_data[PaloAltoImporter.PacketsSent]
                dictionary['packets_received'] = split_data[PaloAltoImporter.PacketsReceived]
            else:
                dictionary['packets_sent'] = None
                dictionary['packets_received'] = split_data[PaloAltoImporter.TotalPackets]
            dictionary['duration'] = max(split_data[PaloAltoImporter.TimeElapsed], 1)

        except:
            print("error parsing line {0}: {1}".format(line_num, line))
            return 2
        return 0


class_ = PaloAltoImporter

# If running as a script, begin by executing main.
if __name__ == "__main__":
    importer = class_()
    importer.main(sys.argv)
