import sam.common as common
import sam.models.links
import sam.models.nodes
import sam.models.upload
import sam.importers.import_base
from spec.python import db_connection

db = db_connection.db
sub_id = db_connection.default_sub
ds_empty = db_connection.dsid_short

importer_names = ['paloalto', 'nfdump', 'aws', 'asa', 'tcpdump']

try:
    import dateutil.parser
    importer_names.append('tshark')
except:
    pass

short_log = """
{"message":"1,2011/06/21 18:06:18,0009C100218,TRAFFIC,end,1,2011/06/21 18:06:27,8.131.66.13,7.66.10.231,0.0.0.0,0.0.0.0,Allow export to Syslog,,,incomplete,vsys1,TAP-T0000R021,TAP-T0000R021,ethernet1/3,ethernet1/3,Copy Traffic Logs to Syslog,2011/06/21 18:06:27,309703,1,61590,443,0,0,0x19,tcp,allow,66,66,0,1,2011/06/21 18:06:19,5,any,0,945780,0x0,8.0.0.0-8.255.255.255,US,0,1,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy","@version":"1","@timestamp":"2011-06-22T01:06:27.000Z","host":"9.8.7.6","priority":14,"timestamp":"Jun 21 18:06:27","logsource":"Palo-Alto-Networks","severity":6,"facility":1,"facility_label":"user-level","severity_label":"Informational"}
{"message":"1,2011/06/21 18:06:19,0009C100218,TRAFFIC,end,1,2011/06/21 18:06:27,7.66.133.39,6.146.175.209,0.0.0.0,0.0.0.0,Allow export to Syslog,,,netbios-ns,vsys1,TAP-T0000R021,TAP-T0000R021,ethernet1/3,ethernet1/3,Copy Traffic Logs to Syslog,2011/06/21 18:06:27,158099,1,137,137,0,0,0x19,udp,allow,184,184,0,3,2011/06/21 18:05:51,33,any,0,945779,0x0,US,6.16.0.0-6.119.255.255,0,3,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy","@version":"1","@timestamp":"2011-06-22T01:06:27.000Z","host":"9.8.7.6","priority":14,"timestamp":"Jun 21 18:06:27","logsource":"Palo-Alto-Networks","severity":6,"facility":1,"facility_label":"user-level","severity_label":"Informational"}
{"message":"1,2011/06/21 18:06:20,0009C100218,TRAFFIC,end,1,2011/06/21 18:06:20,6.229.180.169,7.66.81.57,0.0.0.0,0.0.0.0,Allow export to Syslog,,,netbios-ns,vsys1,TAP-T0000R021,TAP-T0000R021,ethernet1/3,ethernet1/3,Copy Traffic Logs to Syslog,2011/06/21 18:06:20,80266,1,137,137,0,0,0x19,udp,allow,253,253,0,1,2011/06/21 18:05:54,30,any,0,945781,0x0,6.16.0.0-6.119.255.255,US,0,1,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy","@version":"1","@timestamp":"2011-06-22T01:06:20.000Z","host":"9.8.7.6","priority":14,"timestamp":"Jun 21 18:06:20","logsource":"Palo-Alto-Networks","severity":6,"facility":1,"facility_label":"user-level","severity_label":"Informational"}
{"message":"1,2011/06/21 18:06:21,0009C100218,TRAFFIC,end,1,2011/06/21 18:06:21,8.146.31.133,7.66.192.80,0.0.0.0,0.0.0.0,Allow export to Syslog,,,incomplete,vsys1,TAP-T0000R021,TAP-T0000R021,ethernet1/3,ethernet1/3,Copy Traffic Logs to Syslog,2011/06/21 18:06:21,265978,1,64533,443,0,0,0x19,tcp,allow,20009,20009,0,30,2011/06/21 17:06:24,3600,any,0,945782,0x0,8.0.0.0-8.255.255.255,US,0,30,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy","@version":"1","@timestamp":"2011-06-22T01:06:7.000Z","host":"9.8.7.6","priority":14,"timestamp":"Jun 21 18:06:21","logsource":"Palo-Alto-Networks","severity":6,"facility":1,"facility_label":"user-level","severity_label":"Informational"}
{"message":"1,2011/06/21 18:06:22,0009C100218,TRAFFIC,end,1,2011/06/21 18:06:22,7.66.40.63,6.35.146.97,0.0.0.0,0.0.0.0,Allow export to Syslog,,,incomplete,vsys1,TAP-T0000R021,TAP-T0000R021,ethernet1/3,ethernet1/3,Copy Traffic Logs to Syslog,2011/06/21 18:06:22,360655,1,34133,9003,0,0,0x19,tcp,allow,1892,1892,0,11,2011/06/21 17:06:24,3600,any,0,945783,0x0,US,6.16.0.0-6.119.255.255,0,11,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy","@version":"1","@timestamp":"2011-06-22T01:06:22.000Z","host":"9.8.7.6","priority":14,"timestamp":"Jun 21 18:06:22","logsource":"Palo-Alto-Networks","severity":6,"facility":1,"facility_label":"user-level","severity_label":"Informational"}
{"message":"1,2011/06/21 18:06:23,0009C100218,TRAFFIC,end,1,2011/06/21 18:06:23,7.66.40.32,6.229.19.249,0.0.0.0,0.0.0.0,Allow export to Syslog,,,ping,vsys1,TAP-T0000R022,TAP-T0000R022,ethernet1/4,ethernet1/4,Copy Traffic Logs to Syslog,2011/06/21 18:06:23,245351,1,0,0,0,0,0x100019,icmp,allow,74,74,0,1,2011/06/21 18:06:15,0,any,0,945784,0x0,US,6.16.0.0-6.119.255.255,0,1,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy","@version":"1","@timestamp":"2011-06-22T01:06:23.000Z","host":"9.8.7.6","priority":14,"timestamp":"Jun 21 18:06:23","logsource":"Palo-Alto-Networks","severity":6,"facility":1,"facility_label":"user-level","severity_label":"Informational"}
{"message":"1,2011/06/21 18:06:24,0009C100218,TRAFFIC,end,1,2011/06/21 18:06:24,7.66.182.193,6.35.64.27,0.0.0.0,0.0.0.0,Allow export to Syslog,,,icmp,vsys1,TAP-T0000R022,TAP-T0000R022,ethernet1/4,ethernet1/4,Copy Traffic Logs to Syslog,2011/06/21 18:06:24,95633,1,0,0,0,0,0x100019,icmp,allow,360,360,0,3,2011/06/21 18:06:12,3,any,0,945785,0x0,US,6.16.0.0-6.119.255.255,0,3,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy","@version":"1","@timestamp":"2011-06-22T01:06:24.000Z","host":"9.8.7.6","priority":14,"timestamp":"Jun 21 18:06:24","logsource":"Palo-Alto-Networks","severity":6,"facility":1,"facility_label":"user-level","severity_label":"Informational"}
{"message":"1,2011/06/21 18:06:25,0009C100218,TRAFFIC,end,1,2011/06/21 18:06:25,7.66.94.6,6.35.64.113,0.0.0.0,0.0.0.0,Allow export to Syslog,,,snmp-base,vsys1,TAP-T0000R022,TAP-T0000R022,ethernet1/4,ethernet1/4,Copy Traffic Logs to Syslog,2011/06/21 18:06:25,34190678,1,161,59491,0,0,0x100050,udp,allow,183,183,0,1,2011/06/21 18:05:54,30,any,0,945786,0x0,US,6.16.0.0-6.119.255.255,0,1,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy","@version":"1","@timestamp":"2011-06-22T01:06:25.000Z","host":"9.8.7.6","priority":14,"timestamp":"Jun 21 18:06:25","logsource":"Palo-Alto-Networks","severity":6,"facility":1,"facility_label":"user-level","severity_label":"Informational"}
{"message":"1,2011/06/21 18:06:26,0009C100218,TRAFFIC,end,1,2011/06/21 18:06:27,7.66.218.234,7.66.10.55,0.0.0.0,0.0.0.0,Allow export to Syslog,,,incomplete,vsys1,TAP-T0000R022,TAP-T0000R022,ethernet1/4,ethernet1/4,Copy Traffic Logs to Syslog,2011/06/21 18:06:27,33918797,1,39655,26307,0,0,0x19,tcp,allow,2879,2879,0,9,2011/06/21 17:06:24,3600,any,0,945787,0x0,US,US,0,9,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy","@version":"1","@timestamp":"2011-06-22T01:06:27.000Z","host":"9.8.7.6","priority":14,"timestamp":"Jun 21 18:06:27","logsource":"Palo-Alto-Networks","severity":6,"facility":1,"facility_label":"user-level","severity_label":"Informational"}
{"message":"1,2011/06/21 18:06:27,0009C100218,TRAFFIC,end,1,2011/06/21 18:06:27,7.66.36.6,6.146.197.148,0.0.0.0,0.0.0.0,Allow export to Syslog,,,netbios-ns,vsys1,TAP-T0000R022,TAP-T0000R022,ethernet1/4,ethernet1/4,Copy Traffic Logs to Syslog,2011/06/21 18:06:27,34555638,1,137,137,0,0,0x19,udp,allow,184,184,0,3,2011/06/21 18:05:51,33,any,0,945788,0x0,US,6.16.0.0-6.119.255.255,0,3,0,aged-out,0,0,0,0,,Palo-Alto-Networks,from-policy","@version":"1","@timestamp":"2011-06-22T01:06:27.000Z","host":"9.8.7.6","priority":14,"timestamp":"Jun 21 18:06:27","logsource":"Palo-Alto-Networks","severity":6,"facility":1,"facility_label":"user-level","severity_label":"Informational"}
"""


