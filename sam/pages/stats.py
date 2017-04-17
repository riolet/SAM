import json
from sam import constants
import web
from sam import common
import re
import sam.models.settings
import sam.models.links
import sam.models.datasources
import sam.models.nodes
import base
from sam import errors
import decimal


def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError


class Stats(base.Headed):
    pageTitle = "Stats"

    def __init__(self):
        super(Stats, self).__init__('Stats', True, True)
        # common.demo(on=False)
        #TODO: restructure this file.
        self.styles = ['/static/css/general.css']
        self.sub = None
        self.table_links = ''
        self.settingsModel = None

    def ds_stats(self, ds_id):
        table_links = self.table_links.format(id=ds_id)
        stats = []

        # get unique host information
        dstIPs = set([row.ip for row in common.db.query("SELECT dst AS 'ip' FROM {table_links} GROUP BY ip"
                                                        .format(table_links=table_links))])
        stats.append(("Unique destination IP addresses:", str(len(dstIPs))))

        srcIPs = set([row.ip for row in common.db.query("SELECT src AS 'ip' FROM {table_links} GROUP BY ip"
                                                        .format(table_links=table_links))])
        stats.append(("Unique source IP addresses:", str(len(srcIPs))))

        stats.append(("Unique IP addresses:", str(len(dstIPs | srcIPs))))

        # get unique destination ports and spread
        rows = common.db.query("SELECT DISTINCT port AS 'Port' FROM {table_links};"
                               .format(table_links=table_links))
        lrows = rows.list()
        stats.append(("Unique destination ports used:", str(len(lrows))))
        sys_lrows = [i for i in lrows if i['Port'] < 1024]
        stats.append(("Unique system ports used (0..1023):", str(len(sys_lrows))))
        usr_lrows = [i for i in lrows if 1024 <= i['Port'] < 49152]
        stats.append(("Unique user ports used (1024..49151):", str(len(usr_lrows))))
        prv_lrows = [i for i in lrows if 49152 <= i['Port'] < 65536]
        stats.append(("Unique private ports used (49152..65535):", str(len(prv_lrows))))

        rows = common.db.query(
            "SELECT dst AS 'Address', COUNT(DISTINCT port) AS 'Ports', COUNT(links) AS 'Connections' "
            "FROM {table_links} GROUP BY Address ORDER BY Ports DESC, Connections DESC LIMIT 100;"
                .format(table_links=table_links))
        lrows = list(rows)
        if len(lrows) > 0:
            stats.append(("Max ports for one destination: ", str(lrows[0]['Ports'])))
            count = 0
            while count < len(lrows) and lrows[count]['Ports'] > 10:
                count += 1
            if count != len(lrows):
                stats.append(("Percent of destinations with fewer than 10 ports: ", "{0:0.3f}%"
                                   .format((len(dstIPs) - count) * 100 / float(len(dstIPs)))))

        rows = common.db.query("SELECT 1 FROM {table_links} GROUP BY src, dst, port;".format(table_links=table_links))
        lrows = list(rows)
        stats.append(("Total Number of distinct connections (node -> node:port) stored:", str(len(lrows))))
        rows = common.db.query("SELECT SUM(links) AS 'links' FROM {table_links} "
                               "GROUP BY src, dst, port HAVING links > 100;".format(table_links=table_links))
        lrows = list(rows)
        stats.append(("Number of distinct connections occurring more than 100 times:", str(len(lrows))))

        return stats

    def overall_stats(self):
        # ds_model = sam.models.datasources.Datasources(self.session, self.sub)
        node_model = sam.models.nodes.Nodes(common.db, self.sub)
        stats = []
        stats.append(('Total hosts recorded', len(node_model.get_all_endpoints())))

        return stats

    def decode_ds(self, data):
        ds_match = re.search("(\d+)", data.get('ds', ''))
        default_ds = self.settingsModel['datasource']

        if ds_match:
            try:
                ds = int(ds_match.group())
            except ValueError:
                ds = default_ds
        else:
            ds = default_ds

        return ds

    def decode_get_request(self, data):
        query = data.get('q')
        if not query:
            raise errors.RequiredKey('query', 'q')

        ds = self.decode_ds(data)

        return {'query': query, 'ds': ds}

    def perform_get_command(self, request):
        self.require_group('read')
        if request['query'] == 'timerange':
            linksModel = sam.models.links.Links(common.db, self.sub, request['ds'])
            return linksModel.get_timerange()
        elif request['query'] == 'protocols':
            linksModel = sam.models.links.Links(common.db, self.sub, request['ds'])
            return linksModel.get_protocol_list()
        else:
            raise errors.MalformedRequest("Query not recognized.")

    def encode_get_response(self, response):
        return response

    def headless_get(self):
        self.sub = self.user.viewing
        if self.sub is None:
            self.sub = constants.demo['id']
        self.settingsModel = sam.models.settings.Settings(common.db, self.session, self.sub)

        try:
            self.request = self.decode_get_request(self.inbound)
            self.response = self.perform_get_command(self.request)
            self.outbound = self.encode_get_response(self.response)
        except errors.MalformedRequest as e:
            self.outbound = {'result': 'failure', 'message': e.message}
        web.header("Content-Type", "application/json")
        return json.dumps(self.outbound, default=decimal_default)

    def headed_get(self):
        self.require_group('read')
        self.sub = self.user.viewing
        self.settingsModel = sam.models.settings.Settings(common.db, self.session, self.sub)
        self.table_links = "s{acct}_ds{{id}}_Links".format(acct=self.sub)

        segments = []
        segments.append(('Overall', self.overall_stats()))
        ds_model = sam.models.datasources.Datasources(common.db, self.session, self.sub)
        for ds_id in ds_model.ds_ids:
            section_name = 'Datasource: {0}'.format(ds_model.datasources[ds_id]['name'])
            segments.append((section_name, self.ds_stats(ds_id)))

        return self.render('stats', segments)

    def GET(self):
        if "q" in self.inbound:
            return self.headless_get()
        else:
            return self.headed_get()
