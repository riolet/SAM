INSERT INTO syslog (SourceIP, SourcePort, DestinationIP, DestinationPort) VALUES (167813348, 61003, 203598750, 443);
INSERT INTO syslog (SourceIP, SourcePort, DestinationIP, DestinationPort) VALUES (167900212, 56473, 203578134, 443);
INSERT INTO syslog (SourceIP, SourcePort, DestinationIP, DestinationPort) VALUES (2887123978, 51905, 176760776, 3268);
INSERT INTO syslog (SourceIP, SourcePort, DestinationIP, DestinationPort) VALUES (167886306, 59994, 203598750, 443);
INSERT INTO syslog (SourceIP, SourcePort, DestinationIP, DestinationPort) VALUES (2887123978, 51894, 176794212, 3268);
INSERT INTO syslog (SourceIP, SourcePort, DestinationIP, DestinationPort) VALUES (203610520, 46732, 203598668, 389);

--  python helper for making test data from lines like "10.0.160.228, 61003, 12.34.171.158, 443"



def convert(a, b, c, d):
  return (int(a)<<24) + (int(b)<<16) + (int(c)<<8) + int(d)

def encode(line):
  a = line.split(", ")
  srcip = convert(*(a[0].split(".")))
  srcport = int(a[1])
  dstip = convert(*(a[2].split(".")))
  dstport = int(a[3])
  return "INSERT INTO syslog (SourceIP, SourcePort, DestinationIP, DestinationPort) VALUES ({0}, {1}, {2}, {3});".format(srcip, srcport, dstip, dstport)