def test_get_importer():
    m_upload = sam.models.upload.Uploader(db, sub_id, ds_empty, 'paloalto')
    assert isinstance(m_upload.importer, sam.importers.import_base.BaseImporter)

    m_upload = sam.models.upload.Uploader(db, sub_id, ds_empty, 'import_paloalto')
    assert isinstance(m_upload.importer, sam.importers.import_base.BaseImporter)

    m_upload = sam.models.upload.Uploader(db, sub_id, ds_empty, 'PaloAlto')
    assert isinstance(m_upload.importer, sam.importers.import_base.BaseImporter)

    for i in importer_names:
        m_upload = sam.models.upload.Uploader(db, sub_id, ds_empty, i)
        assert isinstance(m_upload.importer, sam.importers.import_base.BaseImporter)

    m_upload = sam.models.upload.Uploader(db, sub_id, ds_empty, '')
    assert m_upload.importer is None


def test_run_import():
    table_name = "s{s}_ds{ds}_Syslog".format(s=sub_id, ds=ds_empty)
    db.query("DELETE FROM {table}".format(table=table_name))
    try:
        m_upload = sam.models.upload.Uploader(db, sub_id, ds_empty, '')
        inserted = m_upload.run_import(short_log)
        assert inserted == 0

        m_upload = sam.models.upload.Uploader(db, sub_id, ds_empty, 'paloalto')
        inserted = m_upload.run_import(short_log)
        assert inserted == 10
        rows = list(db.query("SELECT * FROM {table}".format(table=table_name)))
        t = common.IPtoString
        paths = [(t(x['src']), t(x['dst']), x['dstport']) for x in rows]
        paths.sort(key=lambda row: row[0] + row[1] + str(row[2]))
        expected = [('6.229.180.169', '7.66.81.57', 137),
                    ('7.66.133.39', '6.146.175.209', 137),
                    ('7.66.182.193', '6.35.64.27', 0),
                    ('7.66.218.234', '7.66.10.55', 26307),
                    ('7.66.36.6', '6.146.197.148', 137),
                    ('7.66.40.32', '6.229.19.249', 0),
                    ('7.66.40.63', '6.35.146.97', 9003),
                    ('7.66.94.6', '6.35.64.113', 59491),
                    ('8.131.66.13', '7.66.10.231', 443),
                    ('8.146.31.133', '7.66.192.80', 443)]
        assert paths == expected
    finally:
        db.query("DELETE FROM {table}".format(table=table_name))


