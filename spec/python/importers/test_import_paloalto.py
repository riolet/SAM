from sam.importers import import_base, import_paloalto

sample_log = [
    "",
    """{"message":"1,2011/06/21 18:06:18,0009C100218,TRAFFIC,end,1,2011/06/21 18:06:27,8.131.66.13,7.66.10.231,0.0.0.0,0.0.0.0,Allow export to Syslog,,,incomplete,vsys1,TAP-T0000R021,TAP-T0000R021,ethernet1/3,ethernet1/3,Copy Traffic Logs to Syslog,2011/06/21 18:06:27,309703,1,61590,443,0,0,0x19,tcp,allow,66,66,0,1,2011/06/21 18:06:19,5,any,0,945780,0x0,8.0.0.0-8.255.255.255,US,0,1,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy","@version":"1","@timestamp":"2011-06-22T01:06:27.000Z","host":"9.8.7.6","priority":14,"timestamp":"Jun 21 18:06:27","logsource":"Palo-Alto-Networks","severity":6,"facility":1,"facility_label":"user-level","severity_label":"Informational"}""",
    """{"message":"1,2011/06/21 18:06:19,0009C100218,TRAFFIC,end,1,2011/06/21 18:06:27,7.66.133.39,6.146.175.209,0.0.0.0,0.0.0.0,Allow export to Syslog,,,netbios-ns,vsys1,TAP-T0000R021,TAP-T0000R021,ethernet1/3,ethernet1/3,Copy Traffic Logs to Syslog,2011/06/21 18:06:27,158099,1,137,137,0,0,0x19,udp,allow,184,184,0,3,2011/06/21 18:05:51,33,any,0,945779,0x0,US,6.16.0.0-6.119.255.255,0,3,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy","@version":"1","@timestamp":"2011-06-22T01:06:27.000Z","host":"9.8.7.6","priority":14,"timestamp":"Jun 21 18:06:27","logsource":"Palo-Alto-Networks","severity":6,"facility":1,"facility_label":"user-level","severity_label":"Informational"}""",
    """{"message":"1,2011/06/21 18:06:20,0009C100218,TRAFFIC,end,1,2011/06/21 18:06:20,6.229.180.169,7.66.81.57,0.0.0.0,0.0.0.0,Allow export to Syslog,,,netbios-ns,vsys1,TAP-T0000R021,TAP-T0000R021,ethernet1/3,ethernet1/3,Copy Traffic Logs to Syslog,2011/06/21 18:06:20,80266,1,137,137,0,0,0x19,udp,allow,253,253,0,1,2011/06/21 18:05:54,30,any,0,945781,0x0,6.16.0.0-6.119.255.255,US,0,1,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy","@version":"1","@timestamp":"2011-06-22T01:06:20.000Z","host":"9.8.7.6","priority":14,"timestamp":"Jun 21 18:06:20","logsource":"Palo-Alto-Networks","severity":6,"facility":1,"facility_label":"user-level","severity_label":"Informational"}""",
    """{"message":"1,2011/06/21 18:06:21,0009C100218,TRAFFIC,end,1,2011/06/21 18:06:21,8.146.31.133,7.66.192.80,0.0.0.0,0.0.0.0,Allow export to Syslog,,,incomplete,vsys1,TAP-T0000R021,TAP-T0000R021,ethernet1/3,ethernet1/3,Copy Traffic Logs to Syslog,2011/06/21 18:06:21,265978,1,64533,443,0,0,0x19,tcp,allow,20009,20009,0,30,2011/06/21 17:06:24,3600,any,0,945782,0x0,8.0.0.0-8.255.255.255,US,0,30,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy","@version":"1","@timestamp":"2011-06-22T01:06:7.000Z","host":"9.8.7.6","priority":14,"timestamp":"Jun 21 18:06:21","logsource":"Palo-Alto-Networks","severity":6,"facility":1,"facility_label":"user-level","severity_label":"Informational"}""",
    """{"message":"1,2011/06/21 18:06:22,0009C100218,TRAFFIC,end,1,2011/06/21 18:06:22,7.66.40.63,6.35.146.97,0.0.0.0,0.0.0.0,Allow export to Syslog,,,incomplete,vsys1,TAP-T0000R021,TAP-T0000R021,ethernet1/3,ethernet1/3,Copy Traffic Logs to Syslog,2011/06/21 18:06:22,360655,1,34133,9003,0,0,0x19,tcp,allow,1892,1892,0,11,2011/06/21 17:06:24,3600,any,0,945783,0x0,US,6.16.0.0-6.119.255.255,0,11,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy","@version":"1","@timestamp":"2011-06-22T01:06:22.000Z","host":"9.8.7.6","priority":14,"timestamp":"Jun 21 18:06:22","logsource":"Palo-Alto-Networks","severity":6,"facility":1,"facility_label":"user-level","severity_label":"Informational"}""",
    """{"message":"1,2011/06/21 18:06:23,0009C100218,CONFIG,end,1,2011/06/21 18:06:23,7.66.40.32,6.229.19.249,0.0.0.0,0.0.0.0,Allow export to Syslog,,,ping,vsys1,TAP-T0000R022,TAP-T0000R022,ethernet1/4,ethernet1/4,Copy Traffic Logs to Syslog,2011/06/21 18:06:23,245351,1,0,0,0,0,0x100019,icmp,allow,74,74,0,1,2011/06/21 18:06:15,0,any,0,945784,0x0,US,6.16.0.0-6.119.255.255,0,1,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy","@version":"1","@timestamp":"2011-06-22T01:06:23.000Z","host":"9.8.7.6","priority":14,"timestamp":"Jun 21 18:06:23","logsource":"Palo-Alto-Networks","severity":6,"facility":1,"facility_label":"user-level","severity_label":"Informational"}""",
    """{"message":"1,2011/06/21 18:06:24,0009C100218,TRAFFIC,end,1,2011/06/21 18:06:24,7.66.182.193,6.35.64.27,0.0.0.0,0.0.0.0,Allow export to Syslog,,,icmp,vsys1,TAP-T0000R022,TAP-T0000R022,ethernet1/4,ethernet1/4,Copy Traffic Logs to Syslog,2011/06/21 18:06:24,95633,1,0,0,0,0,0x100019,icmp,allow,360,360,0,3,2011/06/21 18:06:12,3,any,0,945785,0x0,US,6.16.0.0-6.119.255.255,0,3,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy","@version":"1","@timestamp":"2011-06-22T01:06:24.000Z","host":"9.8.7.6","priority":14,"timestamp":"Jun 21 18:06:24","logsource":"Palo-Alto-Networks","severity":6,"facility":1,"facility_label":"user-level","severity_label":"Informational"}""",
    """{"message":"1,2011/06/21 18:06:25,0009C100218,TRAFFIC,end,1,2011/06/21 18:06:25,7.66.94.6,6.35.64.113,0.0.0.0,0.0.0.0,Allow export to Syslog,,,snmp-base,vsys1,TAP-T0000R022,TAP-T0000R022,ethernet1/4,ethernet1/4,Copy Traffic Logs to Syslog,2011/06/21 18:06:25,34190678,1,161,59491,0,0,0x100050,udp,allow,183,183,0,1,2011/06/21 18:05:54,30,any,0,945786,0x0,US,6.16.0.0-6.119.255.255,0,1,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy","@version":"1","@timestamp":"2011-06-22T01:06:25.000Z","host":"9.8.7.6","priority":14,"timestamp":"Jun 21 18:06:25","logsource":"Palo-Alto-Networks","severity":6,"facility":1,"facility_label":"user-level","severity_label":"Informational"}""",
    """{"message":"1,2011/06/21 18:06:26,0009C100218,TRAFFIC,end,1,2011/06/21 18:06:27,7.66.218.234,7.66.10.55,0.0.0.0,0.0.0.0,Allow export to Syslog,,,incomplete,vsys1,TAP-T0000R022,TAP-T0000R022,ethernet1/4,ethernet1/4,Copy Traffic Logs to Syslog,2011/06/21 18:06:27,33918797,1,39655,26307,0,0,0x19,tcp,allow,2879,2879,0,9,2011/06/21 17:06:24,3600,any,0,945787,0x0,US,US,0,9,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy","@version":"1","@timestamp":"2011-06-22T01:06:27.000Z","host":"9.8.7.6","priority":14,"timestamp":"Jun 21 18:06:27","logsource":"Palo-Alto-Networks","severity":6,"facility":1,"facility_label":"user-level","severity_label":"Informational"}""",
    """{"message":"1,2011/06/21 18:06:27,0009C100218,TRAFFIC,end,1,2011/06/21 18:06:27,7.66.36.6,6.146.197.148,0.0.0.0,0.0.0.0,Allow export to Syslog,,netbios-ns,vsys1,TAP-T0000R022,TAP-T0000R022,ethernet1/4,ethernet1/4,Copy Traffic Logs to Syslog,2011/06/21 18:06:27,34555638,1,137,137,0,0,0x19,udp,allow,184,184,0,3,2011/06/21 18:05:51,33,any,0,945788,0x0,US,6.16.0.0-6.119.255.255,0,3,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy","@version":"1","@timestamp":"2011-06-22T01:06:27.000Z","host":"9.8.7.6","priority":14,"timestamp":"Jun 21 18:06:27","logsource":"Palo-Alto-Networks","severity":6,"facility":1,"facility_label":"user-level","severity_label":"Informational"}""",
    "",
    "nonsensical entry",
    "",
]


def test_class():
    assert import_paloalto.class_ == import_paloalto.PaloAltoImporter


def test_translate():
    pa = import_paloalto.PaloAltoImporter()

    translated_lines = []
    for i, line in enumerate(sample_log):
        d = {}
        r = pa.translate(line, i+1, d)
        if r == 0:
            assert set(d.keys()) == set(import_base.BaseImporter.keys)
            translated_lines.append(d)

    assert len(translated_lines) == 8
    assert translated_lines[3] == {
        "src": 143794053,
        "srcport": '64533',
        "dst": 121815120,
        "dstport": '443',
        "timestamp": '2011-06-21 18:06:21',
        "protocol": 'TCP',
        "bytes_sent": '20009',
        "bytes_received": '0',
        "packets_sent": '30',
        "packets_received": '0',
        "duration": '3600',
    }
    assert translated_lines[6] == {
        "src": 121789958,
        "srcport": '161',
        "dst": 102973553,
        "dstport": '59491',
        "timestamp": '2011-06-21 18:06:25',
        "protocol": 'UDP',
        "bytes_sent": '183',
        "bytes_received": '0',
        "packets_sent": '1',
        "packets_received": '0',
        "duration": '30',
    }