def test_import_log():
    syslog_table_name = "s{s}_ds{ds}_Syslog".format(s=sub_id, ds=ds_empty)
    links_table_name = "s{s}_ds{ds}_Links".format(s=sub_id, ds=ds_empty)
    try:
        m_upload = sam.models.upload.Uploader(db, sub_id, ds_empty, 'paloalto')
        m_upload.import_log(short_log)
        rows = list(db.query("SELECT src, dst, port FROM {table} WHERE src < 167772160 "
                             "ORDER BY src ASC, dst ASC, port ASC"
                             .format(table=links_table_name)))
        rows = list(rows)
        t = common.IPtoString
        paths = [(t(x['src']), t(x['dst']), x['port']) for x in rows]
        paths.sort(key=lambda row: row[0] + row[1] + str(row[2]))
        expected = [('6.229.180.169', '7.66.81.57', 137),
                    ('7.66.133.39', '6.146.175.209', 137),
                    ('7.66.182.193', '6.35.64.27', 0),
                    ('7.66.218.234', '7.66.10.55', 26307),
                    ('7.66.36.6', '6.146.197.148', 137),
                    ('7.66.40.32', '6.229.19.249', 0),
                    ('7.66.40.63', '6.35.146.97', 9003),
                    ('7.66.94.6', '6.35.64.113', 59491),
                    ('8.131.66.13', '7.66.10.231', 443),
                    ('8.146.31.133', '7.66.192.80', 443)]
        assert paths == expected
    finally:
        db.query("DELETE FROM {table}".format(table=syslog_table_name))

        m_links = sam.models.links.Links(db, sub_id, ds_empty)
        m_links.delete_connections()

        m_nodes = sam.models.nodes.Nodes(db, sub_id)
        m_nodes.delete_collection(['6', '7', '8', '9'])


